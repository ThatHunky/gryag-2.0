"""Redis client and utilities."""

import json
from typing import Any

import redis.asyncio as redis

from bot.config import get_settings

_redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    """Initialize Redis connection."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def get_redis() -> redis.Redis:
    """Get Redis client (initializes if needed)."""
    if _redis_client is None:
        return await init_redis()
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class RedisCache:
    """Utility class for common cache operations."""

    def __init__(self, prefix: str = "gryag"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        """Generate prefixed key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        client = await get_redis()
        return await client.get(self._key(key))

    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: int | None = None,
    ) -> None:
        """Set value with optional expiration."""
        client = await get_redis()
        await client.set(self._key(key), value, ex=expire_seconds)

    async def delete(self, key: str) -> None:
        """Delete key."""
        client = await get_redis()
        await client.delete(self._key(key))

    async def get_json(self, key: str) -> Any | None:
        """Get and parse JSON value."""
        value = await self.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(
        self,
        key: str,
        value: Any,
        expire_seconds: int | None = None,
    ) -> None:
        """Set JSON value."""
        await self.set(key, json.dumps(value), expire_seconds)

    async def incr(self, key: str) -> int:
        """Increment counter."""
        client = await get_redis()
        return await client.incr(self._key(key))

    async def expire(self, key: str, seconds: int) -> None:
        """Set expiration on key."""
        client = await get_redis()
        await client.expire(self._key(key), seconds)
