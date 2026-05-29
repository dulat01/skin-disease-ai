"""
Predictions Router - Proxy to Prediction Service
"""
import logging

from fastapi import APIRouter, Request, Response, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import httpx

from app.config import settings
from app.utils.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])

# HTTP client with longer timeout for ML inference
client = httpx.AsyncClient(timeout=60.0)
circuit_breaker = get_circuit_breaker("prediction-service")


async def proxy_request(
    request: Request,
    path: str,
    method: str = "GET"
) -> Response:
    """Proxy request to prediction service"""
    if not circuit_breaker.can_execute():
        raise HTTPException(
            status_code=503,
            detail="Prediction service temporarily unavailable"
        )

    url = f"{settings.PREDICTION_SERVICE_URL}{path}"

    try:
        body = await request.body() if method in ["POST", "PUT", "PATCH"] else None

        headers = dict(request.headers)
        headers.pop("host", None)

        # Add user info
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
        logger.error(f"Prediction service request failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Prediction service unavailable"
        )


async def proxy_multipart_request(
    request: Request,
    path: str
) -> Response:
    """Proxy multipart form data to prediction service"""
    if not circuit_breaker.can_execute():
        raise HTTPException(
            status_code=503,
            detail="Prediction service temporarily unavailable"
        )

    url = f"{settings.PREDICTION_SERVICE_URL}{path}"

    try:
        # Read form data
        form = await request.form()

        # Prepare headers
        headers = {}
        if hasattr(request.state, "user_id"):
            headers["x-user-id"] = request.state.user_id
            headers["x-user-email"] = request.state.email
            headers["x-user-is-admin"] = str(request.state.is_admin)

        # Prepare files and data
        files = {}
        data = {}

        for key, value in form.items():
            if hasattr(value, "file"):  # UploadFile
                files[key] = (value.filename, await value.read(), value.content_type)
            else:
                data[key] = value

        response = await client.post(
            url,
            headers=headers,
            files=files,
            data=data,
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
        logger.error(f"Prediction service request failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Prediction service unavailable"
        )


@router.post("/")
async def create_prediction(request: Request):
    """Create a synchronous prediction"""
    return await proxy_multipart_request(request, "/api/v1/predictions/")


@router.post("/async")
async def create_async_prediction(request: Request):
    """Create an asynchronous prediction"""
    return await proxy_multipart_request(request, "/api/v1/predictions/async")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, request: Request):
    """Get async task status"""
    return await proxy_request(request, f"/api/v1/predictions/task/{task_id}", "GET")


@router.get("/history")
async def get_history(request: Request):
    """Get prediction history"""
    return await proxy_request(request, "/api/v1/predictions/history", "GET")


@router.get("/doctor/queue")
async def get_doctor_queue(request: Request):
    """Doctor: get pending review queue"""
    return await proxy_request(request, "/api/v1/predictions/doctor/queue", "GET")


@router.get("/{prediction_id}")
async def get_prediction(prediction_id: str, request: Request):
    """Get prediction by ID"""
    return await proxy_request(request, f"/api/v1/predictions/{prediction_id}", "GET")


@router.post("/{prediction_id}/feedback")
async def submit_feedback(prediction_id: str, request: Request):
    """Submit feedback for a prediction"""
    return await proxy_request(request, f"/api/v1/predictions/{prediction_id}/feedback", "POST")


@router.post("/{prediction_id}/review")
async def review_prediction(prediction_id: str, request: Request):
    """Doctor: approve or reject a prediction"""
    return await proxy_request(request, f"/api/v1/predictions/{prediction_id}/review", "POST")
