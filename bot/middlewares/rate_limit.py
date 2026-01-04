"""Rate limiting middleware for non-admins."""

from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.config import get_settings


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting for non-admins.
    Uses in-memory storage (Redis integration to be added).
    Admins bypass rate limits.
    """

    def __init__(self):
        self._usage: dict[int, list[datetime]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Check rate limit before processing."""
        if not isinstance(event, Message):
            return await handler(event, data)
        
        message: Message = event
        settings = get_settings()
        
        if not settings.rate_limit_enabled:
            return await handler(event, data)
        
        user_id = message.from_user.id if message.from_user else 0
        
        # Admin bypass
        if user_id in settings.admin_ids:
            return await handler(event, data)
        
        # Check rate limit
        is_allowed, remaining, reset_time = self._check_limit(
            user_id,
            settings.rate_limit_prompts,
            settings.rate_limit_window_hours,
        )
        
        if not is_allowed:
            minutes_until_reset = int((reset_time - datetime.utcnow()).total_seconds() / 60)
            await message.reply(
                f"⏳ Занадто багато запитів!\n"
                f"Спробуй через {minutes_until_reset} хв."
            )
            return
        
        # Add to data for potential use in handlers
        data["rate_limit_remaining"] = remaining
        
        return await handler(event, data)

    def _check_limit(
        self,
        user_id: int,
        max_requests: int,
        window_hours: int,
    ) -> tuple[bool, int, datetime]:
        """
        Check if user is within rate limit.
        Returns: (is_allowed, remaining_requests, window_reset_time)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(hours=window_hours)
        
        # Get user's request history
        if user_id not in self._usage:
            self._usage[user_id] = []
        
        # Filter out old requests
        self._usage[user_id] = [
            ts for ts in self._usage[user_id] if ts > window_start
        ]
        
        current_count = len(self._usage[user_id])
        remaining = max_requests - current_count - 1
        
        if current_count >= max_requests:
            # Get oldest request to calculate reset time
            oldest = min(self._usage[user_id]) if self._usage[user_id] else now
            reset_time = oldest + timedelta(hours=window_hours)
            return False, 0, reset_time
        
        # Add this request
        self._usage[user_id].append(now)
        
        # Calculate approximate reset time
        reset_time = now + timedelta(hours=window_hours)
        
        return True, max(0, remaining), reset_time

    def reset_user(self, user_id: int) -> None:
        """Reset rate limit for a user."""
        if user_id in self._usage:
            del self._usage[user_id]
