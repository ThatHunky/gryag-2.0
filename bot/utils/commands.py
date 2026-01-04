"""Command setup utilities."""

import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from bot.config import get_settings

logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot) -> None:
    """Setup bot commands for different scopes."""
    settings = get_settings()
    
    # 1. Default commands (for everyone)
    default_commands = [
        BotCommand(command="memories", description="Show what I remember about you"),
        BotCommand(command="start", description="Start interaction"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="stats", description="Show statistics"),
    ]
    
    try:
        await bot.set_my_commands(
            commands=default_commands,
            scope=BotCommandScopeDefault()
        )
        logger.info("Set default commands")
    except Exception as e:
        logger.error(f"Failed to set default commands: {e}")

    # 2. Admin commands (for admin IDs only)
    admin_commands = default_commands + [
        BotCommand(command="status", description="[Admin] System status"),
        BotCommand(command="config", description="[Admin] View configuration"),
        BotCommand(command="reload_prompt", description="[Admin] Reload system prompt"),
        BotCommand(command="ban", description="[Admin] Ban user"),
        BotCommand(command="unban", description="[Admin] Unban user"),
        BotCommand(command="restrict", description="[Admin] Restrict user"),
        BotCommand(command="whitelist", description="[Admin] Manage whitelist"),
        BotCommand(command="blacklist", description="[Admin] Manage blacklist"),
    ]
    
    for admin_id in settings.admin_ids:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
            logger.info(f"Set admin commands for user {admin_id}")
        except Exception as e:
            logger.warning(f"Failed to set commands for admin {admin_id}: {e}")
