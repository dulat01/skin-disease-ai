"""
Redis client for caching and rate limiting
"""
import json
import logging
from datetime import timedelta
from typing import Any, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for caching and rate limiting"""

    def __init__(self, url: str):
        self.url = url
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis"""
        try:
            self._client = redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Redis"""
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> Redis:
        """Get the Redis client instance"""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return self._client

    # ==========================================================================
    # Basic Operations
    # ==========================================================================

    async def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set a value with optional expiration"""
        return await self.client.set(key, value, ex=expire)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        return await self.client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        return await self.client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key"""
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get TTL of a key"""
        return await self.client.ttl(key)

    # ==========================================================================
    # JSON Operations
    # ==========================================================================

    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON value by key"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set a JSON value with optional expiration"""
        return await self.set(key, json.dumps(value), expire)

    # ==========================================================================
    # Rate Limiting
    # ==========================================================================

    async def rate_limit_check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using sliding window.
        Returns: (is_allowed, current_count, remaining)
        """
        pipe = self.client.pipeline()

        # Increment counter
        pipe.incr(key)
        # Set expiry only if key is new
        pipe.expire(key, window_seconds, nx=True)
        # Get current TTL
        pipe.ttl(key)

        results = await pipe.execute()
        current_count = results[0]
        ttl = results[2]

        is_allowed = current_count <= max_requests
        remaining = max(0, max_requests - current_count)

        return is_allowed, current_count, remaining

    async def sliding_window_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        More accurate sliding window rate limit.
        Returns: (is_allowed, remaining_requests)
        """
        import time
        now = time.time()
        window_start = now - window_seconds

        pipe = self.client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiration
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        is_allowed = current_count < max_requests
        remaining = max(0, max_requests - current_count - 1)

        return is_allowed, remaining

    # ==========================================================================
    # Cache Patterns
    # ==========================================================================

    async def cache_get_or_set(
        self,
        key: str,
        factory: callable,
        expire: Optional[Union[int, timedelta]] = None
    ) -> Any:
        """Get from cache or set using factory function"""
        value = await self.get_json(key)
        if value is not None:
            return value

        # Generate value
        value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
        await self.set_json(key, value, expire)
        return value

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self.delete(*keys)
        return 0


# Import asyncio for cache_get_or_set
import asyncio

# Singleton instance factory
_clients: dict[str, RedisClient] = {}


def get_redis_client(url: str) -> RedisClient:
    """Get or create a Redis client instance"""
    if url not in _clients:
        _clients[url] = RedisClient(url)
    return _clients[url]
