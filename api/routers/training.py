from fastapi import APIRouter
from core.trainer import train_and_save
router = APIRouter()

@router.post("/")
def train():
    return train_and_save()
