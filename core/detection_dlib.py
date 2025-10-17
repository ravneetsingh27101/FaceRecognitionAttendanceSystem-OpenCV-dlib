"""
Dlib-based face detection module
Replaces OpenCV Haar Cascade with dlib's HOG detector
"""
import dlib
import cv2
import numpy as np

class DlibFaceDetector:
    def __init__(self):
        # Initialize dlib's face detector (HOG + SVM)
        self.detector = dlib.get_frontal_face_detector()
        
    def detect_faces(self, gray_image):
        """
        Detect faces in grayscale image using dlib
        Returns list of (x, y, w, h) rectangles
        """
        # dlib expects numpy array
        if not isinstance(gray_image, np.ndarray):
            gray_image = np.array(gray_image)
            
        # Detect faces using dlib
        faces = self.detector(gray_image)
        
        # Convert dlib rectangles to (x, y, w, h) format
        face_rects = []
        for face in faces:
            x = face.left()
            y = face.top()
            w = face.width()
            h = face.height()
            face_rects.append((x, y, w, h))
            
        return face_rects

# Global detector instance
_detector = DlibFaceDetector()

def detect_faces(gray):
    """
    Drop-in replacement for OpenCV detect_faces function
    """
    return _detector.detect_faces(gray)

