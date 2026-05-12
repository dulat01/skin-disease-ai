"""
Patient Profile schemas
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class PatientProfileUpdate(BaseModel):
    """Schema for updating patient profile"""
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    blood_type: Optional[str] = Field(None, max_length=5)
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    current_medications: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=100)


class PatientProfileResponse(BaseModel):
    """Schema for patient profile response"""
    id: str
    user_id: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    current_medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
