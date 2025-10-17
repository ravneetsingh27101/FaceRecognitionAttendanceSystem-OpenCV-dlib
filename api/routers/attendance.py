from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import cv2, numpy as np, json, os, time
from core.detection import detect_faces
from core.preprocessing import to_gray, equalize, crop_face
from core.trainer import MODEL_PATH
from config.settings import settings

router = APIRouter()
last_mark = {}

class MarkOut(BaseModel):
    student_id: Optional[str]
    status: str
    confidence: Optional[float]=None

@router.post("/mark", response_model=MarkOut)
async def mark_attendance(subject_id:int, class_id:int=0, file: UploadFile = File(...)):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(400, "Model not trained")
    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Bad image")
    gray = to_gray(img)
    faces = detect_faces(gray)
    try:
        from core.recognizer_dlib import DlibFaceRecognizer  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"Recognizer unavailable: {e}")
    rec = DlibFaceRecognizer(); rec.load(MODEL_PATH)
    label_map = json.load(open("models/label_map.json","r"))
    inv = {int(v):k for k,v in label_map.items()}

    # If single-face mode enforced
    if settings.SINGLE_FACE_MODE and len(faces)!=1:
        raise HTTPException(400, "Require single face")

    results = []
    for (x,y,w,h) in faces:
        face = crop_face(equalize(gray), (x,y,w,h))
        lbl, conf = rec.predict(face)
        person = inv.get(lbl, "Unknown")
        now = time.time()
        if person != "Unknown" and conf >= (1.0 - (settings.DLIB_THRESH/0.6)):
            # conf is mapped from distance; accept if under distance threshold
            if now - last_mark.get(person, 0) >= settings.DEBOUNCE_SECONDS:
                last_mark[person] = now
                results.append({"student_id": person, "status":"Present", "confidence": conf})
            else:
                results.append({"student_id": person, "status":"Debounced", "confidence": conf})
        else:
            results.append({"student_id": None, "status":"Uncertain", "confidence": conf})

    # Return the most confident positive result if any, else the first uncertain
    positives = [r for r in results if r["status"] in ("Present","Debounced")]
    if positives:
        return max(positives, key=lambda r: r.get("confidence") or 0.0)
    return results[0] if results else {"student_id": None, "status":"NoFace"}
