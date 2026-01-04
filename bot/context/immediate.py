"""Get last N messages for immediate context."""

from datetime import datetime

from bot.db.session import get_session
from bot.db.repositories import MessageRepository


async def get_immediate_context(
    chat_id: int,
    limit: int = 100,
) -> list[dict]:
    """
    Get the last N messages from chat as context.
    
    Returns list of message dicts with role and content.
    """
    async with get_session() as session:
        repo = MessageRepository(session)
        messages = await repo.get_recent(chat_id, limit)
        
        return [
            {
                "id": msg.id,
                "user_id": msg.user_id,
                "content": msg.content,
                "is_bot": msg.is_bot_message,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]


async def get_context_since(
    chat_id: int,
    since: datetime,
) -> list[dict]:
    """Get all messages since a specific datetime."""
    async with get_session() as session:
        repo = MessageRepository(session)
        messages = await repo.get_since(chat_id, since)
        
        return [
            {
                "id": msg.id,
                "user_id": msg.user_id,
                "content": msg.content,
                "is_bot": msg.is_bot_message,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
