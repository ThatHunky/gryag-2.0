"""Memory repository for user memories."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UserMemory


class MemoryRepository:
    """Repository for user memory operations (global, max 50 per user)."""

    def __init__(self, session: AsyncSession, max_memories: int = 50):
        self.session = session
        self.max_memories = max_memories

    async def add_memory(self, user_id: int, fact: str) -> UserMemory:
        """Add a memory for a user, enforcing FIFO limit."""
        # Check current count
        count = await self.count_memories(user_id)
        
        # Delete oldest if at limit
        if count >= self.max_memories:
            await self._delete_oldest(user_id, count - self.max_memories + 1)
        
        # Add new memory
        memory = UserMemory(user_id=user_id, fact=fact)
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def get_memories(self, user_id: int) -> list[UserMemory]:
        """Get all memories for a user."""
        result = await self.session.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user_id)
            .order_by(UserMemory.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a specific memory by ID."""
        result = await self.session.execute(
            delete(UserMemory).where(UserMemory.id == memory_id)
        )
        return (result.rowcount or 0) > 0

    async def delete_all_for_user(self, user_id: int) -> int:
        """Delete all memories for a user."""
        result = await self.session.execute(
            delete(UserMemory).where(UserMemory.user_id == user_id)
        )
        return result.rowcount or 0

    async def count_memories(self, user_id: int) -> int:
        """Count memories for a user."""
        result = await self.session.execute(
            select(func.count())
            .select_from(UserMemory)
            .where(UserMemory.user_id == user_id)
        )
        return result.scalar() or 0

    async def _delete_oldest(self, user_id: int, count: int) -> None:
        """Delete the oldest N memories for a user."""
        # Get oldest memory IDs
        result = await self.session.execute(
            select(UserMemory.id)
            .where(UserMemory.user_id == user_id)
            .order_by(UserMemory.created_at.asc())
            .limit(count)
        )
        ids_to_delete = [row[0] for row in result.all()]
        
        if ids_to_delete:
            await self.session.execute(
                delete(UserMemory).where(UserMemory.id.in_(ids_to_delete))
            )

    async def find_duplicate(self, user_id: int, fact: str) -> UserMemory | None:
        """Check if a similar fact already exists."""
        result = await self.session.execute(
            select(UserMemory).where(
                UserMemory.user_id == user_id,
                UserMemory.fact == fact,
            )
        )
        return result.scalar_one_or_none()
