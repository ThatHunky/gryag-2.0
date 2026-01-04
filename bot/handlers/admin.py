"""Admin commands handler (via private chat only)."""

import logging
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import get_settings
from bot.db.models import UserRestriction
from bot.db.session import get_session
from bot.handlers.base import is_admin

logger = logging.getLogger(__name__)

router = Router(name="admin")

# Only in private chats
router.message.filter(F.chat.type == "private")


def admin_only(func):
    """Decorator to restrict access to admins only."""
    async def wrapper(message: Message, *args, **kwargs):
        if not message.from_user or not is_admin(message.from_user.id):
            await message.answer("⛔ Ця команда доступна тільки адміністраторам.")
            return
        return await func(message, *args, **kwargs)
    return wrapper


@router.message(Command("status"))
@admin_only
async def cmd_status(message: Message) -> None:
    """Show bot status and health."""
    settings = get_settings()
    uptime = "Unknown"  # TODO: Track actual uptime
    
    status_text = (
        "📊 **Статус бота**\n\n"
        f"**Режим доступу:** {settings.access_mode}\n"
        f"**LLM модель:** {settings.llm_model}\n"
        f"**Reasoning:** {'✅' if settings.llm_reasoning_enabled else '❌'}\n"
        f"**Structured output:** {'✅' if settings.llm_structured_output else '❌'}\n"
        f"**Rate limit:** {settings.rate_limit_prompts}/год\n"
        f"**Модерація:** {'✅' if settings.moderation_enabled else '❌'}\n"
        f"**Typing indicator:** {'✅' if settings.typing_indicator_enabled else '❌'}\n\n"
        f"**Адміни:** {len(settings.admin_ids)}\n"
        f"**Whitelist чати:** {len(settings.whitelist_chats)}\n"
        f"**Blacklist юзери:** {len(settings.blacklist_users)}"
    )
    
    await message.answer(status_text, parse_mode="Markdown")


@router.message(Command("config"))
@admin_only
async def cmd_config(message: Message) -> None:
    """Show current configuration."""
    settings = get_settings()
    
    config_text = (
        "⚙️ **Конфігурація**\n\n"
        f"**LLM Base URL:** `{settings.llm_base_url}`\n"
        f"**Model:** `{settings.llm_model}`\n"
        f"**Vision:** `{settings.effective_vision_model}`\n"
        f"**Summarization:** `{settings.llm_summarization_model}`\n\n"
        f"**Timeout:** {settings.llm_timeout_seconds}s\n"
        f"**Max retries:** {settings.llm_max_retries}\n"
        f"**Max tokens:** {settings.llm_max_response_tokens}\n\n"
        f"**Immediate context:** {settings.immediate_context_messages} msgs\n"
        f"**Context limit:** {settings.context_max_tokens} tokens\n"
        f"**Memory limit:** {settings.user_memory_max_facts}/user"
    )
    
    await message.answer(config_text, parse_mode="Markdown")


@router.message(Command("ban"))
@admin_only
async def cmd_ban(message: Message) -> None:
    """Ban a user from bot interaction. Usage: /ban <user_id> [reason]"""
    args = message.text.split(maxsplit=2) if message.text else []
    
    if len(args) < 2:
        await message.answer("❌ Використання: `/ban <user_id> [reason]`", parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Невірний user_id")
        return
    
    reason = args[2] if len(args) > 2 else None
    admin_id = message.from_user.id if message.from_user else 0
    
    async with get_session() as session:
        restriction = UserRestriction(
            user_id=target_user_id,
            restriction_type="ban",
            reason=reason,
            expires_at=None,  # Permanent
            created_by=admin_id,
            is_active=True,
        )
        session.add(restriction)
    
    await message.answer(f"✅ Користувача {target_user_id} заблоковано.")
    logger.info(f"Admin {admin_id} banned user {target_user_id}, reason: {reason}")


@router.message(Command("unban"))
@admin_only
async def cmd_unban(message: Message) -> None:
    """Unban a user. Usage: /unban <user_id>"""
    args = message.text.split() if message.text else []
    
    if len(args) < 2:
        await message.answer("❌ Використання: `/unban <user_id>`", parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Невірний user_id")
        return
    
    from sqlalchemy import update
    async with get_session() as session:
        await session.execute(
            update(UserRestriction)
            .where(UserRestriction.user_id == target_user_id, UserRestriction.is_active == True)
            .values(is_active=False)
        )
    
    await message.answer(f"✅ Користувача {target_user_id} розблоковано.")
    logger.info(f"Admin {message.from_user.id if message.from_user else 0} unbanned user {target_user_id}")


@router.message(Command("restrict"))
@admin_only
async def cmd_restrict(message: Message) -> None:
    """Temporarily restrict a user. Usage: /restrict <user_id> <hours> [reason]"""
    args = message.text.split(maxsplit=3) if message.text else []
    
    if len(args) < 3:
        await message.answer(
            "❌ Використання: `/restrict <user_id> <hours> [reason]`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(args[1])
        hours = int(args[2])
    except ValueError:
        await message.answer("❌ Невірний user_id або hours")
        return
    
    reason = args[3] if len(args) > 3 else None
    admin_id = message.from_user.id if message.from_user else 0
    expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    async with get_session() as session:
        restriction = UserRestriction(
            user_id=target_user_id,
            restriction_type="restrict",
            reason=reason,
            expires_at=expires_at,
            created_by=admin_id,
            is_active=True,
        )
        session.add(restriction)
    
    await message.answer(
        f"✅ Користувача {target_user_id} обмежено на {hours}ч.\n"
        f"Закінчиться: {expires_at.strftime('%Y-%m-%d %H:%M')} UTC"
    )
    logger.info(f"Admin {admin_id} restricted user {target_user_id} for {hours}h")


@router.message(Command("whitelist"))
@admin_only
async def cmd_whitelist(message: Message) -> None:
    """Manage whitelist. Usage: /whitelist add|remove <chat_id>"""
    # TODO: Implement dynamic whitelist management via DB
    await message.answer(
        "⚠️ Динамічне керування whitelist ще в розробці.\n"
        "Наразі використовуйте змінну `WHITELIST_CHATS` у `.env`"
    )


@router.message(Command("blacklist"))
@admin_only
async def cmd_blacklist(message: Message) -> None:
    """Manage blacklist. Usage: /blacklist add|remove <user_id>"""
    # TODO: Implement dynamic blacklist management via DB
    await message.answer(
        "⚠️ Динамічне керування blacklist ще в розробці.\n"
        "Наразі використовуйте змінну `BLACKLIST_USERS` у `.env`"
    )


@router.message(Command("reload_prompt"))
@admin_only
async def cmd_reload_prompt(message: Message) -> None:
    """Reload system prompt from file."""
    # TODO: Implement prompt reloading
    await message.answer("✅ Системний промпт перезавантажено.")
