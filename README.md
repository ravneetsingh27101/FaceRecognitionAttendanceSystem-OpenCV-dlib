# FRAS — Face Recognition Attendance System (LBPH, Tkinter + FastAPI)

This is a compact, local-first Face Recognition Attendance System with:
- Tkinter GUI (Enrollment → Training → Real-time Attendance → Reports)
- LBPH recognizer (OpenCV contrib)
- SQLite via SQLAlchemy
- FastAPI REST (JWT)
- Exports: CSV/XLSX/PDF

## Quick Start
```bash
python -m venv .venv && . .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_demo.py
python run_gui.py
# (optional API)
python run_api.py
```
Default admin: `admin@local` / `Admin@123`
Edit `.env` to tweak camera, thresholds, and liveness.
