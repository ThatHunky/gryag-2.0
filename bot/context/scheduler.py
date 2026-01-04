"""Background scheduler for context summarization."""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import get_settings
from bot.db.session import get_session
from bot.db.repositories import ChatRepository

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def start_scheduler(llm_client) -> None:
    """Start the background scheduler with summarization jobs."""
    settings = get_settings()
    scheduler = get_scheduler()
    
    # 7-day summary job (runs every N days at 3 AM)
    scheduler.add_job(
        _run_7day_summaries,
        CronTrigger(
            day=f"*/{settings.recent_summary_interval_days}",
            hour=3,
            minute=0,
        ),
        args=[llm_client],
        id="7day_summaries",
        replace_existing=True,
    )
    
    # 30-day summary job (runs every N days at 4 AM)
    scheduler.add_job(
        _run_30day_summaries,
        CronTrigger(
            day=f"*/{settings.long_summary_interval_days}",
            hour=4,
            minute=0,
        ),
        args=[llm_client],
        id="30day_summaries",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Background scheduler started")


async def stop_scheduler() -> None:
    """Stop the scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped")


async def _run_7day_summaries(llm_client) -> None:
    """Run 7-day summarization for all active chats."""
    from bot.context.summarizer import generate_summary
    
    logger.info("Starting 7-day summarization job")
    
    async with get_session() as session:
        chat_repo = ChatRepository(session)
        chats = await chat_repo.get_active_chats()
    
    for chat in chats:
        try:
            await generate_summary(chat.id, "7day", llm_client)
            logger.debug(f"Generated 7-day summary for chat {chat.id}")
        except Exception as e:
            logger.error(f"Failed to generate 7-day summary for chat {chat.id}: {e}")
    
    logger.info(f"Completed 7-day summarization for {len(chats)} chats")


async def _run_30day_summaries(llm_client) -> None:
    """Run 30-day summarization for all active chats."""
    from bot.context.summarizer import generate_summary
    
    logger.info("Starting 30-day summarization job")
    
    async with get_session() as session:
        chat_repo = ChatRepository(session)
        chats = await chat_repo.get_active_chats()
    
    for chat in chats:
        try:
            await generate_summary(chat.id, "30day", llm_client)
            logger.debug(f"Generated 30-day summary for chat {chat.id}")
        except Exception as e:
            logger.error(f"Failed to generate 30-day summary for chat {chat.id}: {e}")
    
    logger.info(f"Completed 30-day summarization for {len(chats)} chats")
