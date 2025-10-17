from core.dataset import load_dataset
from core.recognizer_dlib import DlibFaceRecognizer
from core.trainer import MODEL_PATH
import os, numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def evaluate():
    images, labels, _ = load_dataset()
    if not os.path.exists(MODEL_PATH) or len(images)==0:
        return {"ok": False, "msg": "No model or images."}
    rec = DlibFaceRecognizer()
    rec.load(MODEL_PATH)

    preds = []
    for img in images:
        label, conf = rec.predict(img)
        preds.append(label)
    acc = accuracy_score(labels, preds)
    report = classification_report(labels, preds, zero_division=0, output_dict=True)
    cm = confusion_matrix(labels, preds).tolist()
    return {"ok": True, "accuracy": acc, "report": report, "confusion_matrix": cm}
