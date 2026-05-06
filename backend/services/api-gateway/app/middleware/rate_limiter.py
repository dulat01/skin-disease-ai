"""
Rate Limiter Middleware
"""
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware"""

    def __init__(self, app, redis_client: redis.Redis = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client identifier (IP or user ID)
        client_ip = request.client.host if request.client else "unknown"

        # Check if user is authenticated
        user_id = request.headers.get("x-user-id")
        client_key = f"rate_limit:{user_id or client_ip}"

        if self.redis_client:
            try:
                # Check rate limit
                is_allowed, remaining = await self._check_rate_limit(client_key)

                if not is_allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "success": False,
                            "error": "Rate limit exceeded",
                            "message": f"Too many requests. Try again in {self.window_seconds} seconds."
                        },
                        headers={
                            "X-RateLimit-Limit": str(self.max_requests),
                            "X-RateLimit-Remaining": "0",
                            "Retry-After": str(self.window_seconds)
                        }
                    )

                # Add rate limit headers to response
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(self.max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                return response

            except Exception as e:
                logger.error(f"Rate limiter error: {e}")
                # Allow request if rate limiter fails
                return await call_next(request)
        else:
            return await call_next(request)

    async def _check_rate_limit(self, key: str) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.
        Returns: (is_allowed, remaining_requests)
        """
        pipe = self.redis_client.pipeline()

        # Increment counter
        pipe.incr(key)
        # Set expiry only if key is new
        pipe.expire(key, self.window_seconds, nx=True)

        results = await pipe.execute()
        current_count = results[0]

        is_allowed = current_count <= self.max_requests
        remaining = max(0, self.max_requests - current_count)

        return is_allowed, remaining
