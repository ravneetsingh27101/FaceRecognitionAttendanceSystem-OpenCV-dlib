import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    DB_URL: str = os.getenv("DB_URL", "sqlite:///storage/fras.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_secret")
    JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "60"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))
    LBPH_THRESH: float = float(os.getenv("LBPH_THRESH", "85"))
    DEBOUNCE_SECONDS: int = int(os.getenv("DEBOUNCE_SECONDS", "120"))
    SINGLE_FACE_MODE: bool = os.getenv("SINGLE_FACE_MODE", "true").lower() == "true"
    ENABLE_LIVENESS: bool = os.getenv("ENABLE_LIVENESS", "true").lower() == "true"
    LIVENESS_MODE: str = os.getenv("LIVENESS_MODE", "blink")
    # Dlib cosine distance threshold (~0.6 default). Lower is stricter.
    DLIB_THRESH: float = float(os.getenv("DLIB_THRESH", "0.6"))

settings = Settings()
