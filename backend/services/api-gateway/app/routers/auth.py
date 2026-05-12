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


@router.get("/profile")
async def get_patient_profile(request: Request):
    """Proxy get patient profile to auth service"""
    return await proxy_request(request, "/api/v1/auth/profile", "GET")


@router.put("/profile")
async def update_patient_profile(request: Request):
    """Proxy update patient profile to auth service"""
    return await proxy_request(request, "/api/v1/auth/profile", "PUT")


@router.post("/doctors/register")
async def register_doctor(request: Request):
    """Proxy doctor registration to auth service"""
    return await proxy_request(request, "/api/v1/doctors/register", "POST")


@router.post("/doctors/login")
async def login_doctor(request: Request):
    """Proxy doctor login to auth service"""
    return await proxy_request(request, "/api/v1/doctors/login", "POST")


@router.get("/doctors/plans")
async def get_subscription_plans(request: Request):
    """Proxy get subscription plans to auth service"""
    return await proxy_request(request, "/api/v1/doctors/plans", "GET")


@router.post("/subscription/request")
async def request_subscription(request: Request):
    """Proxy subscription request to auth service"""
    return await proxy_request(request, "/api/v1/public/subscription/request", "POST")


@router.get("/subscription/status")
async def get_subscription_status(request: Request):
    """Proxy get subscription status to auth service"""
    return await proxy_request(request, "/api/v1/doctors/subscription/status", "GET")


@router.get("/admin/doctors")
async def list_doctors(request: Request):
    """Proxy list doctors to auth service"""
    return await proxy_request(request, f"/api/v1/admin/doctors?verified_only={request.query_params.get('verified_only', False)}", "GET")


@router.post("/admin/doctors/{doctor_id}/verify")
async def verify_doctor(request: Request, doctor_id: str):
    """Proxy verify doctor to auth service"""
    return await proxy_request(request, f"/api/v1/admin/doctors/{doctor_id}/verify", "POST")


@router.get("/admin/subscription-requests")
async def list_subscription_requests(request: Request):
    """Proxy list subscription requests to auth service"""
    return await proxy_request(request, f"/api/v1/admin/subscription-requests?status={request.query_params.get('status', 'pending')}", "GET")


@router.post("/admin/subscription-requests/{request_id}/approve")
async def approve_subscription_request(request: Request, request_id: str):
    """Proxy approve subscription request to auth service"""
    return await proxy_request(request, f"/api/v1/admin/subscription-requests/{request_id}/approve", "POST")


@router.post("/admin/subscription-requests/{request_id}/decline")
async def decline_subscription_request(request: Request, request_id: str):
    """Proxy decline subscription request to auth service"""
    return await proxy_request(request, f"/api/v1/admin/subscription-requests/{request_id}/decline", "POST")
