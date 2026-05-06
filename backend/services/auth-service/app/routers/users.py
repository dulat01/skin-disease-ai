"""
Users Router
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.services.user import UserService
from app.services.jwt import jwt_service

router = APIRouter(prefix="/api/v1/auth", tags=["Users"])


async def get_current_user_id(
    authorization: str = Header(..., description="Bearer token")
) -> UUID:
    """Extract user ID from JWT token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization.split(" ")[1]
    payload = jwt_service.verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return UUID(payload.sub)


@router.get("/me", response_model=dict)
async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current authenticated user's profile.
    Requires a valid access token in the Authorization header.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "message": "User retrieved successfully",
        "data": UserResponse.model_validate(user.to_dict())
    }


@router.put("/me", response_model=dict)
async def update_current_user(
    user_data: UserUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's profile.

    - **full_name**: Optional - User's new full name
    - **phone**: Optional - User's phone number
    - **avatar_url**: Optional - URL to user's avatar image
    """
    user_service = UserService(db)
    user = await user_service.update(user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": UserResponse.model_validate(user.to_dict())
    }


@router.post("/me/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Change the current user's password.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars, uppercase, lowercase, digit)
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not jwt_service.verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    await user_service.update_password(user_id, password_data.new_password)

    return {
        "success": True,
        "message": "Password changed successfully"
    }


@router.delete("/me", response_model=dict)
async def delete_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate the current user's account.
    This is a soft delete - the account can be reactivated.
    """
    user_service = UserService(db)
    success = await user_service.deactivate(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "message": "Account deactivated successfully"
    }
