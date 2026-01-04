"""Access control middleware with multi-layer checks."""

from datetime import datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.config import get_settings
from bot.db.models import UserRestriction
from bot.db.session import get_session
from sqlalchemy import select


class AccessControlMiddleware(BaseMiddleware):
    """
    Multi-layer access control:
    1. Admin bypass - admins skip all checks
    2. Ban/restriction check - permanent or temporary
    3. Blacklist check
    4. Access mode check (global/private/whitelist)
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process message through access control layers."""
        if not isinstance(event, Message):
            return await handler(event, data)
        
        message: Message = event
        settings = get_settings()
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        
        from sqlalchemy import func
        
        # Layer 1: Admin bypass
        if user_id in settings.admin_ids:
            return await handler(event, data)
        
        # Layer 2: Check bot-level bans/restrictions
        is_restricted = await self._check_restriction(user_id)
        if is_restricted:
            # Silently ignore banned users
            return
        
        # Layer 3: Blacklist check (Env + DB)
        if user_id in settings.blacklist_users:
            return
        
        if await self._check_blacklist(user_id):
            return
        
        # Layer 4: Access mode check
        if not await self._check_access_mode(settings, message):
            return
        
        return await handler(event, data)

    async def _check_restriction(self, user_id: int) -> bool:
        """Check if user is banned or restricted."""
        async with get_session() as session:
            result = await session.execute(
                select(UserRestriction).where(
                    UserRestriction.user_id == user_id,
                    UserRestriction.is_active == True,  # noqa: E712
                )
            )
            restriction = result.scalar_one_or_none()
            
            if restriction is None:
                return False
            
            # Check if temporary restriction has expired
            if restriction.expires_at and restriction.expires_at < datetime.utcnow():
                restriction.is_active = False
                await session.flush()
                return False
            
            return True

    async def _check_blacklist(self, user_id: int) -> bool:
        """Check if user is blacklisted in DB."""
        from bot.db.models import AccessList
        
        async with get_session() as session:
            count = await session.scalar(
                select(func.count(AccessList.id)).where(
                    AccessList.entity_id == user_id,
                    AccessList.entity_type == "user",
                    AccessList.list_type == "blacklist"
                )
            )
            return count > 0

    async def _check_access_mode(self, settings, message: Message) -> bool:
        """Check if message passes access mode filter."""
        mode = settings.access_mode
        chat_type = message.chat.type
        chat_id = message.chat.id
        
        if mode == "global":
            return True
        
        if mode == "private":
            return chat_type == "private"
        
        if mode == "whitelist":
            # Check env var first
            if chat_id in settings.whitelist_chats:
                return True
            
            # Check DB
            from bot.db.models import AccessList
            async with get_session() as session:
                count = await session.scalar(
                    select(func.count(AccessList.id)).where(
                        AccessList.entity_id == chat_id,
                        AccessList.entity_type == "chat",
                        AccessList.list_type == "whitelist"
                    )
                )
                if count > 0:
                    return True
            
            return chat_type == "private"
        
        return True
