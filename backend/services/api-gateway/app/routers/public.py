"""
Public Router - proxy public endpoints (no authentication required)
"""
import logging
from fastapi import APIRouter, Request, Response, HTTPException
import httpx

from app.config import settings
from app.utils.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/public", tags=["Public"])

client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
circuit_breaker = get_circuit_breaker("auth-service")


async def proxy_request(request: Request, path: str, method: str = "GET") -> Response:
    """Proxy request to auth service (public, no auth required)"""
    if not circuit_breaker.can_execute():
        raise HTTPException(status_code=503, detail="Auth service temporarily unavailable")

    url = f"{settings.AUTH_SERVICE_URL}{path}"

    try:
        body = await request.body() if method in ["POST", "PUT", "PATCH"] else None
        headers = dict(request.headers)
        headers.pop("host", None)

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
        raise HTTPException(status_code=503, detail="Auth service unavailable")


@router.get("/subscription/plans")
async def get_subscription_plans(request: Request):
    """Proxy get subscription plans to auth service"""
    return await proxy_request(request, "/api/v1/public/subscription/plans", "GET")


@router.post("/subscription/request")
async def request_subscription(request: Request):
    """Proxy subscription request to auth service"""
    return await proxy_request(request, "/api/v1/public/subscription/request", "POST")
