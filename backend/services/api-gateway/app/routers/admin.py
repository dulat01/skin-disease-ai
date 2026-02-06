"""
Admin Router - Proxy to Admin Service
"""
import logging

from fastapi import APIRouter, Request, Response, HTTPException
import httpx

from app.config import settings
from app.utils.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
circuit_breaker = get_circuit_breaker("admin-service")


async def proxy_request(
    request: Request,
    path: str,
    method: str = "GET"
) -> Response:
    """Proxy request to admin service"""
    # Check if user is admin
    if not hasattr(request.state, "is_admin") or not request.state.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    if not circuit_breaker.can_execute():
        raise HTTPException(
            status_code=503,
            detail="Admin service temporarily unavailable"
        )

    url = f"{settings.ADMIN_SERVICE_URL}{path}"

    try:
        body = await request.body() if method in ["POST", "PUT", "PATCH"] else None

        headers = dict(request.headers)
        headers.pop("host", None)

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
        logger.error(f"Admin service request failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Admin service unavailable"
        )


@router.get("/dashboard")
async def get_dashboard(request: Request):
    """Get admin dashboard overview"""
    return await proxy_request(request, "/api/v1/admin/dashboard", "GET")


@router.get("/statistics/daily")
async def get_daily_statistics(request: Request):
    """Get daily statistics"""
    return await proxy_request(request, "/api/v1/admin/statistics/daily", "GET")


@router.get("/users")
async def list_users(request: Request):
    """List all users"""
    return await proxy_request(request, "/api/v1/admin/users", "GET")


@router.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user details"""
    return await proxy_request(request, f"/api/v1/admin/users/{user_id}", "GET")


@router.get("/model/metrics")
async def get_model_metrics(request: Request):
    """Get model performance metrics"""
    return await proxy_request(request, "/api/v1/admin/model/metrics", "GET")


@router.get("/notifications")
async def get_notifications(request: Request):
    """Get admin notifications"""
    return await proxy_request(request, "/api/v1/admin/notifications", "GET")
