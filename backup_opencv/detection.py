import cv2
import os

HAAR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def detect_faces(gray):
    faces = HAAR.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60,60))
    return faces
