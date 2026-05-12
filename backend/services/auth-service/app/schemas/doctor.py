"""
Doctor and subscription schemas
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class DoctorRegister(BaseModel):
    """Doctor registration request"""
    email: str
    password: str = Field(..., min_length=8)
    full_name: str
    license_number: str
    specialization: Optional[str] = None
    phone: Optional[str] = None


class DoctorLogin(BaseModel):
    """Doctor login request"""
    email: str
    password: str


class DoctorResponse(BaseModel):
    """Doctor profile response"""
    id: str
    email: str
    full_name: str
    license_number: str
    specialization: Optional[str] = None
    is_verified: bool
    phone: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionPlanResponse(BaseModel):
    """Subscription plan response"""
    id: str
    name: str
    duration_days: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription response"""
    id: str
    user_id: str
    plan_id: str
    is_active: bool
    start_date: datetime
    end_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionRequestCreate(BaseModel):
    """Create subscription request"""
    plan_id: str
    contact_info: Optional[str] = None
    notes: Optional[str] = None


class SubscriptionRequestResponse(BaseModel):
    """Subscription request response"""
    id: str
    user_id: Optional[str] = None
    plan_id: str
    status: str
    contact_info: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
