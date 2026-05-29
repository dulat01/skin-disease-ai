"""
Prediction models
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class Prediction(Base):
    """Prediction history model"""
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Image info
    image_path = Column(Text, nullable=False)  # MinIO path
    original_filename = Column(String(255), nullable=True)
    image_size_bytes = Column(Integer, nullable=True)

    # Prediction results
    predicted_class = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)
    is_malignant = Column(Boolean, nullable=True)

    # Top predictions (JSON array)
    top_predictions = Column(JSON, nullable=True)  # [{class: str, confidence: float}]

    # Processing info
    processing_time_ms = Column(Integer, nullable=True)
    model_version = Column(String(50), default="1.0.0")

    # Status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Celery task (for async predictions)
    celery_task_id = Column(String(255), nullable=True, index=True)

    # User message for doctor (subscription users only)
    user_message = Column(Text, nullable=True)

    # Doctor review (if user has subscription)
    doctor_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Doctor assigned to review
    doctor_approved = Column(Boolean, nullable=True)
    doctor_notes = Column(Text, nullable=True)
    doctor_reviewed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Prediction {self.id} - {self.predicted_class}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "image_path": self.image_path,
            "original_filename": self.original_filename,
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "is_malignant": self.is_malignant,
            "top_predictions": self.top_predictions,
            "processing_time_ms": self.processing_time_ms,
            "model_version": self.model_version,
            "status": self.status,
            "error_message": self.error_message,
            "celery_task_id": self.celery_task_id,
            "doctor_id": str(self.doctor_id) if self.doctor_id else None,
            "user_message": self.user_message,
            "doctor_approved": self.doctor_approved,
            "doctor_notes": self.doctor_notes,
            "doctor_reviewed_at": self.doctor_reviewed_at.isoformat() if self.doctor_reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class PredictionFeedback(Base):
    """User feedback for predictions"""
    __tablename__ = "prediction_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Feedback
    is_correct = Column(Boolean, nullable=False)
    actual_class = Column(String(255), nullable=True)  # If incorrect, what was the actual class
    comment = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PredictionFeedback {self.id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "prediction_id": str(self.prediction_id),
            "user_id": str(self.user_id),
            "is_correct": self.is_correct,
            "actual_class": self.actual_class,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
