from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os
from config.settings import settings

Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    roll_no = Column(String, unique=True)

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Present")
    note = Column(Text)

def main():
    os.makedirs("storage", exist_ok=True)
    engine = create_engine(settings.DB_URL, echo=False, future=True)
    Base.metadata.create_all(engine)
    print(f"Database initialised at {settings.DB_URL}")

if __name__ == "__main__":
    main()
