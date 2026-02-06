"""
JWT Token Service
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.schemas.token import TokenPayload


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTService:
    """JWT token management service"""

    def __init__(self):
        self.secret = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    def create_access_token(
        self,
        user_id: str,
        email: str,
        is_admin: bool = False
    ) -> Tuple[str, datetime]:
        """Create access token"""
        now = datetime.utcnow()
        expire = now + self.access_token_expire

        payload = {
            "sub": user_id,
            "email": email,
            "is_admin": is_admin,
            "type": "access",
            "iat": now,
            "exp": expire,
        }

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token, expire

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        is_admin: bool = False
    ) -> Tuple[str, datetime]:
        """Create refresh token"""
        now = datetime.utcnow()
        expire = now + self.refresh_token_expire

        payload = {
            "sub": user_id,
            "email": email,
            "is_admin": is_admin,
            "type": "refresh",
            "iat": now,
            "exp": expire,
        }

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token, expire

    def create_tokens(
        self,
        user_id: str,
        email: str,
        is_admin: bool = False
    ) -> dict:
        """Create both access and refresh tokens"""
        access_token, access_expire = self.create_access_token(user_id, email, is_admin)
        refresh_token, refresh_expire = self.create_refresh_token(user_id, email, is_admin)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(self.access_token_expire.total_seconds()),
            "refresh_expires_at": refresh_expire,
        }

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return TokenPayload(
                sub=payload.get("sub"),
                email=payload.get("email"),
                is_admin=payload.get("is_admin", False),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
                type=payload.get("type", "access"),
            )
        except JWTError:
            return None

    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenPayload]:
        """Verify token and check type"""
        payload = self.decode_token(token)
        if not payload:
            return None
        if payload.type != token_type:
            return None
        if payload.exp < datetime.utcnow():
            return None
        return payload

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)


# Singleton instance
jwt_service = JWTService()
