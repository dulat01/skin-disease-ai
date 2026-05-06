"""
Users Router - Admin user management
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["User Management"])

# HTTP client for auth service
client = httpx.AsyncClient(timeout=10.0)


@router.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users.

    Fetches user data from auth service.
    """
    try:
        # Build query params
        params = {
            "page": page,
            "page_size": page_size
        }
        if is_active is not None:
            params["is_active"] = is_active
        if search:
            params["search"] = search

        # Fetch from auth service
        response = await client.get(
            f"{settings.AUTH_SERVICE_URL}/api/v1/admin/users",
            params=params,
            headers={"x-user-is-admin": "True"}
        )

        if response.status_code == 200:
            return response.json()
        else:
            # Return empty list if auth service unavailable
            return {
                "success": True,
                "message": "Users retrieved (auth service unavailable)",
                "data": {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0
                }
            }

    except httpx.RequestError as e:
        logger.error(f"Failed to fetch users from auth service: {e}")
        return {
            "success": True,
            "message": "Users retrieved (auth service unavailable)",
            "data": {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        }


@router.get("/users/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed user information.
    """
    try:
        response = await client.get(
            f"{settings.AUTH_SERVICE_URL}/api/v1/admin/users/{user_id}",
            headers={"x-user-is-admin": "True"}
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

    except httpx.RequestError as e:
        logger.error(f"Failed to fetch user from auth service: {e}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")


@router.post("/users/{user_id}/deactivate", response_model=dict)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user account.
    """
    try:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/api/v1/admin/users/{user_id}/deactivate",
            headers={"x-user-is-admin": "True"}
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

    except httpx.RequestError as e:
        logger.error(f"Failed to deactivate user: {e}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")


@router.post("/users/{user_id}/activate", response_model=dict)
async def activate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reactivate a user account.
    """
    try:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/api/v1/admin/users/{user_id}/activate",
            headers={"x-user-is-admin": "True"}
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

    except httpx.RequestError as e:
        logger.error(f"Failed to activate user: {e}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")
