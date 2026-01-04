"""Error handling utilities with user-friendly messages."""

from typing import Literal

ErrorType = Literal[
    "llm_timeout",
    "llm_rate_limit",
    "user_rate_limit",
    "tool_error",
    "network_error",
    "model_unavailable",
    "unknown",
]

ERROR_MESSAGES: dict[ErrorType, str] = {
    "llm_timeout": "Я занадто довго думаю... Спробуй ще раз? 🤔",
    "llm_rate_limit": "API зайнятий. Зачекай хвильку. ⏳",
    "user_rate_limit": "Занадто багато запитів! Ти можеш надіслати ще {remaining} через {time}.",
    "tool_error": "Щось пішло не так з цією дією. 🔧",
    "network_error": "Проблема з підключенням. Пробую ще раз... 🔄",
    "model_unavailable": "Переключаюсь на запасну модель... 🔄",
    "unknown": "Упс, щось пішло не так. Спробуй ще раз. 😅",
}


class BotError(Exception):
    """Base exception for bot errors."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = "unknown",
        details: dict | None = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}

    def user_message(self) -> str:
        """Get user-friendly error message."""
        return format_error_message(self.error_type, **self.details)


class LLMError(BotError):
    """LLM-related error."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = "llm_timeout",
        details: dict | None = None,
    ):
        super().__init__(message, error_type, details)


class RateLimitError(BotError):
    """Rate limit error."""
    
    def __init__(
        self,
        message: str,
        remaining: int = 0,
        reset_minutes: int = 0,
    ):
        super().__init__(
            message,
            error_type="user_rate_limit",
            details={"remaining": remaining, "time": f"{reset_minutes} хв"},
        )


def format_error_message(error_type: ErrorType, **kwargs) -> str:
    """Format user-friendly error message."""
    template = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["unknown"])
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
