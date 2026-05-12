"""
Patient Profile model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class PatientProfile(Base):
    """Patient medical profile linked to User"""
    __tablename__ = "patient_profiles"
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_patient_profiles_user_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Demographics
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)  # Male/Female/Other/Prefer not to say
    blood_type = Column(String(5), nullable=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-

    # Medical history
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)

    # Emergency contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PatientProfile {self.user_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "blood_type": self.blood_type,
            "allergies": self.allergies,
            "medical_history": self.medical_history,
            "current_medications": self.current_medications,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "emergency_contact_relation": self.emergency_contact_relation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
