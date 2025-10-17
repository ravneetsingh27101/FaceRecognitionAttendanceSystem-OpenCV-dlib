from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os, re, base64, io, csv, json, time
from datetime import datetime
import cv2
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.init_db import Base, Student, AttendanceLog
from config.settings import settings
from core.preprocessing import to_gray, equalize, crop_face
from core.detection import detect_faces
from core.trainer import train_and_save, MODEL_PATH


engine = create_engine(settings.DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

router = APIRouter()


def _b64_to_image(b64: str) -> np.ndarray:
    # Strip data URL prefix if present
    if b64.startswith("data:"):
        try:
            b64 = b64.split(",", 1)[1]
        except Exception:
            pass
    try:
        raw = base64.b64decode(b64)
    except Exception:
        raise HTTPException(400, "Invalid base64 image")
    nparr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Invalid image data")
    return img


class RegisterIn(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    class_name: Optional[str] = None
    photo_base64: Optional[str] = None


class RegisterOut(BaseModel):
    ok: bool
    msg: str
    saved: int = 0


@router.post("/register_student", response_model=RegisterOut)
def register_student(payload: RegisterIn):
    person_raw = payload.id or ""
    if not person_raw.strip():
        raise HTTPException(400, "Missing student id")

    # sanitize filesystem id
    person = re.sub(r"[^A-Za-z0-9_\-]", "_", person_raw.strip())
    person = re.sub(r"_+", "_", person).strip(" _-")
    if not person:
        raise HTTPException(400, "Invalid student id after sanitization")

    os.makedirs("data/faces", exist_ok=True)
    dest = os.path.join("data", "faces", person)
    os.makedirs(dest, exist_ok=True)

    saved = 0
    # If a single photo provided, store as img_000.jpg (preprocessed crop if a face is found)
    if payload.photo_base64:
        img = _b64_to_image(payload.photo_base64)
        gray = to_gray(img)
        faces = detect_faces(gray)
        
        if len(faces) >= 1:
            # Find the largest face (most likely to be the main subject)
            largest_face = max(faces, key=lambda f: f[2] * f[3])  # f[2] = width, f[3] = height
            x, y, w, h = largest_face
            
            # Save the best face with improved cropping
            face = crop_face(equalize(gray), (x, y, w, h))
            fn = os.path.join(dest, f"img_{saved:03d}.jpg")
            cv2.imwrite(fn, face)
            saved += 1
            
            # Also save additional faces if detected
            for i, (x, y, w, h) in enumerate(faces[1:3]):  # Skip the first (largest) face
                face = crop_face(equalize(gray), (x, y, w, h))
                fn = os.path.join(dest, f"img_{saved:03d}.jpg")
                cv2.imwrite(fn, face)
                saved += 1
        else:
            # If no face detected, save the center portion of the image
            h, w = gray.shape
            center_x, center_y = w // 2, h // 2
            crop_size = min(w, h) // 2
            x = max(0, center_x - crop_size // 2)
            y = max(0, center_y - crop_size // 2)
            cropped = gray[y:y+crop_size, x:x+crop_size]
            cropped = cv2.resize(cropped, (160, 160))
            fn = os.path.join(dest, f"img_{saved:03d}.jpg")
            cv2.imwrite(fn, cropped)
            saved += 1

    # Upsert student basic info in DB
    db = SessionLocal()
    try:
        existing = db.query(Student).filter(Student.roll_no == person).first()
        if existing:
            # update name if provided
            if payload.name:
                existing.name = payload.name
            db.commit()
        else:
            s = Student(name=payload.name or person, roll_no=person)
            db.add(s)
            db.commit()
    finally:
        db.close()

    # Optionally auto-train if at least 2 total images exist in dataset
    try:
        res = train_and_save()
        msg = res.get("msg", "Model updated")
    except Exception as e:
        msg = f"Registered. Training skipped: {e}"

    return {"ok": True, "msg": msg, "saved": int(saved)}


class Capture50In(BaseModel):
    student_id: str
    photos_base64: List[str]  # List of base64 encoded images


@router.post("/capture_50_images", response_model=RegisterOut)
def capture_50_images(payload: Capture50In):
    """Capture 50 images for a student to improve training accuracy"""
    person_raw = payload.student_id or ""
    if not person_raw.strip():
        raise HTTPException(400, "Missing student id")

    # sanitize filesystem id
    person = re.sub(r"[^A-Za-z0-9_\-]", "_", person_raw.strip())
    person = re.sub(r"_+", "_", person).strip(" _-")
    if not person:
        raise HTTPException(400, "Invalid student id after sanitization")

    os.makedirs("data/faces", exist_ok=True)
    dest = os.path.join("data", "faces", person)
    os.makedirs(dest, exist_ok=True)

    saved = 0
    max_images = 50
    
    # Process up to 50 images
    for i, photo_b64 in enumerate(payload.photos_base64[:max_images]):
        try:
            img = _b64_to_image(photo_b64)
            gray = to_gray(img)
            faces = detect_faces(gray)

            if len(faces) >= 1:
                # Use the largest face for better quality
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                face = crop_face(equalize(gray), (x, y, w, h))

                # Check face quality before saving
                from core.preprocessing import is_good_quality_face
                if is_good_quality_face(face, min_variance=20.0):
                    fn = os.path.join(dest, f"img_{saved:03d}.jpg")
                    cv2.imwrite(fn, face)
                    saved += 1
                else:
                    # Skip poor quality images
                    continue
            else:
                # Fall back to saving resized grayscale image
                gray = cv2.resize(gray, (160, 160))
                fn = os.path.join(dest, f"img_{saved:03d}.jpg")
                cv2.imwrite(fn, gray)
                saved += 1

        except Exception as e:
            print(f"Error processing image {i}: {e}")
            continue

    # Auto-train the model with the new images
    try:
        res = train_and_save()
        msg = f"Captured {saved} images. {res.get('msg', 'Model updated')}"
    except Exception as e:
        msg = f"Captured {saved} images. Training failed: {e}"

    return {"ok": True, "msg": msg, "saved": int(saved)}


class MarkIn(BaseModel):
    photo_base64: str
    subject_id: Optional[int] = None
    class_id: Optional[int] = None


class MarkOut(BaseModel):
    student_id: Optional[str]
    status: str
    confidence: Optional[float] = None


_last_mark_web: Dict[str, float] = {}


@router.post("/mark", response_model=MarkOut)
def mark(payload: MarkIn):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(400, "Model not trained")

    img = _b64_to_image(payload.photo_base64)
    gray = to_gray(img)  # Use improved grayscale conversion
    faces = detect_faces(gray)

    # single-face mode
    if settings.SINGLE_FACE_MODE and len(faces) != 1:
        raise HTTPException(400, "Require single face")

    # Lazy import to avoid requiring dlib at app startup
    try:
        from core.recognizer_dlib import DlibFaceRecognizer  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"Recognizer unavailable: {e}")
    rec = DlibFaceRecognizer(); rec.load(MODEL_PATH)
    label_map = json.load(open("models/label_map.json", "r", encoding="utf-8"))
    # Create inverse mapping, handling both string and integer values
    inv = {}
    for k, v in label_map.items():
        try:
            # Try to convert to int, if it fails, use as string
            inv[int(v)] = k
        except (ValueError, TypeError):
            # If conversion fails, use the value as-is
            inv[v] = k

    best = None
    for (x, y, w, h) in faces:
        # Use improved face cropping with better preprocessing
        face = crop_face(equalize(gray), (x, y, w, h))
        
        # Check face quality before recognition
        from core.preprocessing import is_good_quality_face
        if not is_good_quality_face(face, min_variance=30.0):
            continue  # Skip poor quality faces
        
        lbl, conf = rec.predict(face)
        person = inv.get(lbl, "Unknown")
        if best is None or (conf or 0) > (best[2] or 0):
            best = (person, lbl, conf)

    if not best:
        return {"student_id": None, "status": "NoFace"}

    person, _, conf = best
    now = time.time()
    accept_conf = (conf >= (1.0 - (settings.DLIB_THRESH / 0.6)))

    if person != "Unknown" and accept_conf:
        if now - _last_mark_web.get(person, 0) >= settings.DEBOUNCE_SECONDS:
            _last_mark_web[person] = now
            # Write to today's CSV (same as GUI behavior)
            _write_log(person)
            return {"student_id": person, "status": "Present", "confidence": float(conf)}
        else:
            return {"student_id": person, "status": "Debounced", "confidence": float(conf)}
    return {"student_id": None, "status": "Uncertain", "confidence": float(conf or 0.0)}


def _write_log(person_id: str):
    os.makedirs("reports/exports", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path = f"reports/exports/{today}.csv"
    hdr = "person_id,timestamp,status\n"
    if not os.path.exists(path):
        open(path, "w", encoding="utf-8").write(hdr)
    # prevent duplicate rows for the same person today
    already = False
    try:
        with open(path, "r", encoding="utf-8") as f:
            prefix = f"{person_id},"
            for line in f:
                if line.startswith(prefix):
                    already = True
                    break
    except Exception:
        pass
    if not already:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{person_id},{datetime.now().isoformat()},Present\n")


class StudentOut(BaseModel):
    id: int
    name: str
    roll_no: str


@router.get("/students", response_model=List[StudentOut])
def list_students_web():
    db = SessionLocal()
    try:
        studs = db.query(Student).all()
        return studs
    finally:
        db.close()


@router.get("/records")
def records(date: Optional[str] = None):
    # Return rows from exports CSV identified by date (YYYY-MM-DD), or today's if not given
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    path = f"reports/exports/{date}.csv"
    rows = []
    if os.path.exists(path):
        try:
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    rows.append(row)
        except Exception:
            pass
    return {"rows": rows, "date": date}


@router.get("/stats")
def stats():
    """Return summary counts for home dashboard.
    present_today derived from CSV (GUI logging),
    total_students from DB.
    """
    # students count from DB
    db = SessionLocal()
    try:
        total_students = db.query(Student).count()
    finally:
        db.close()

    # present today from CSV
    today = datetime.now().strftime("%Y-%m-%d")
    path = f"reports/exports/{today}.csv"
    present_today = 0
    if os.path.exists(path):
        try:
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if (row.get("status") or "").lower() == "present":
                        present_today += 1
        except Exception:
            pass

    # Fake overall rate based on present/total if available
    attendance_rate = 0
    if total_students > 0:
        attendance_rate = round((present_today / total_students) * 100)

    return {
        "total_students": total_students,
        "attendance_rate": attendance_rate,
        "present_today": present_today,
    }


# Admin endpoints
class AdminLoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
def admin_login(payload: AdminLoginIn):
    """Admin login endpoint (accepts JSON body)"""
    # Simple admin authentication (in production, use proper JWT)
    if payload.email == "admin@local" and payload.password == "Admin@123":
        return {"ok": True, "token": "admin_token_123", "message": "Login successful"}
    else:
        raise HTTPException(401, "Invalid credentials")


@router.post("/reset_database")
def reset_database():
    """Reset entire database - DANGER ZONE"""
    try:
        db = SessionLocal()
        try:
            # Ensure FK behavior is enabled (SQLite)
            try:
                db.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass

            # Delete all attendance records first (FK -> Student)
            db.query(AttendanceLog).delete()
            # Then delete all students
            db.query(Student).delete()
            db.commit()
        finally:
            db.close()

        # Delete all face training data
        import shutil
        faces_dir = "data/faces"
        if os.path.exists(faces_dir):
            shutil.rmtree(faces_dir)
        os.makedirs(faces_dir, exist_ok=True)

        # Delete trained models
        model_files = ["models/dlib_recognizer.pkl", "models/label_map.json"]
        for model_file in model_files:
            if os.path.exists(model_file):
                os.remove(model_file)

        # Delete exported attendance CSVs
        exports_dir = "reports/exports"
        if os.path.exists(exports_dir):
            for fn in os.listdir(exports_dir):
                try:
                    os.remove(os.path.join(exports_dir, fn))
                except Exception:
                    pass

        # Release pooled connections
        try:
            engine.dispose()
        except Exception:
            pass

        return {"ok": True, "message": "Database, faces, models, and exports reset"}
    except Exception as e:
        return {"ok": False, "message": f"Error resetting database: {str(e)}"}


@router.post("/delete_faces")
def delete_faces():
    """Delete all enrolled faces - DANGER ZONE"""
    try:
        # Delete all face training data
        import shutil
        faces_dir = "data/faces"
        if os.path.exists(faces_dir):
            shutil.rmtree(faces_dir)
        os.makedirs(faces_dir, exist_ok=True)
        
        # Delete trained models
        model_files = ["models/dlib_recognizer.pkl", "models/label_map.json"]
        for model_file in model_files:
            if os.path.exists(model_file):
                os.remove(model_file)
        
        return {"ok": True, "message": "All faces deleted successfully"}
    except Exception as e:
        return {"ok": False, "message": f"Error deleting faces: {str(e)}"}


@router.post("/delete_attendance")
def delete_attendance():
    """Delete all attendance records - DANGER ZONE"""
    try:
        db = SessionLocal()
        try:
            # Enable FK
            try:
                db.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass

            # Delete all attendance records in DB
            db.query(AttendanceLog).delete()
            db.commit()
        finally:
            db.close()

        # Delete exported CSVs as well
        exports_dir = "reports/exports"
        if os.path.exists(exports_dir):
            for fn in os.listdir(exports_dir):
                try:
                    os.remove(os.path.join(exports_dir, fn))
                except Exception:
                    pass

        try:
            engine.dispose()
        except Exception:
            pass

        return {"ok": True, "message": "Attendance records cleared (DB + CSV)"}
    except Exception as e:
        return {"ok": False, "message": f"Error deleting attendance records: {str(e)}"}


