from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.init_db import Student, Base
from config.settings import settings

engine = create_engine(settings.DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
router = APIRouter()

class StudentOut(BaseModel):
    id: int
    name: str
    roll_no: str
    class Config: orm_mode = True

@router.get("/", response_model=List[StudentOut])
def list_students():
    db = SessionLocal()
    studs = db.query(Student).all()
    db.close()
    return studs
