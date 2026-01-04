"""Trigger detection utilities for group chats."""

from bot.config import get_settings


def check_triggers(
    text: str,
    bot_username: str | None = None,
    reply_to_bot: bool = False,
) -> bool:
    """
    Check if message triggers bot response.
    
    Triggers:
    1. Keyword match (configurable)
    2. Bot mention (@username)
    3. Reply to bot message
    """
    settings = get_settings()
    text_lower = text.lower()
    
    # Check keywords
    for keyword in settings.bot_trigger_keywords:
        if keyword.lower() in text_lower:
            return True
    
    # Check bot mention
    if bot_username and f"@{bot_username.lower()}" in text_lower:
        return True
    
    # Check reply to bot
    if reply_to_bot:
        return True
    
    return False


def extract_query(
    text: str,
    bot_username: str | None = None,
) -> str:
    """Extract the actual query from message, removing trigger keywords/mentions."""
    settings = get_settings()
    result = text
    
    # Remove bot mention
    if bot_username:
        result = result.replace(f"@{bot_username}", "").replace(f"@{bot_username.lower()}", "")
    
    # Remove trigger keywords (case-insensitive)
    for keyword in settings.bot_trigger_keywords:
        result = result.lower().replace(keyword.lower(), "")
    
    return result.strip()
