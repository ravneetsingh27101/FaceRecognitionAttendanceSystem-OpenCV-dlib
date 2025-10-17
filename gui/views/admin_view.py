import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.init_db import User, Role, Subject, Class, Base
from config.settings import settings
import bcrypt
import os, shutil, glob

class AdminView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Button(self, text="Create Operator", command=self.create_operator).pack(pady=6)
        tk.Button(self, text="Create Subject AI-102", command=self.create_subject).pack(pady=6)
        tk.Button(self, text="Create Class MCA-B", command=self.create_class).pack(pady=6)
        tk.Button(self, text="Reset Database (Drop & Recreate)", command=self.reset_database, fg="#b00000").pack(pady=12)
        tk.Button(self, text="Reset Face Data (images, models, labels, reports)", command=self.reset_face_assets, fg="#b00000").pack(pady=6)

        self.engine = create_engine(settings.DB_URL, echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_operator(self):
        db = self.Session()
        role = db.query(Role).filter_by(name="Operator").first()
        if not role:
            role = Role(name="Operator")
            db.add(role); db.commit()
        email = "operator@local"
        if db.query(User).filter_by(email=email).first():
            messagebox.showinfo("Operator", "operator@local already exists.")
            db.close(); return
        pw = bcrypt.hashpw("Operator@123".encode(), bcrypt.gensalt()).decode()
        user = User(email=email, password_hash=pw, role=role)
        db.add(user); db.commit(); db.close()
        messagebox.showinfo("Operator", "Created operator@local / Operator@123")

    def create_subject(self):
        db = self.Session()
        if not db.query(Subject).filter_by(code="AI-102").first():
            db.add(Subject(code="AI-102", name="Advanced AI")); db.commit()
            messagebox.showinfo("Subject", "Created AI-102")
        else:
            messagebox.showinfo("Subject", "AI-102 exists.")
        db.close()

    def create_class(self):
        db = self.Session()
        if not db.query(Class).filter_by(name="MCA-B").first():
            db.add(Class(name="MCA-B")); db.commit()
            messagebox.showinfo("Class", "Created MCA-B")
        else:
            messagebox.showinfo("Class", "MCA-B exists.")
        db.close()

    def reset_database(self):
        if not messagebox.askyesno("Reset Database", "This will DELETE ALL DATA and recreate empty tables. Continue?"):
            return
        try:
            engine = self.engine
            # Drop all tables then recreate
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            messagebox.showinfo("Reset Database", "Database has been reset. You may want to run seed_demo.py.")
        except Exception as e:
            messagebox.showerror("Reset Database", f"Failed to reset: {e}")

    def reset_face_assets(self):
        if not messagebox.askyesno("Reset Face Data", "This will DELETE all enrolled faces, generated models, label maps, and exported reports. Continue?"):
            return
        errors = []
        # Delete enrolled face images
        try:
            faces_dir = os.path.join("data", "faces")
            if os.path.exists(faces_dir):
                shutil.rmtree(faces_dir)
            os.makedirs(faces_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"faces: {e}")
        # Delete generated models (keep dlib base *.dat files)
        try:
            models_dir = "models"
            if os.path.exists(models_dir):
                # remove known generated files
                for p in [
                    os.path.join(models_dir, "lbph_model.yml"),
                    os.path.join(models_dir, "dlib_recognizer.pkl"),
                    os.path.join(models_dir, "label_map.json"),
                ]:
                    try:
                        if os.path.exists(p): os.remove(p)
                    except Exception as e:
                        errors.append(f"models:{os.path.basename(p)} {e}")
        except Exception as e:
            errors.append(f"models: {e}")
        # Delete exported reports
        try:
            reports_dir = os.path.join("reports", "exports")
            if os.path.exists(reports_dir):
                for f in glob.glob(os.path.join(reports_dir, "*.csv")):
                    try:
                        os.remove(f)
                    except Exception as e:
                        errors.append(f"reports:{os.path.basename(f)} {e}")
        except Exception as e:
            errors.append(f"reports: {e}")

        if errors:
            messagebox.showwarning("Reset Face Data", "Completed with warnings:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Reset Face Data", "All face data, generated models, labels, and reports have been cleared.")
