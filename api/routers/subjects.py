from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.init_db import Subject, Base
from config.settings import settings

engine = create_engine(settings.DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
router = APIRouter()

class SubjectOut(BaseModel):
    id: int
    code: str
    name: str
    class Config: orm_mode = True

@router.get("/", response_model=List[SubjectOut])
def list_subjects():
    db = SessionLocal()
    subs = db.query(Subject).all()
    db.close()
    return subs
