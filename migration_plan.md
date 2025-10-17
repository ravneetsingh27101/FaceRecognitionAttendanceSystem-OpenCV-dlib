# Migration Plan: OpenCV to Alternative Face Recognition

## Current OpenCV Usage Analysis

### Face Detection
- **Current**: Haar Cascade (`cv2.CascadeClassifier`)
- **Files affected**: `core/detection.py`, `gui/views/attendance_view.py`, `gui/views/enroll_view.py`

### Face Recognition  
- **Current**: LBPH (`cv2.face.LBPHFaceRecognizer`)
- **Files affected**: `core/recognizer.py`, `api/routers/attendance.py`

### Image Processing
- **Current**: OpenCV functions (`cv2.cvtColor`, `cv2.equalizeHist`, etc.)
- **Files affected**: `core/preprocessing.py`

## Migration Options

### Option A: face_recognition Library (Recommended)
**Pros**: Easy installation, high accuracy, simple API
**Cons**: Larger dependency, slower than dlib

```python
# Installation
pip install face_recognition

# Usage example
import face_recognition
import cv2

# Face detection
face_locations = face_recognition.face_locations(rgb_image)
# Face recognition  
face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
```

### Option B: MediaPipe (Google)
**Pros**: Fast, lightweight, good accuracy
**Cons**: Different API, requires adaptation

```python
# Installation
pip install mediapipe

# Usage example
import mediapipe as mp
import cv2

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
```

### Option C: InsightFace (Deep Learning)
**Pros**: State-of-the-art accuracy, modern approach
**Cons**: More complex, requires GPU for best performance

```python
# Installation
pip install insightface

# Usage example
import insightface
import cv2

app = insightface.app.FaceAnalysis()
faces = app.get(img)
```

## Implementation Strategy

### Phase 1: Detection Migration
1. Replace Haar Cascade with chosen alternative
2. Update `core/detection.py`
3. Test detection accuracy

### Phase 2: Recognition Migration  
1. Replace LBPH with chosen alternative
2. Update `core/recognizer.py`
3. Retrain models with new approach

### Phase 3: Integration
1. Update API endpoints
2. Update GUI components
3. Test end-to-end functionality

## Recommended Approach: face_recognition

The `face_recognition` library is the most straightforward replacement:

1. **Easy installation**: `pip install face_recognition`
2. **Simple API**: Similar to OpenCV but more powerful
3. **High accuracy**: Better than LBPH
4. **Minimal code changes**: Direct replacement possible

## Next Steps

1. Try dlib installation methods above
2. If dlib fails, proceed with face_recognition library
3. Implement detection replacement first
4. Then implement recognition replacement
5. Test and validate results

