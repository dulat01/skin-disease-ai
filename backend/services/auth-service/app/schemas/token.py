"""
Token schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    email: str
    is_admin: bool = False
    exp: datetime
    iat: datetime
    type: str = "access"  # access or refresh


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request schema"""
    refresh_token: Optional[str] = None  # If provided, revokes specific token
