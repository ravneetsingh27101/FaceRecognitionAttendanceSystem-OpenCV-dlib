import os, json, cv2
from core.detection import detect_faces
from core.preprocessing import to_gray, equalize, crop_face, laplacian_variance

DATA_DIR = "data/faces"
LABEL_MAP_PATH = "models/label_map.json"

def load_dataset(min_var=20.0, target=(160,160)):
    images, labels = [], []
    label_map = {}
    inv = {}
    if os.path.exists(LABEL_MAP_PATH):
        inv = json.load(open(LABEL_MAP_PATH,"r",encoding="utf-8"))
        # Create label_map with proper handling of string/integer values
        label_map = {}
        for k, v in inv.items():
            try:
                label_map[int(v)] = k
            except (ValueError, TypeError):
                # If conversion fails, use the value as-is
                label_map[v] = k

    label_counter = 0
    if not os.path.exists(DATA_DIR):
        return images, labels, label_map

    for person_id in sorted(os.listdir(DATA_DIR)):
        person_dir = os.path.join(DATA_DIR, person_id)
        if not os.path.isdir(person_dir): continue
        if person_id not in inv:
            inv[person_id] = str(label_counter)
            label_map[label_counter] = person_id
            label_counter += 1
        try:
            lbl = int(inv[person_id])
        except (ValueError, TypeError):
            # If conversion fails, use the value as-is
            lbl = inv[person_id]
        for f in os.listdir(person_dir):
            p = os.path.join(person_dir, f)
            img = cv2.imread(p)
            if img is None: continue
            gray = to_gray(img)
            faces = detect_faces(gray)
            if len(faces)!=1: continue
            face = crop_face(equalize(gray), faces[0], target=target)
            if laplacian_variance(face) < min_var: continue
            images.append(face)
            labels.append(lbl)
    os.makedirs("models", exist_ok=True)
    json.dump(inv, open(LABEL_MAP_PATH,"w",encoding="utf-8"), indent=2)
    return images, labels, label_map
