"""Summary repository for database operations."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Summary


class SummaryRepository:
    """Repository for summary operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        chat_id: int,
        summary_type: str,
        content: str,
        token_count: int,
        period_start: datetime,
        period_end: datetime,
    ) -> Summary:
        """Add a new summary."""
        summary = Summary(
            chat_id=chat_id,
            summary_type=summary_type,
            content=content,
            token_count=token_count,
            period_start=period_start,
            period_end=period_end,
        )
        self.session.add(summary)
        await self.session.flush()
        return summary

    async def get_latest(
        self,
        chat_id: int,
        summary_type: str,
    ) -> Summary | None:
        """Get the latest summary of a specific type for a chat."""
        result = await self.session.execute(
            select(Summary)
            .where(
                Summary.chat_id == chat_id,
                Summary.summary_type == summary_type,
            )
            .order_by(Summary.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all_for_chat(
        self,
        chat_id: int,
    ) -> list[Summary]:
        """Get all summaries for a chat."""
        result = await self.session.execute(
            select(Summary)
            .where(Summary.chat_id == chat_id)
            .order_by(Summary.created_at.desc())
        )
        return list(result.scalars().all())
