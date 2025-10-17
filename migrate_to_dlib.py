"""
Migration script to switch from OpenCV to dlib
This script helps migrate your face recognition system
"""
import os
import shutil
from pathlib import Path

def backup_original_files():
    """Backup original OpenCV files"""
    print("Creating backup of original files...")
    
    files_to_backup = [
        "core/detection.py",
        "core/recognizer.py"
    ]
    
    backup_dir = Path("backup_opencv")
    backup_dir.mkdir(exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)
            print(f"[OK] Backed up {file_path} to {backup_path}")
        else:
            print(f"[WARN] File not found: {file_path}")

def update_imports():
    """Update import statements in affected files"""
    print("\nUpdating import statements...")
    
    # Files that need import updates
    files_to_update = [
        "api/routers/attendance.py",
        "gui/views/attendance_view.py", 
        "gui/views/enroll_view.py",
        "core/dataset.py"
    ]
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"Updating imports in {file_path}...")
            # This would need manual editing based on specific usage
            print(f"  [WARN] Manual review needed for {file_path}")

def create_dlib_requirements():
    """Create updated requirements.txt with dlib"""
    print("\nCreating updated requirements.txt...")
    
    # Read current requirements
    with open("requirements.txt", "r") as f:
        lines = f.readlines()
    
    # Remove opencv-contrib-python and add dlib
    new_lines = []
    for line in lines:
        if "opencv-contrib-python" not in line:
            new_lines.append(line)
    
    # Add dlib and keep opencv-python for basic image operations
    new_lines.append("dlib~=20.0.0\n")
    new_lines.append("opencv-python~=4.9.0.80\n")  # Keep basic OpenCV
    
    with open("requirements_dlib.txt", "w") as f:
        f.writelines(new_lines)
    
    print("[OK] Created requirements_dlib.txt")

def main():
    """Main migration process"""
    print("=== OpenCV to dlib Migration Helper ===")
    print()
    
    # Step 1: Backup original files
    backup_original_files()
    
    # Step 2: Create dlib requirements
    create_dlib_requirements()
    
    # Step 3: Update imports (manual step)
    update_imports()
    
    print("\n=== Migration Steps Completed ===")
    print()
    print("Next steps:")
    print("1. Download dlib models: python scripts/download_dlib_models.py")
    print("2. Install new requirements: pip install -r requirements_dlib.txt")
    print("3. Update your code to use dlib modules:")
    print("   - Replace 'from core.detection import detect_faces' with 'from core.detection_dlib import detect_faces'")
    print("   - Replace 'from core.recognizer import LBPHRecognizer' with 'from core.recognizer_dlib import DlibFaceRecognizer'")
    print("4. Test the new implementation")
    print()
    print("[WARN] Important: Test thoroughly before deploying to production!")

if __name__ == "__main__":
    main()
