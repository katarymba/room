"""Optional Redis client for production-grade rate limiting and caching.

Falls back gracefully when Redis is unavailable (e.g., during development or
when ``REDIS_URL`` is not set).  All public helpers return ``None`` / default
values in that case so callers do not need to handle the absence of Redis.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Lazily imported so the app still starts without redis installed
_redis_module = None
_client = None


def _get_redis():
    """Return a connected async Redis client, or *None* if unavailable."""
    global _redis_module, _client
    if _client is not None:
        return _client

    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return None

    try:
        import redis.asyncio as aioredis  # type: ignore

        _redis_module = aioredis
        _client = aioredis.from_url(redis_url, decode_responses=True)
        logger.info("Redis client initialised: %s", redis_url)
        return _client
    except ImportError:
        logger.warning("redis package not installed; rate limiting uses in-memory store")
        return None
    except Exception as exc:
        logger.warning("Failed to connect to Redis (%s); falling back to in-memory store", exc)
        return None


class RedisClient:
    """Thin wrapper around the async Redis client with a graceful fallback."""

    # ── Key/value helpers ─────────────────────────────────────────────────────

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> bool:
        """Set *key* = *value* with a TTL in seconds.  Returns ``True`` on success."""
        client = _get_redis()
        if client is None:
            return False
        try:
            await client.set(key, value, ex=ttl)
            return True
        except Exception as exc:
            logger.warning("Redis set_with_ttl error: %s", exc)
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get the value for *key*, or ``None`` if missing / Redis unavailable."""
        client = _get_redis()
        if client is None:
            return None
        try:
            return await client.get(key)
        except Exception as exc:
            logger.warning("Redis get error: %s", exc)
            return None

    async def increment(self, key: str, ttl: Optional[int] = None) -> Optional[int]:
        """Atomically increment *key* and optionally set *ttl* on first creation."""
        client = _get_redis()
        if client is None:
            return None
        try:
            pipe = client.pipeline()
            pipe.incr(key)
            if ttl is not None:
                pipe.expire(key, ttl, nx=True)
            results = await pipe.execute()
            return results[0]
        except Exception as exc:
            logger.warning("Redis increment error: %s", exc)
            return None

    async def get_ttl(self, key: str) -> int:
        """Return remaining TTL in seconds for *key* (``-1`` if no TTL, ``-2`` if missing)."""
        client = _get_redis()
        if client is None:
            return -2
        try:
            return await client.ttl(key)
        except Exception as exc:
            logger.warning("Redis get_ttl error: %s", exc)
            return -2

    async def delete(self, key: str) -> bool:
        """Delete *key*.  Returns ``True`` if the key existed."""
        client = _get_redis()
        if client is None:
            return False
        try:
            return bool(await client.delete(key))
        except Exception as exc:
            logger.warning("Redis delete error: %s", exc)
            return False

    @property
    def available(self) -> bool:
        """``True`` when Redis is configured and reachable."""
        return _get_redis() is not None


# Singleton instance used throughout the app
redis_client = RedisClient()
