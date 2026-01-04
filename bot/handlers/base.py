"""Base handler utilities."""

from aiogram import Bot
from aiogram.types import Message

from bot.config import get_settings


async def send_typing_action(bot: Bot, chat_id: int) -> None:
    """Send typing indicator if enabled."""
    settings = get_settings()
    if settings.typing_indicator_enabled:
        await bot.send_chat_action(chat_id=chat_id, action="typing")


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    settings = get_settings()
    return user_id in settings.admin_ids


def extract_user_info(message: Message) -> dict:
    """Extract user info from message."""
    user = message.from_user
    if not user:
        return {"id": 0, "username": None, "full_name": "Unknown"}
    
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
    }


def extract_chat_info(message: Message) -> dict:
    """Extract chat info from message."""
    chat = message.chat
    return {
        "id": chat.id,
        "title": chat.title or chat.full_name,
        "type": chat.type,
    }
