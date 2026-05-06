"""
Token and audit models
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class RefreshToken(Base):
    """Refresh token storage"""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Device info
    device_name = Column(String(255), nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Status
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<RefreshToken {self.id}>"


class AuthAuditLog(Base):
    """Authentication audit trail"""
    __tablename__ = "auth_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, register, password_change, etc.
    email = Column(String(255), nullable=True)

    # Request info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Result
    success = Column(Boolean, nullable=False)
    failure_reason = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<AuthAuditLog {self.event_type} at {self.created_at}>"
