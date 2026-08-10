from fastapi import APIRouter
from database import get_telegram_users, get_telegram_user_conversation, get_telegram_stats

router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.get("/users")
def get_users():
    return get_telegram_users()

@router.get("/users/{sender_id}/conversation")
def get_user_conversation(sender_id: str):
    return get_telegram_user_conversation(sender_id)

@router.get("/stats")
def get_stats():
    return get_telegram_stats()
