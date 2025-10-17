"""
Dlib-based face recognition module
Replaces OpenCV LBPH with dlib's face recognition
"""
import dlib
import os
import numpy as np
import pickle
from config.settings import settings
from core.recognizer_base import RecognizerBase
import cv2

class DlibFaceRecognizer(RecognizerBase):
    def __init__(self):
        # Initialize dlib's face recognition components
        # Prefer 5-point predictor if available (works with face_recognition model), else 68-point
        self.predictor_path = (
            "models/shape_predictor_5_face_landmarks.dat"
            if os.path.exists("models/shape_predictor_5_face_landmarks.dat")
            else "models/shape_predictor_68_face_landmarks.dat"
        )
        self.face_rec_model_path = "models/dlib_face_recognition_resnet_model_v1.dat"
        
        # Check if required models exist
        if not os.path.exists(self.predictor_path):
            raise FileNotFoundError(f"Shape predictor not found: {self.predictor_path}")
        if not os.path.exists(self.face_rec_model_path):
            raise FileNotFoundError(f"Face recognition model not found: {self.face_rec_model_path}")
            
        # Initialize dlib components
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(self.predictor_path)
        self.face_rec = dlib.face_recognition_model_v1(self.face_rec_model_path)
        
        # Store face encodings and labels
        self.face_encodings = []
        self.labels = []
        self.label_map = {}
        
    def train(self, images, labels):
        """
        Train the recognizer with face images and labels
        """
        self.face_encodings = []
        self.labels = list(labels)
        
        for img in images:
            # Get face encoding using dlib
            encoding = self._get_face_encoding(img)
            if encoding is not None:
                self.face_encodings.append(encoding)
            else:
                # If no face found, add zero vector
                self.face_encodings.append(np.zeros(128))
                
        # Create label mapping
        unique_labels = list(set(labels))
        self.label_map = {label: idx for idx, label in enumerate(unique_labels)}
        
    def predict(self, img):
        """
        Predict the label and confidence for a face image
        """
        if not self.face_encodings:
            return -1, 0.0
            
        # Get face encoding for input image
        face_encoding = self._get_face_encoding(img)
        if face_encoding is None:
            return -1, 0.0
            
        # Calculate distances to all known faces
        distances = []
        for known_encoding in self.face_encodings:
            distance = np.linalg.norm(face_encoding - known_encoding)
            distances.append(distance)
            
        # Find the closest match
        min_distance = min(distances)
        closest_idx = distances.index(min_distance)
        
        # Convert distance to confidence (lower distance = higher confidence)
        # dlib typically uses 0.6 as threshold for face recognition
        confidence = max(0.0, 1.0 - (min_distance / 0.6))
        
        # Get the label for the closest match
        label = self.labels[closest_idx]
        
        return int(label), float(confidence)
        
    def _get_face_encoding(self, img):
        """
        Get face encoding using dlib
        """
        # Ensure RGB image for descriptor; detector works with grayscale or RGB
        if len(img.shape) == 3:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        # Detect faces
        faces = self.detector(rgb)
        if len(faces) == 0:
            return None
            
        # Get landmarks for the first face
        face = faces[0]
        landmarks = self.predictor(rgb, face)
        
        # Get face encoding
        face_encoding = self.face_rec.compute_face_descriptor(rgb, landmarks)
        return np.array(face_encoding)
        
    def save(self, path: str):
        """
        Save the trained model
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'face_encodings': self.face_encodings,
            'labels': self.labels,
            'label_map': self.label_map
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
            
    def load(self, path: str):
        """
        Load a trained model
        """
        if not os.path.exists(path):
            raise FileNotFoundError(path)
            
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
            
        self.face_encodings = model_data['face_encodings']
        self.labels = model_data['labels']
        self.label_map = model_data['label_map']
