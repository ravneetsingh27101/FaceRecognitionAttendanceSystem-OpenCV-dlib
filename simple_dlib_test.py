"""
Simple dlib test without model dependencies
"""
import dlib
import numpy as np

def test_basic_dlib():
    """Test basic dlib functionality"""
    print("Testing basic dlib functionality...")
    
    # Test 1: Basic dlib import
    print(f"[OK] dlib version: {dlib.__version__}")
    
    # Test 2: Face detector initialization
    detector = dlib.get_frontal_face_detector()
    print("[OK] Face detector initialized")
    
    # Test 3: Create a simple test image
    test_img = np.zeros((100, 100), dtype=np.uint8)
    faces = detector(test_img)
    print(f"[OK] Face detection working (detected {len(faces)} faces in test image)")
    
    print("\n[SUCCESS] Basic dlib functionality is working!")
    return True

if __name__ == "__main__":
    test_basic_dlib()
