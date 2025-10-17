"""
Download required dlib models for face recognition
"""
import os
import urllib.request
from pathlib import Path
import bz2
import shutil

def download_and_maybe_decompress(url: str, dest_path: Path) -> bool:
    """Download URL. If URL ends with .bz2, download to temp and decompress to dest_path (.dat)."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if url.endswith('.bz2'):
            tmp_bz2 = dest_path.with_suffix(dest_path.suffix + '.bz2')
            print(f"Downloading {tmp_bz2.name}...")
            urllib.request.urlretrieve(url, tmp_bz2)
            print(f"[OK] Downloaded {tmp_bz2.name}")
            print(f"Decompressing to {dest_path.name}...")
            with bz2.open(tmp_bz2, 'rb') as src, open(dest_path, 'wb') as out:
                shutil.copyfileobj(src, out)
            tmp_bz2.unlink(missing_ok=True)
            print(f"[OK] Wrote {dest_path.name}")
        else:
            print(f"Downloading {dest_path.name}...")
            urllib.request.urlretrieve(url, dest_path)
            print(f"[OK] Downloaded {dest_path.name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        return False

def main():
    """Download required dlib models"""
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Model URLs (these are the standard dlib models)
    models = {
        "shape_predictor_5_face_landmarks.dat": "http://dlib.net/files/shape_predictor_5_face_landmarks.dat.bz2",
        "shape_predictor_68_face_landmarks.dat": "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
        "dlib_face_recognition_resnet_model_v1.dat": "http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2"
    }
    
    print("Downloading dlib models...")
    print("This may take a few minutes depending on your internet connection.")
    print()
    
    success_count = 0
    for filename, url in models.items():
        filepath = models_dir / filename
        
        # Always ensure valid file (simple size check > 1MB)
        need_download = True
        if filepath.exists():
            if filepath.stat().st_size > 1_000_000:
                print(f"[OK] {filename} already exists, skipping...")
                success_count += 1
                need_download = False
            else:
                print(f"[WARN] {filename} seems invalid/corrupt. Re-downloading...")
                try:
                    filepath.unlink()
                except Exception:
                    pass

        if need_download:
            if download_and_maybe_decompress(url, filepath):
                success_count += 1

        # Validate not still compressed (some previous runs may have saved .bz2 as .dat)
        try:
            with open(filepath, 'rb') as check:
                head = check.read(3)
            if head == b'BZh':
                print(f"[WARN] {filename} appears compressed. Decompressing now...")
                tmp_bz2 = filepath.with_suffix(filepath.suffix + '.bz2')
                # rename to .bz2 then decompress
                try:
                    filepath.rename(tmp_bz2)
                except Exception:
                    # copy if rename fails across filesystems
                    shutil.copy2(filepath, tmp_bz2)
                    filepath.unlink(missing_ok=True)
                with bz2.open(tmp_bz2, 'rb') as src, open(filepath, 'wb') as out:
                    shutil.copyfileobj(src, out)
                tmp_bz2.unlink(missing_ok=True)
                print(f"[OK] Decompressed {filename}")
        except Exception as e:
            print(f"[WARN] Could not validate {filename}: {e}")
    
    print()
    if success_count == len(models):
        print("[OK] All models downloaded successfully!")
        print("You can now use dlib-based face recognition.")
    else:
        print(f"[ERROR] Only {success_count}/{len(models)} models downloaded successfully.")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main()
