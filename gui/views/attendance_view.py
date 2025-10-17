# gui/views/attendance_view.py
import tkinter as tk
from tkinter import messagebox
import threading
import time
import json
import os
from datetime import datetime
import cv2

from config.settings import settings
from core.detection import detect_faces
from core.preprocessing import to_gray, equalize, crop_face
from core.recognizer_dlib import DlibFaceRecognizer

MODEL_PATH = "models/dlib_recognizer.pkl"
LABEL_MAP_PATH = "models/label_map.json"


class AttendanceView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # --- UI ---
        top = tk.Frame(self); top.pack(pady=8)
        tk.Button(top, text="Start Session (Camera)", command=self.start_session, width=22).pack(side="left", padx=6)
        tk.Button(top, text="Stop Session", command=self.stop_session, width=16).pack(side="left", padx=6)

        opts = tk.Frame(self); opts.pack(pady=4)
        self.auto_start_var = tk.BooleanVar(value=True)   # auto-start when tab is selected
        self.auto_stop_var  = tk.BooleanVar(value=True)   # auto-stop right after first mark
        tk.Checkbutton(opts, text="Auto Start on tab", variable=self.auto_start_var).pack(side="left", padx=8)
        tk.Checkbutton(opts, text="Auto Stop after mark", variable=self.auto_stop_var).pack(side="left", padx=8)

        self.msg = tk.StringVar(value="Ready.")
        tk.Label(self, textvariable=self.msg, anchor="w").pack(fill="x", padx=10)

        # --- runtime state ---
        self._thread = None
        self._running = False
        self._last_mark = {}       # person_id -> last timestamp (fallback debounce)
        self._rec = None
        self._label_inv = None
        self._win_title = "FRAS Camera"

        # --- anti-duplicate guards ---
        self._marked_session = set()   # already logged in this session
        self._stable_id = None         # stabilizing candidate id across frames
        self._stable_count = 0
        self._STABLE_FRAMES = 5        # require N consecutive frames to accept

    # Called by App when the tab becomes visible
    def maybe_auto_start(self):
        if self.auto_start_var.get() and not self._running:
            self.start_session()

    def _load_model(self) -> bool:
        if not os.path.exists(MODEL_PATH) or os.path.getsize(MODEL_PATH) < 100:
            messagebox.showerror("Model", "Model not found or empty. Train it first (Training tab).")
            return False
        try:
            self._rec = DlibFaceRecognizer(); self._rec.load(MODEL_PATH)
        except Exception as e:
            messagebox.showerror("Model", f"Failed to load model: {e}\nRe-train from Training tab.")
            return False
        if not os.path.exists(LABEL_MAP_PATH):
            messagebox.showerror("Model", "Missing label_map.json. Train the model first.")
            return False
        label_map = json.load(open(LABEL_MAP_PATH, "r", encoding="utf-8"))  # person_id -> str(label)
        self._label_inv = {int(v): k for k, v in label_map.items()}
        return True

    def start_session(self):
        if self._running:
            self.msg.set("Session already running."); return

        # Camera probe
        cam_index = settings.CAMERA_INDEX
        test = cv2.VideoCapture(cam_index)
        if not test.isOpened():
            self.msg.set(f"Camera index {cam_index} failed. Try CAMERA_INDEX=1 in .env.")
            messagebox.showerror("Camera", f"Cannot open camera at index {cam_index}.")
            return
        test.release()

        # Load model
        if not self._load_model():
            return

        # Reset duplicate/stability guards for this session
        self._marked_session.clear()
        self._stable_id = None
        self._stable_count = 0

        self._running = True
        self.msg.set("Session started. Camera window opened. Press Q or click Stop to end.")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop_session(self):
        if not self._running:
            self.msg.set("No active session."); return
        self._running = False
        self.msg.set("Stopping session...")

    def _loop(self):
        cap = cv2.VideoCapture(settings.CAMERA_INDEX)
        if not cap.isOpened():
            self.msg.set(f"Camera index {settings.CAMERA_INDEX} failed to open.")
            self._running = False; return

        cv2.namedWindow(self._win_title, cv2.WINDOW_NORMAL)
        try:
            while self._running:
                ok, frame = cap.read()
                if not ok or frame is None:
                    self.msg.set("Camera read failed."); break

                gray = to_gray(frame)
                faces = detect_faces(gray)

                # Single-face enforcement
                if settings.SINGLE_FACE_MODE and len(faces) != 1:
                    cv2.putText(frame, "Require exactly ONE face in frame.", (20, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                    for (x,y,w,h) in faces:
                        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,0,255), 2)
                    cv2.imshow(self._win_title, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or cv2.getWindowProperty(self._win_title, cv2.WND_PROP_VISIBLE) < 1:
                        break
                    continue

                if len(faces) < 1:
                    cv2.putText(frame, "No face detected.", (20, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,200,255), 2)
                    cv2.imshow(self._win_title, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or cv2.getWindowProperty(self._win_title, cv2.WND_PROP_VISIBLE) < 1:
                        break
                    continue

                # Predict for all faces
                best = None
                preds = []
                for (x,y,w,h) in faces:
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (10,220,10), 2)
                    face = crop_face(equalize(gray), (x,y,w,h))
                    try:
                        lbl, conf = self._rec.predict(face)
                    except Exception as e:
                        continue
                    person_id = self._label_inv.get(lbl, "Unknown")
                    preds.append((person_id, conf))
                    if best is None or (conf or 0) > (best[1] or 0):
                        best = (person_id, conf)

                if not preds:
                    cv2.putText(frame, "Predict failed.", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                    cv2.imshow(self._win_title, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or cv2.getWindowProperty(self._win_title, cv2.WND_PROP_VISIBLE) < 1:
                        break
                    continue

                person_id, conf = best
                now = time.time()
                last = self._last_mark.get(person_id, 0)
                debounced = (now - last) < settings.DEBOUNCE_SECONDS
                # For dlib mapping, conf is 0..1 with 1 best (from our mapping)
                # Accept when underlying distance <= DLIB_THRESH, i.e., conf >= 1 - (DLIB_THRESH/0.6)
                confident = (conf >= (1.0 - (settings.DLIB_THRESH/0.6)))

                # --- stability filter across frames ---
                if confident and person_id != "Unknown":
                    if self._stable_id == person_id:
                        self._stable_count += 1
                    else:
                        self._stable_id = person_id
                        self._stable_count = 1
                else:
                    # break stability streak if id/confidence not good
                    self._stable_id = None
                    self._stable_count = 0

                # --- decide logging (per-session guard + stability + debounce) ---
                if (person_id != "Unknown"
                    and confident
                    and self._stable_id == person_id
                    and self._stable_count >= self._STABLE_FRAMES
                    and not debounced
                    and person_id not in self._marked_session):

                    # mark now
                    self._marked_session.add(person_id)
                    self._last_mark[person_id] = now
                    self._write_log(person_id)

                    status = f"Marked Present: {person_id} (conf={conf:.1f})"
                    color = (10,220,10)
                    self.msg.set(status)

                    # reset stability so we don't immediately try again
                    self._stable_id = None
                    self._stable_count = 0

                    if self.auto_stop_var.get():
                        break

                elif person_id in self._marked_session:
                    status = f"{person_id}: already logged this session"
                    color = (0,165,255)

                elif debounced:
                    status = f"{person_id}: debounced ({int(now - last)}s)"
                    color = (0,165,255)

                else:
                    # show progress toward stability for UX
                    status = (f"Uncertain (conf={conf:.1f})"
                              if person_id == "Unknown" or not confident
                              else f"Stabilizing {person_id} [{self._stable_count}/{self._STABLE_FRAMES}]")
                    color = (0,0,255) if person_id == "Unknown" or not confident else (0,165,255)

                # overlay + show
                cv2.putText(frame, status, (20,40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.imshow(self._win_title, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or cv2.getWindowProperty(self._win_title, cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cap.release()
            try:
                if cv2.getWindowProperty(self._win_title, cv2.WND_PROP_VISIBLE) >= 0:
                    cv2.destroyWindow(self._win_title)
            except Exception:
                # window might already be gone
                pass
            self._running = False
            self.msg.set("Session stopped.")

    def _write_log(self, person_id: str):
        """
        Writes a single 'Present' row to today's CSV.
        Includes a per-day uniqueness guard: if this person already appears
        in today's CSV, do not write a duplicate line.
        Also emits <<AttendanceLogged>> so Dashboard refreshes immediately.
        """
        os.makedirs("reports/exports", exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        path = f"reports/exports/{today}.csv"
        hdr = "person_id,timestamp,status\n"

        # ---- per-day uniqueness guard ----
        already = False
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    # fast check: any line starting with "person_id,"
                    prefix = f"{person_id},"
                    for line in f:
                        if line.startswith(prefix):
                            already = True
                            break
            except Exception:
                pass

        if not already:
            line = f"{person_id},{datetime.now().isoformat()},Present\n"
            if not os.path.exists(path):
                open(path, "w", encoding="utf-8").write(hdr + line)
            else:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(line)
            
            # Update the message to show successful logging
            self.msg.set(f"Successfully logged attendance for {person_id}")
        else:
            # Update the message to show duplicate was prevented
            self.msg.set(f"Attendance already logged for {person_id} today")

        # notify dashboard regardless (so counts update even if duplicate suppressed)
        try:
            # Generate event on the root window so it can be caught by the app
            self.winfo_toplevel().event_generate("<<AttendanceLogged>>", when="tail")
        except Exception:
            pass
