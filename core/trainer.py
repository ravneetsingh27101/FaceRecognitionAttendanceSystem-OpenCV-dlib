import json
from core.dataset import load_dataset, LABEL_MAP_PATH
def _load_recognizer():
    # Lazy import to avoid requiring dlib for non-recognition operations
    from core.recognizer_dlib import DlibFaceRecognizer  # type: ignore
    return DlibFaceRecognizer()

MODEL_PATH = "models/dlib_recognizer.pkl"

def train_and_save():
    images, labels, label_map = load_dataset()
    if len(images) < 2:
        return {"ok": False, "msg":"Not enough images to train."}
    rec = _load_recognizer()
    rec.train(images, labels)
    rec.save(MODEL_PATH)
    # persist label map for runtime inverse lookup
    json.dump({str(k): str(v) for k,v in label_map.items()}, open(LABEL_MAP_PATH, "w", encoding="utf-8"), indent=2)
    return {"ok": True, "msg":"Model trained.", "num_images": len(images), "classes": len(set(labels))}
