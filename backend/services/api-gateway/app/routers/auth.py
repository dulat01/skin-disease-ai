"""
Auth Router - Proxy to Auth Service
"""
import logging
from typing import Optional

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import httpx

from app.config import settings
from app.utils.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# HTTP client for proxying requests
client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
circuit_breaker = get_circuit_breaker("auth-service")


async def proxy_request(
    request: Request,
    path: str,
    method: str = "GET"
) -> Response:
    """Proxy request to auth service"""
    if not circuit_breaker.can_execute():
        raise HTTPException(
            status_code=503,
            detail="Auth service temporarily unavailable"
        )

    url = f"{settings.AUTH_SERVICE_URL}{path}"

    try:
        # Get request body if present
        body = await request.body() if method in ["POST", "PUT", "PATCH"] else None

        # Forward headers (except host)
        headers = dict(request.headers)
        headers.pop("host", None)

        # Add user info if authenticated
        if hasattr(request.state, "user_id"):
            headers["x-user-id"] = request.state.user_id
            headers["x-user-email"] = request.state.email
            headers["x-user-is-admin"] = str(request.state.is_admin)

        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            content=body,
            params=dict(request.query_params)
        )

        circuit_breaker.record_success()

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )

    except httpx.RequestError as e:
        circuit_breaker.record_failure()
        logger.error(f"Auth service request failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Auth service unavailable"
        )


@router.post("/register")
async def register(request: Request):
    """Proxy registration to auth service"""
    return await proxy_request(request, "/api/v1/auth/register", "POST")


@router.post("/login")
async def login(request: Request):
    """Proxy login to auth service"""
    return await proxy_request(request, "/api/v1/auth/login", "POST")


@router.post("/logout")
async def logout(request: Request):
    """Proxy logout to auth service"""
    return await proxy_request(request, "/api/v1/auth/logout", "POST")


@router.post("/refresh")
async def refresh(request: Request):
    """Proxy token refresh to auth service"""
    return await proxy_request(request, "/api/v1/auth/refresh", "POST")


@router.get("/me")
async def get_current_user(request: Request):
    """Proxy get current user to auth service"""
    return await proxy_request(request, "/api/v1/auth/me", "GET")


@router.put("/me")
async def update_current_user(request: Request):
    """Proxy update user to auth service"""
    return await proxy_request(request, "/api/v1/auth/me", "PUT")


@router.post("/me/change-password")
async def change_password(request: Request):
    """Proxy password change to auth service"""
    return await proxy_request(request, "/api/v1/auth/me/change-password", "POST")


@router.post("/verify")
async def verify_token(request: Request):
    """Proxy token verification to auth service"""
    return await proxy_request(request, "/api/v1/auth/verify", "POST")
