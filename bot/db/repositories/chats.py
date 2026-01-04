"""Chat repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Chat


class ChatRepository:
    """Repository for chat operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, chat_id: int) -> Chat | None:
        """Get chat by Telegram chat ID."""
        result = await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        chat_id: int,
        title: str | None = None,
        chat_type: str = "private",
        member_count: int | None = None,
    ) -> Chat:
        """Get existing chat or create new one."""
        chat = await self.get_by_id(chat_id)
        if chat is None:
            chat = Chat(
                id=chat_id,
                title=title,
                chat_type=chat_type,
                member_count=member_count,
            )
            self.session.add(chat)
            await self.session.flush()
        else:
            # Update metadata
            if title is not None:
                chat.title = title
            if member_count is not None:
                chat.member_count = member_count
        return chat

    async def update(self, chat: Chat) -> Chat:
        """Update chat."""
        self.session.add(chat)
        await self.session.flush()
        return chat

    async def get_active_chats(self) -> list[Chat]:
        """Get all active chats."""
        result = await self.session.execute(
            select(Chat).where(Chat.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())
