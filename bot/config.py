"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_comma_list(value: str | None) -> list[str]:
    """Parse comma-separated string into list."""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_comma_int_list(value: str | None) -> list[int]:
    """Parse comma-separated string into list of ints."""
    if not value or not value.strip():
        return []
    result = []
    for item in value.split(","):
        item = item.strip()
        if item:
            try:
                result.append(int(item))
            except ValueError:
                pass
    return result


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str = Field(..., description="Telegram bot token from @BotFather")
    bot_trigger_keywords_raw: str = Field(
        default="gryag,Гряг,griag",
        alias="BOT_TRIGGER_KEYWORDS",
        description="Keywords that trigger the bot in group chats",
    )

    # Admin
    admin_ids_raw: str = Field(
        default="",
        alias="ADMIN_IDS",
        description="Telegram user IDs with admin privileges",
    )

    # LLM Configuration
    llm_api_key: str = Field(..., description="API key for LLM provider")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for OpenAI-compatible API",
    )
    llm_model: str = Field(default="gpt-4o", description="Primary LLM model")
    llm_vision_model: str | None = Field(
        default=None,
        description="Vision model (falls back to primary if not set)",
    )
    llm_vision_base_url: str | None = Field(
        default=None,
        description="Base URL for vision API (falls back to llm_base_url if not set)",
    )
    llm_vision_api_key: str | None = Field(
        default=None,
        description="API key for vision API (falls back to llm_api_key if not set)",
    )
    llm_vision_enabled: bool = Field(
        default=True,
        description="Enable vision capabilities for image understanding",
    )
    llm_summarization_model: str = Field(
        default="gpt-4o-mini",
        description="Model for context summarization",
    )

    # Reasoning Mode
    llm_reasoning_enabled: bool = Field(default=True, description="Enable extended thinking")
    llm_reasoning_effort: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Reasoning effort level",
    )

    # Structured Output
    llm_structured_output: bool = Field(
        default=True,
        description="Use JSON schema for responses",
    )
    llm_structured_input: bool = Field(
        default=False,
        description="Use structured input format",
    )

    # Context Settings
    immediate_context_messages: int = Field(default=100, ge=10, le=500)
    recent_summary_tokens: int = Field(default=1024, ge=256, le=4096)
    recent_summary_interval_days: int = Field(default=3, ge=1, le=7)
    long_summary_tokens: int = Field(default=4096, ge=1024, le=16384)
    long_summary_interval_days: int = Field(default=14, ge=7, le=30)

    # User Memory
    user_memory_max_facts: int = Field(default=50, ge=10, le=100)

    # System Prompt
    system_prompt_file: str = Field(default="default.md")

    # Access Control
    access_mode: Literal["global", "private", "whitelist"] = Field(default="global")
    whitelist_chats_raw: str = Field(default="", alias="WHITELIST_CHATS")
    blacklist_users_raw: str = Field(default="", alias="BLACKLIST_USERS")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_prompts: int = Field(default=30, ge=1, le=1000)
    rate_limit_window_hours: int = Field(default=1, ge=1, le=24)

    # Moderation
    moderation_enabled: bool = Field(default=False)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://bot:bot@postgres:5432/gryag",
    )
    redis_url: str = Field(default="redis://redis:6379/0")

    # Image Generation
    image_generation_enabled: bool = Field(default=True)
    image_generation_model: str = Field(default="dall-e-3")
    image_generation_base_url: str | None = Field(default=None)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_format: Literal["json", "text"] = Field(default="json")
    log_file_enabled: bool = Field(default=True)
    log_file_path: str = Field(default="./data/logs")
    log_file_retention_days: int = Field(default=7, ge=1, le=30)

    # Response Limits
    llm_max_response_tokens: int = Field(default=2048, ge=256, le=16384)
    context_max_tokens: int = Field(default=8000, ge=2000, le=128000)

    # Reliability
    llm_fallback_model: str | None = Field(default=None)
    llm_timeout_seconds: int = Field(default=60, ge=10, le=300)
    llm_max_retries: int = Field(default=3, ge=0, le=10)

    # UX Features
    typing_indicator_enabled: bool = Field(default=True)

    # Properties to parse comma-separated values
    @property
    def bot_trigger_keywords(self) -> list[str]:
        """Get trigger keywords as list."""
        return parse_comma_list(self.bot_trigger_keywords_raw)

    @property
    def admin_ids(self) -> list[int]:
        """Get admin IDs as list."""
        return parse_comma_int_list(self.admin_ids_raw)

    @property
    def whitelist_chats(self) -> list[int]:
        """Get whitelisted chat IDs as list."""
        return parse_comma_int_list(self.whitelist_chats_raw)

    @property
    def blacklist_users(self) -> list[int]:
        """Get blacklisted user IDs as list."""
        return parse_comma_int_list(self.blacklist_users_raw)

    @property
    def effective_vision_model(self) -> str:
        """Get vision model, falling back to primary model."""
        return self.llm_vision_model or self.llm_model

    @property
    def effective_image_base_url(self) -> str:
        """Get image generation base URL, falling back to LLM base URL."""
        return self.image_generation_base_url or self.llm_base_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

