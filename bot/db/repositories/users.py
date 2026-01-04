"""User repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User


class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by Telegram user ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: int,
        username: str | None = None,
        full_name: str = "Unknown",
    ) -> User:
        """Get existing user or create new one."""
        user = await self.get_by_id(user_id)
        if user is None:
            user = User(
                id=user_id,
                username=username,
                full_name=full_name,
            )
            self.session.add(user)
            await self.session.flush()
        else:
            # Update metadata
            if username is not None:
                user.username = username
            if full_name != "Unknown":
                user.full_name = full_name
        return user

    async def update_pronouns(self, user_id: int, pronouns: str) -> User | None:
        """Update user pronouns."""
        user = await self.get_by_id(user_id)
        if user:
            user.pronouns = pronouns
            await self.session.flush()
        return user

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
