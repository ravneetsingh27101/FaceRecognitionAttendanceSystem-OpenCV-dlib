# gui/views/enroll_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import cv2, os, re
from config.settings import settings
from core.detection import detect_faces
from core.preprocessing import to_gray, equalize, crop_face, laplacian_variance
from core.trainer import train_and_save


class EnrollView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.person_id_var = tk.StringVar()
        top = tk.Frame(self); top.pack(fill="x", pady=8)
        tk.Label(top, text="Person ID / Roll No.:").pack(side="left")
        tk.Entry(top, textvariable=self.person_id_var, width=24).pack(side="left", padx=6)
        tk.Button(top, text="Open Camera Preview", command=self.preview).pack(side="left", padx=6)
        tk.Button(top, text="Start Capture (50+)", command=self.capture).pack(side="left", padx=6)
        self.msg = tk.StringVar()
        tk.Label(self, textvariable=self.msg, anchor="w").pack(fill="x", padx=8)

    def capture(self):
        person_raw = self.person_id_var.get()
        if not person_raw or not person_raw.strip():
            messagebox.showerror("Error", "Enter a Person ID / Roll No.")
            return

        # Sanitize for Windows paths: keep letters, numbers, underscore, dash
        person = person_raw.strip()
        person = re.sub(r'[^A-Za-z0-9_\-]', '_', person)
        person = re.sub(r'_+', '_', person).strip(' _-')
        if not person:
            messagebox.showerror("Error", f"Invalid Person ID: '{person_raw}'. Try e.g. CU003_10070")
            return
        if person != person_raw:
            self.msg.set(f"Sanitized ID: '{person_raw}' → '{person}'")

        os.makedirs("data/faces", exist_ok=True)
        dest = os.path.join("data", "faces", person)
        try:
            os.makedirs(dest, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create folder for '{person}': {e}")
            return

        cap = cv2.VideoCapture(settings.CAMERA_INDEX)
        if not cap.isOpened():
            messagebox.showerror("Camera", f"Cannot open camera index {settings.CAMERA_INDEX}")
            return

        saved = 0
        win_title = f"Enroll – {person}"
        try:
            cv2.namedWindow(win_title, cv2.WINDOW_NORMAL)
            while saved < 50:
                ok, frame = cap.read()
                if not ok:
                    self.msg.set("Camera read failed."); break
                gray = to_gray(frame)
                faces = detect_faces(gray)
                # Draw face boxes
                for (x,y,w,h) in faces:
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (0,200,0), 2)
                # Overlay instructions
                hint = "Look at camera. Ensure single face. Press Q to stop."
                cv2.putText(frame, hint, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                cv2.putText(frame, f"Saved: {saved}/50", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50,220,50), 2)

                if len(faces) == 1:
                    face = crop_face(equalize(gray), faces[0])
                    if laplacian_variance(face) >= 20.0:
                        fn = os.path.join(dest, f"img_{saved:03d}.jpg")
                        cv2.imwrite(fn, face)
                        saved += 1
                        self.msg.set(f"Captured {saved}/50 for {person}")

                cv2.imshow(win_title, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or cv2.getWindowProperty(win_title, cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cap.release()
            try:
                if cv2.getWindowProperty(win_title, cv2.WND_PROP_VISIBLE) >= 0:
                    cv2.destroyWindow(win_title)
            except Exception:
                pass

        if saved >= 50:
            # Auto-retrain model after sufficient capture
            try:
                res = train_and_save()
                if res.get("ok"):
                    messagebox.showinfo("Enrollment", f"Captured {saved} images for {person}. Model retrained.")
                else:
                    messagebox.showwarning("Training", f"Captured {saved} but training failed: {res.get('msg')}")
            except Exception as e:
                messagebox.showwarning("Training", f"Captured {saved} but auto-training errored: {e}")
        else:
            messagebox.showwarning("Enrollment", f"Only captured {saved}. Try again for better quality/lighting.")

    def preview(self):
        cap = cv2.VideoCapture(settings.CAMERA_INDEX)
        if not cap.isOpened():
            messagebox.showerror("Camera", f"Cannot open camera index {settings.CAMERA_INDEX}")
            return
        title = "Enrollment Preview"
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                gray = to_gray(frame)
                faces = detect_faces(gray)
                for (x,y,w,h) in faces:
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (0,200,0), 2)
                cv2.putText(frame, "Press Q to close", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                cv2.imshow(title, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cap.release()
            try:
                if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) >= 0:
                    cv2.destroyWindow(title)
            except Exception:
                pass
