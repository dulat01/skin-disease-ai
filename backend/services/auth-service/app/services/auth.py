"""
Authentication Service
"""
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.token import RefreshToken, AuthAuditLog
from app.schemas.user import UserCreate
from app.schemas.token import Token, TokenPayload
from app.services.jwt import jwt_service
from app.services.user import UserService


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def register(
        self,
        user_data: UserCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, Token]:
        """Register a new user"""
        # Check if user exists
        existing_user = await self.user_service.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Create user
        user = await self.user_service.create(user_data)

        # Create tokens
        tokens = jwt_service.create_tokens(
            str(user.id),
            user.email,
            user.is_admin
        )

        # Store refresh token
        await self._store_refresh_token(
            user.id,
            tokens["refresh_token"],
            tokens["refresh_expires_at"],
            ip_address,
            user_agent
        )

        # Log registration
        await self._log_auth_event(
            user_id=user.id,
            event_type="register",
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

        return user, Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        )

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, Token]:
        """Authenticate user and return tokens"""
        # Get user
        user = await self.user_service.get_by_email(email)

        if not user:
            await self._log_auth_event(
                event_type="login",
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason="User not found"
            )
            raise ValueError("Invalid email or password")

        if not user.is_active:
            await self._log_auth_event(
                user_id=user.id,
                event_type="login",
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason="Account deactivated"
            )
            raise ValueError("Account is deactivated")

        # Verify password
        if not jwt_service.verify_password(password, user.hashed_password):
            await self._log_auth_event(
                user_id=user.id,
                event_type="login",
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason="Invalid password"
            )
            raise ValueError("Invalid email or password")

        # Create tokens
        tokens = jwt_service.create_tokens(
            str(user.id),
            user.email,
            user.is_admin
        )

        # Store refresh token
        await self._store_refresh_token(
            user.id,
            tokens["refresh_token"],
            tokens["refresh_expires_at"],
            ip_address,
            user_agent
        )

        # Update last login
        await self.user_service.update_last_login(user.id)

        # Log login
        await self._log_auth_event(
            user_id=user.id,
            event_type="login",
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

        return user, Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        )

    async def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Token:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = jwt_service.verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        # Check if token is revoked
        token_hash = jwt_service.hash_token(refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False
            )
        )
        stored_token = result.scalar_one_or_none()

        if not stored_token:
            raise ValueError("Refresh token not found or revoked")

        # Get user
        user = await self.user_service.get_by_id(UUID(payload.sub))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Revoke old refresh token
        await self._revoke_refresh_token(token_hash)

        # Create new tokens
        tokens = jwt_service.create_tokens(
            str(user.id),
            user.email,
            user.is_admin
        )

        # Store new refresh token
        await self._store_refresh_token(
            user.id,
            tokens["refresh_token"],
            tokens["refresh_expires_at"],
            ip_address,
            user_agent
        )

        return Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        )

    async def logout(
        self,
        user_id: UUID,
        refresh_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Logout user by revoking refresh token(s)"""
        if refresh_token:
            # Revoke specific token
            token_hash = jwt_service.hash_token(refresh_token)
            await self._revoke_refresh_token(token_hash)
        else:
            # Revoke all user's tokens
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
                .values(is_revoked=True, revoked_at=datetime.utcnow())
            )

        # Log logout
        await self._log_auth_event(
            user_id=user_id,
            event_type="logout",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

        return True

    async def _store_refresh_token(
        self,
        user_id: UUID,
        token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RefreshToken:
        """Store refresh token in database"""
        token_hash = jwt_service.hash_token(token)

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(refresh_token)
        await self.db.flush()
        return refresh_token

    async def _revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token"""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True, revoked_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def _log_auth_event(
        self,
        event_type: str,
        success: bool,
        user_id: Optional[UUID] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log authentication event"""
        audit_log = AuthAuditLog(
            user_id=user_id,
            event_type=event_type,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        self.db.add(audit_log)
        await self.db.flush()

    async def verify_access_token(self, token: str) -> Optional[TokenPayload]:
        """Verify an access token"""
        return jwt_service.verify_token(token, token_type="access")
