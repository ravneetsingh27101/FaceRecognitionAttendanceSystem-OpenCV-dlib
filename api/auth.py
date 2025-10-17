from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.init_db import Base, User, Role
from config.settings import settings

engine = create_engine(settings.DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    username: str
    password: str

def create_access_token(sub: str):
    payload = {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

@router.post("/login", response_model=Token)
def login(payload: LoginIn):
    db = SessionLocal()
    user = db.query(User).filter(User.email==payload.username).first()
    # Lazy import bcrypt so app can start without the wheel; login will fail if unavailable
    try:
        import bcrypt  # type: ignore
        bcrypt_ok = bcrypt.checkpw(payload.password.encode(), user.password_hash.encode()) if user else False
    except Exception as e:
        raise HTTPException(500, f"Auth unavailable: bcrypt not installed ({e})")
    if user is None or not bcrypt_ok:
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token(sub=str(user.email))
    return {"access_token": token}
