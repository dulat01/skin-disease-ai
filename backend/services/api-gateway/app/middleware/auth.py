"""
Authentication Middleware
"""
import logging
from typing import Callable, Optional
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/doctors/register",
    "/api/v1/auth/doctors/login",
    "/api/v1/auth/subscription/request",
    "/api/v1/public",  # All public endpoints
]


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT Authentication middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth for public paths
        path = request.url.path
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("authorization")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Missing authorization header"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Invalid authorization header format"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        token = auth_header.split(" ")[1]

        # Verify token
        payload = self._verify_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Invalid or expired token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Add user info to request state
        request.state.user_id = payload.get("sub")
        request.state.email = payload.get("email")
        request.state.is_admin = payload.get("is_admin", False)

        # Continue to next middleware/handler
        response = await call_next(request)
        return response

    def _verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Check token type
            if payload.get("type") != "access":
                return None

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return None

            return payload

        except JWTError as e:
            logger.debug(f"JWT verification failed: {e}")
            return None
