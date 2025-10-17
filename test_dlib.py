"""
Test script to verify dlib installation and functionality
"""
import os
import sys
import cv2
import numpy as np

def test_dlib_import():
    """Test if dlib can be imported"""
    try:
        import dlib
        print(f"[OK] dlib imported successfully, version: {dlib.__version__}")
        return True
    except ImportError as e:
        print(f"[ERROR] Failed to import dlib: {e}")
        return False

def test_dlib_models():
    """Test if required dlib models exist"""
    models = [
        "models/shape_predictor_68_face_landmarks.dat",
        "models/dlib_face_recognition_resnet_model_v1.dat"
    ]
    
    all_exist = True
    for model in models:
        if os.path.exists(model):
            print(f"[OK] Model exists: {model}")
        else:
            print(f"[ERROR] Model missing: {model}")
            all_exist = False
    
    return all_exist

def test_dlib_face_detection():
    """Test dlib face detection"""
    try:
        from core.detection_dlib import detect_faces
        
        # Create a simple test image (black image)
        test_img = np.zeros((100, 100), dtype=np.uint8)
        
        # Test face detection
        faces = detect_faces(test_img)
        print(f"[OK] dlib face detection working, detected {len(faces)} faces")
        return True
        
    except Exception as e:
        print(f"[ERROR] dlib face detection failed: {e}")
        return False

def test_dlib_face_recognition():
    """Test dlib face recognition"""
    try:
        from core.recognizer_dlib import DlibFaceRecognizer
        
        # This will fail if models don't exist, which is expected
        recognizer = DlibFaceRecognizer()
        print("[OK] dlib face recognition initialized successfully")
        return True
        
    except FileNotFoundError as e:
        print(f"[ERROR] dlib models not found: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] dlib face recognition failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Testing dlib Installation ===")
    print()
    
    tests = [
        ("dlib import", test_dlib_import),
        ("dlib models", test_dlib_models),
        ("face detection", test_dlib_face_detection),
        ("face recognition", test_dlib_face_recognition)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("[OK] All tests passed! dlib is ready to use.")
    else:
        print("[WARN] Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

