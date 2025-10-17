import cv2
import os
import numpy as np

# Load multiple cascade classifiers for better detection
HAAR_FRONTAL = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
HAAR_ALT = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt.xml")
HAAR_ALT2 = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")

def detect_faces(gray):
    """
    Improved face detection using multiple cascade classifiers
    """
    all_faces = []

    # Guard: skip detection on images that are too small to avoid OpenCV assertions
    if gray is None or gray.size == 0 or gray.shape[0] < 40 or gray.shape[1] < 40:
        return np.array([])
    
    # Try different cascade classifiers with optimized parameters
    cascades = [
        (HAAR_FRONTAL, {"scaleFactor": 1.1, "minNeighbors": 4, "minSize": (30, 30)}),
        (HAAR_ALT, {"scaleFactor": 1.08, "minNeighbors": 3, "minSize": (28, 28)}),
        (HAAR_ALT2, {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (24, 24)})
    ]
    
    for cascade, params in cascades:
        try:
            # Do not pass maxSize; OpenCV can assert if it becomes invalid. Let it auto-select.
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=params["scaleFactor"],
                minNeighbors=params["minNeighbors"],
                minSize=params["minSize"],
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            if len(faces) > 0:
                all_faces.extend(faces)
        except Exception:
            continue
    
    # Remove duplicate faces using IoU (Intersection over Union)
    if len(all_faces) > 1:
        all_faces = _remove_duplicate_faces(all_faces)
    
    return np.array(all_faces)

def _remove_duplicate_faces(faces, threshold=0.3):
    """
    Remove duplicate face detections using IoU
    """
    if len(faces) <= 1:
        return faces
    
    # Convert to list of tuples for easier manipulation
    faces_list = [tuple(face) for face in faces]
    unique_faces = []
    
    for face in faces_list:
        is_duplicate = False
        for unique_face in unique_faces:
            if _calculate_iou(face, unique_face) > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_faces.append(face)
    
    return np.array(unique_faces)

def _calculate_iou(face1, face2):
    """
    Calculate Intersection over Union for two face rectangles
    """
    x1, y1, w1, h1 = face1
    x2, y2, w2, h2 = face2
    
    # Calculate intersection
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    
    intersection = (x_right - x_left) * (y_bottom - y_top)
    
    # Calculate union
    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0
