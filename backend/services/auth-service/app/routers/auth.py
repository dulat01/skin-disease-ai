"""
Authentication Router
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token, LoginRequest, RefreshTokenRequest, LogoutRequest
from app.services.auth import AuthService
from app.events.publisher import EventPublisher

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    - **email**: Valid email address
    - **password**: Min 8 chars, must contain uppercase, lowercase, and digit
    - **full_name**: User's full name (2-255 chars)
    """
    ip_address, user_agent = get_client_info(request)
    auth_service = AuthService(db)

    try:
        user, tokens = await auth_service.register(
            user_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Publish event
        publisher = EventPublisher()
        await publisher.publish_user_registered(user)

        return {
            "success": True,
            "message": "Registration successful",
            "data": {
                "user": UserResponse.model_validate(user.to_dict()),
                "tokens": tokens.model_dump()
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=dict)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access/refresh tokens.

    - **email**: User's email address
    - **password**: User's password
    """
    ip_address, user_agent = get_client_info(request)
    auth_service = AuthService(db)

    try:
        user, tokens = await auth_service.login(
            login_data.email,
            login_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Publish event
        publisher = EventPublisher()
        await publisher.publish_user_logged_in(user, ip_address, user_agent)

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "user": UserResponse.model_validate(user.to_dict()),
                "tokens": tokens.model_dump()
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh", response_model=dict)
async def refresh_tokens(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.

    - **refresh_token**: Valid refresh token from login
    """
    ip_address, user_agent = get_client_info(request)
    auth_service = AuthService(db)

    try:
        tokens = await auth_service.refresh_tokens(
            refresh_data.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "success": True,
            "message": "Tokens refreshed successfully",
            "data": {
                "tokens": tokens.model_dump()
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/logout", response_model=dict)
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = None  # Will be injected by middleware
):
    """
    Logout user by revoking refresh token(s).

    - **refresh_token**: Optional - if provided, revokes only that token.
                         If not provided, revokes all user's refresh tokens.
    """
    ip_address, user_agent = get_client_info(request)

    # In real usage, current_user_id comes from JWT middleware
    # For now, we'll require the refresh token to identify the user
    if not logout_data.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required for logout"
        )

    auth_service = AuthService(db)

    try:
        # Verify the refresh token first to get user_id
        from app.services.jwt import jwt_service
        payload = jwt_service.verify_token(logout_data.refresh_token, token_type="refresh")
        if not payload:
            raise ValueError("Invalid refresh token")

        from uuid import UUID
        await auth_service.logout(
            UUID(payload.sub),
            refresh_token=logout_data.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "success": True,
            "message": "Logout successful"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/verify", response_model=dict)
async def verify_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify an access token and return the user info.
    Token should be provided in Authorization header.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)

    payload = await auth_service.verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "success": True,
        "message": "Token is valid",
        "data": {
            "user_id": payload.sub,
            "email": payload.email,
            "is_admin": payload.is_admin,
            "expires_at": payload.exp.isoformat()
        }
    }
