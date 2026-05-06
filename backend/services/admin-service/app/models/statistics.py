"""
Statistics and metrics models
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class DailyStatistics(Base):
    """Aggregated daily statistics"""
    __tablename__ = "daily_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, unique=True, index=True)

    # User metrics
    total_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)

    # Prediction metrics
    total_predictions = Column(Integer, default=0)
    successful_predictions = Column(Integer, default=0)
    failed_predictions = Column(Integer, default=0)
    avg_processing_time_ms = Column(Float, nullable=True)

    # Disease distribution
    disease_distribution = Column(JSON, nullable=True)  # {class_name: count}
    malignant_count = Column(Integer, default=0)
    benign_count = Column(Integer, default=0)

    # Feedback metrics
    feedback_count = Column(Integer, default=0)
    positive_feedback = Column(Integer, default=0)
    negative_feedback = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DailyStatistics {self.date}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "total_users": self.total_users,
            "new_users": self.new_users,
            "active_users": self.active_users,
            "total_predictions": self.total_predictions,
            "successful_predictions": self.successful_predictions,
            "failed_predictions": self.failed_predictions,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "disease_distribution": self.disease_distribution,
            "malignant_count": self.malignant_count,
            "benign_count": self.benign_count,
            "feedback_count": self.feedback_count,
            "positive_feedback": self.positive_feedback,
            "negative_feedback": self.negative_feedback,
        }


class ModelMetrics(Base):
    """Model performance tracking"""
    __tablename__ = "model_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Performance metrics
    total_predictions = Column(Integer, default=0)
    avg_confidence = Column(Float, nullable=True)
    min_confidence = Column(Float, nullable=True)
    max_confidence = Column(Float, nullable=True)

    # Feedback-based accuracy
    feedback_count = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    accuracy = Column(Float, nullable=True)

    # Class-wise metrics
    class_metrics = Column(JSON, nullable=True)  # {class: {count, avg_confidence}}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ModelMetrics {self.model_version} - {self.date}>"


class AdminNotification(Base):
    """Admin notifications and alerts"""
    __tablename__ = "admin_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Notification details
    type = Column(String(50), nullable=False, index=True)  # alert, info, warning
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")  # low, normal, high, critical

    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    # Extra data
    extra_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AdminNotification {self.type} - {self.title}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
