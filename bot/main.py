"""Main entry point for the bot."""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.cache import close_redis, init_redis
from bot.config import get_settings
from bot.context.scheduler import start_scheduler, stop_scheduler
from bot.db import close_db, init_db
from bot.handlers import admin_router, commands_router, group_router, private_router
from bot.llm import LLMClient
from bot.middlewares import AccessControlMiddleware, LoggingMiddleware, RateLimitMiddleware
from bot.utils.logging import setup_logging

logger = logging.getLogger(__name__)

# Track startup time
_start_time: datetime | None = None


def get_uptime() -> str:
    """Get bot uptime string."""
    if not _start_time:
        return "Startup..."
    
    delta = datetime.utcnow() - _start_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, sections = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    
    return " ".join(parts)


async def startup(bot: Bot, dp: Dispatcher) -> None:
    """Startup validation and initialization."""
    global _start_time
    _start_time = datetime.utcnow()
    
    settings = get_settings()
    
    logger.info("Starting Gryag 2.0 bot...")
    
    # 1. Validate bot token
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot authenticated: @{bot_info.username}")
    except Exception as e:
        logger.critical(f"Failed to authenticate bot: {e}")
        sys.exit(1)
    
    # 2. Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # 3. Initialize Redis
    try:
        await init_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed (continuing without cache): {e}")
    
    # 4. Initialize LLM client and scheduler
    try:
        llm_client = LLMClient()
        await start_scheduler(llm_client)
        logger.info("Background scheduler started")
    except Exception as e:
        logger.warning(f"Scheduler failed to start: {e}")

    # 5. Setup commands
    try:
        from bot.utils.commands import setup_bot_commands
        await setup_bot_commands(bot)
    except Exception as e:
        logger.warning(f"Failed to setup commands: {e}")
    
    logger.info("Startup complete!")


async def shutdown(bot: Bot, dp: Dispatcher) -> None:
    """Graceful shutdown."""
    logger.info("Shutting down...")
    
    # 1. Stop scheduler
    await stop_scheduler()
    
    # 2. Close Redis
    await close_redis()
    
    # 3. Close database
    await close_db()
    
    # 4. Close bot session
    await bot.session.close()
    
    logger.info("Shutdown complete")


def create_bot() -> Bot:
    """Create and configure the bot instance."""
    settings = get_settings()
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def create_dispatcher() -> Dispatcher:
    """Create and configure the dispatcher."""
    dp = Dispatcher()
    
    # Register middlewares (order matters!)
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(AccessControlMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    
    # Register routers
    dp.include_router(commands_router)
    dp.include_router(admin_router)
    dp.include_router(private_router)
    dp.include_router(group_router)
    
    return dp


async def main() -> None:
    """Main entry point."""
    # Setup logging
    setup_logging()
    
    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher()
    
    # Register startup/shutdown hooks using proper async wrappers
    async def on_startup():
        await startup(bot, dp)
    
    async def on_shutdown():
        await shutdown(bot, dp)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Handle signals for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(dp.stop_polling()))
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    # Start polling
    logger.info("Starting polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
