"""Message repository for database operations."""

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Message


class MessageRepository:
    """Repository for message operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        telegram_message_id: int,
        chat_id: int,
        user_id: int | None,
        content: str,
        content_type: str = "text",
        reply_to_message_id: int | None = None,
        is_bot_message: bool = False,
    ) -> Message:
        """Add a new message."""
        message = Message(
            telegram_message_id=telegram_message_id,
            chat_id=chat_id,
            user_id=user_id,
            content=content,
            content_type=content_type,
            reply_to_message_id=reply_to_message_id,
            is_bot_message=is_bot_message,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_recent(
        self,
        chat_id: int,
        limit: int = 100,
    ) -> list[Message]:
        """Get recent messages for a chat."""
        result = await self.session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def get_since(
        self,
        chat_id: int,
        since: datetime,
    ) -> list[Message]:
        """Get messages since a specific datetime."""
        result = await self.session.execute(
            select(Message)
            .where(Message.chat_id == chat_id, Message.created_at >= since)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_count_since(
        self,
        chat_id: int,
        since: datetime,
    ) -> int:
        """Get message count since a specific datetime."""
        result = await self.session.execute(
            select(func.count())
            .select_from(Message)
            .where(Message.chat_id == chat_id, Message.created_at >= since)
        )
        return result.scalar() or 0

    async def delete_old(
        self,
        chat_id: int,
        older_than_days: int = 60,
    ) -> int:
        """Delete messages older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        result = await self.session.execute(
            delete(Message).where(
                Message.chat_id == chat_id,
                Message.created_at < cutoff,
            )
        )
        return result.rowcount or 0

    async def find_by_telegram_id(
        self,
        chat_id: int,
        telegram_message_id: int,
    ) -> Message | None:
        """Find message by Telegram message ID."""
        result = await self.session.execute(
            select(Message).where(
                Message.chat_id == chat_id,
                Message.telegram_message_id == telegram_message_id,
            )
        )
        return result.scalar_one_or_none()
