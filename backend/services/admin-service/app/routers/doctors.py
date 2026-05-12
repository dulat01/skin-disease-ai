"""
Admin Doctor Management Router
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Doctors"])


@router.get("/doctors", response_model=dict)
async def list_doctors(
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Admin: list all doctors or only verified doctors"""
    try:
        import httpx
        import os

        AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')

        # Call auth service to get doctors (would need to implement this endpoint)
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/v1/admin/doctors",
                params={"verified_only": verified_only}
            )

            if response.status_code == 200:
                return response.json()

        return {
            "success": False,
            "error": "Failed to fetch doctors"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/doctors/{doctor_id}/verify", response_model=dict)
async def verify_doctor(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Admin: verify a doctor account"""
    try:
        import httpx
        import os

        AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/admin/doctors/{doctor_id}/verify"
            )

            if response.status_code == 200:
                return response.json()

        return {
            "success": False,
            "error": "Failed to verify doctor"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/subscription-requests", response_model=dict)
async def list_subscription_requests(
    status_filter: str = "pending",
    db: AsyncSession = Depends(get_db)
):
    """Admin: list subscription requests"""
    try:
        import httpx
        import os

        AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/v1/admin/subscription-requests",
                params={"status": status_filter}
            )

            if response.status_code == 200:
                return response.json()

        return {
            "success": False,
            "error": "Failed to fetch subscription requests"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/subscription-requests/{request_id}/approve", response_model=dict)
async def approve_subscription_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Admin: approve a subscription request"""
    try:
        import httpx
        import os

        AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/admin/subscription-requests/{request_id}/approve"
            )

            if response.status_code == 200:
                return response.json()

        return {
            "success": False,
            "error": "Failed to approve subscription request"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/subscription-requests/{request_id}/decline", response_model=dict)
async def decline_subscription_request(
    request_id: UUID,
    reason: str = "Request declined",
    db: AsyncSession = Depends(get_db)
):
    """Admin: decline a subscription request"""
    try:
        import httpx
        import os

        AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/admin/subscription-requests/{request_id}/decline",
                json={"reason": reason}
            )

            if response.status_code == 200:
                return response.json()

        return {
            "success": False,
            "error": "Failed to decline subscription request"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
