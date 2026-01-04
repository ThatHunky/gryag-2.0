"""Logging middleware for message tracking."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Log all incoming messages for debugging."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Log message details before processing."""
        if isinstance(event, Message):
            message: Message = event
            user = message.from_user
            chat = message.chat
            
            user_info = f"{user.full_name} (@{user.username})" if user else "Unknown"
            chat_info = f"{chat.title or chat.full_name} ({chat.type})"
            content = message.text[:50] if message.text else f"[{message.content_type}]"
            
            logger.info(
                f"Incoming: {user_info} in {chat_info}: {content}"
            )
        
        return await handler(event, data)

