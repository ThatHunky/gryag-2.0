"""Cache package for Redis."""

from bot.cache.redis import get_redis, init_redis, close_redis

__all__ = ["get_redis", "init_redis", "close_redis"]
