import cv2
import os
import numpy as np
from config.settings import settings
from core.recognizer_base import RecognizerBase

class LBPHRecognizer(RecognizerBase):
    def __init__(self):
        if not hasattr(cv2, "face"):
            raise RuntimeError("opencv-contrib-python is required for LBPH (cv2.face.*).")
        self.model = cv2.face.LBPHFaceRecognizer_create()

    def train(self, images, labels):
        self.model.train(images, np.array(labels))

    def predict(self, img):
        label, conf = self.model.predict(img)
        return int(label), float(conf)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.write(path)

    def load(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        self.model.read(path)
