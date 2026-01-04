"""Message formatting utilities."""


def format_user_mention(user_id: int, full_name: str, username: str | None = None) -> str:
    """Format user mention for Telegram."""
    if username:
        return f"@{username}"
    return f"[{full_name}](tg://user?id={user_id})"


def truncate_text(text: str, max_length: int = 4096, suffix: str = "...") -> str:
    """Truncate text to fit Telegram message limit."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """Escape special Markdown characters."""
    special_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def format_context_message(
    user_name: str,
    content: str,
    is_bot: bool = False,
    timestamp: str | None = None,
) -> str:
    """Format message for context display."""
    prefix = "🤖 Bot" if is_bot else f"👤 {user_name}"
    time_str = f" [{timestamp}]" if timestamp else ""
    return f"{prefix}{time_str}: {content}"
