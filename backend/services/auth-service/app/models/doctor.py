"""
Doctor model for subscription-based diagnosis approval
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class Doctor(Base):
    """Doctor account model for image diagnosis approval"""
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)

    # Credentials
    license_number = Column(String(100), nullable=False)
    specialization = Column(String(255), nullable=True)

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile
    avatar_url = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Doctor {self.email}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "license_number": self.license_number,
            "specialization": self.specialization,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }


class SubscriptionPlan(Base):
    """Subscription plan options"""
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)  # "1-month", "3-month", "6-month"
    duration_days = Column(String(10), nullable=False)  # 30, 90, 180
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SubscriptionPlan {self.name}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "duration_days": self.duration_days,
            "description": self.description,
        }


class Subscription(Base):
    """User subscription tracking"""
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('subscription_plans.id'), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Subscription {self.user_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "plan_id": str(self.plan_id),
            "is_active": self.is_active,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SubscriptionRequest(Base):
    """Track subscription purchase requests"""
    __tablename__ = "subscription_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('subscription_plans.id'), nullable=False)

    status = Column(String(20), default="pending", nullable=False)  # pending, approved, declined
    contact_info = Column(String(255), nullable=True)  # email/phone for contact
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SubscriptionRequest {self.user_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "plan_id": str(self.plan_id),
            "status": self.status,
            "contact_info": self.contact_info,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
