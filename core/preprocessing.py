import cv2
import numpy as np

def to_gray(img):
    """Convert image to grayscale with improved conversion"""
    if len(img.shape) == 3:
        # Use weighted conversion for better grayscale representation
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    return gray

def equalize(gray):
    """Enhanced histogram equalization for better contrast"""
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for better results
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    return clahe.apply(gray)

def enhance_image(img):
    """Apply multiple enhancement techniques for better face recognition"""
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Apply histogram equalization
    equalized = equalize(blurred)
    
    # Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(equalized, 9, 75, 75)
    
    return filtered

def crop_face(gray, box, target=(160,160)):
    """Improved face cropping with better padding and alignment"""
    x, y, w, h = box
    
    # Calculate dynamic padding based on face size
    padding = max(20, min(w, h) // 3)  # More generous padding
    
    # Ensure we don't go out of bounds
    x_start = max(0, x - padding)
    y_start = max(0, y - padding)
    x_end = min(gray.shape[1], x + w + padding)
    y_end = min(gray.shape[0], y + h + padding)
    
    # Extract the face region with padding
    face = gray[y_start:y_end, x_start:x_end]
    
    # If the face region is too small, use the original box
    if face.size == 0 or face.shape[0] < 20 or face.shape[1] < 20:
        x, y, w, h = box
        face = gray[y:y+h, x:x+w]
    
    # Apply image enhancement before resizing
    face = enhance_image(face)
    
    # Resize to target size with better interpolation
    face = cv2.resize(face, target, interpolation=cv2.INTER_CUBIC)
    
    # Apply final enhancement
    face = equalize(face)
    
    return face

def laplacian_variance(gray):
    """Calculate Laplacian variance for blur detection"""
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def is_good_quality_face(face_img, min_variance=50.0):
    """Check if the face image is of good quality for recognition"""
    if face_img is None or face_img.size == 0:
        return False
    
    # Check image size
    if face_img.shape[0] < 50 or face_img.shape[1] < 50:
        return False
    
    # Check for sufficient detail (blur detection)
    variance = laplacian_variance(face_img)
    if variance < min_variance:
        return False
    
    # Check for reasonable brightness (not too dark or too bright)
    mean_brightness = np.mean(face_img)
    if mean_brightness < 30 or mean_brightness > 220:
        return False
    
    return True
