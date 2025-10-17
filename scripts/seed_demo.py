from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.init_db import Base, Role, User, Student, Subject, Class
from config.settings import settings
import bcrypt

engine = create_engine(settings.DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    admin_role = db.query(Role).filter_by(name="Admin").first()
    if not admin_role:
        admin_role = Role(name="Admin")
        db.add(admin_role)

    operator_role = db.query(Role).filter_by(name="Operator").first()
    if not operator_role:
        operator_role = Role(name="Operator")
        db.add(operator_role)

    admin = db.query(User).filter_by(email="admin@local").first()
    if not admin:
        admin = User(email="admin@local", password_hash=hash_pw("Admin@123"), role=admin_role)
        db.add(admin)

    # Demo entities
    s1 = db.query(Student).filter_by(roll_no="CU001").first() or Student(name="Alice", roll_no="CU001")
    s2 = db.query(Student).filter_by(roll_no="CU002").first() or Student(name="Bob", roll_no="CU002")
    sub = db.query(Subject).filter_by(code="AI-101").first() or Subject(code="AI-101", name="Intro to AI")
    cls = db.query(Class).filter_by(name="MCA-A").first() or Class(name="MCA-A")

    db.add_all([s1, s2, sub, cls])
    db.commit()
    db.close()
    print("Seeded demo data and admin user (admin@local / Admin@123).")

if __name__ == "__main__":
    main()
