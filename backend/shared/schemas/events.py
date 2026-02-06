"""
Shared event schemas for RabbitMQ inter-service communication
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Event types for inter-service communication"""
    # Auth events
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # Prediction events
    PREDICTION_CREATED = "prediction.created"
    PREDICTION_COMPLETED = "prediction.completed"
    PREDICTION_FAILED = "prediction.failed"
    PREDICTION_FEEDBACK = "prediction.feedback"

    # Admin events
    ADMIN_ALERT = "admin.alert"
    STATISTICS_UPDATED = "statistics.updated"


class BaseEvent(BaseModel):
    """Base event schema"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str
    correlation_id: Optional[str] = None
    payload: dict = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserRegisteredEvent(BaseEvent):
    """Event emitted when a new user registers"""
    event_type: EventType = EventType.USER_REGISTERED
    source_service: str = "auth-service"

    class Payload(BaseModel):
        user_id: str
        email: str
        full_name: str
        is_admin: bool = False
        created_at: datetime


class UserLoggedInEvent(BaseEvent):
    """Event emitted when a user logs in"""
    event_type: EventType = EventType.USER_LOGGED_IN
    source_service: str = "auth-service"

    class Payload(BaseModel):
        user_id: str
        email: str
        ip_address: Optional[str] = None
        user_agent: Optional[str] = None


class PredictionCreatedEvent(BaseEvent):
    """Event emitted when a prediction is initiated"""
    event_type: EventType = EventType.PREDICTION_CREATED
    source_service: str = "prediction-service"

    class Payload(BaseModel):
        prediction_id: str
        user_id: str
        image_path: str
        is_async: bool = False


class PredictionCompletedEvent(BaseEvent):
    """Event emitted when a prediction is completed"""
    event_type: EventType = EventType.PREDICTION_COMPLETED
    source_service: str = "prediction-service"

    class Payload(BaseModel):
        prediction_id: str
        user_id: str
        predicted_class: str
        confidence: float
        processing_time_ms: int
        is_malignant: bool


class PredictionFeedbackEvent(BaseEvent):
    """Event emitted when user provides feedback on a prediction"""
    event_type: EventType = EventType.PREDICTION_FEEDBACK
    source_service: str = "prediction-service"

    class Payload(BaseModel):
        prediction_id: str
        user_id: str
        is_correct: bool
        actual_class: Optional[str] = None
        comment: Optional[str] = None


# Exchange and queue names
EXCHANGES = {
    "auth": "auth.events",
    "prediction": "prediction.events",
    "admin": "admin.events",
}

QUEUES = {
    "auth_events": "auth.events.queue",
    "prediction_events": "prediction.events.queue",
    "admin_notifications": "admin.notifications.queue",
    "statistics_aggregator": "statistics.aggregator.queue",
}

ROUTING_KEYS = {
    EventType.USER_REGISTERED: "user.registered",
    EventType.USER_LOGGED_IN: "user.logged_in",
    EventType.USER_LOGGED_OUT: "user.logged_out",
    EventType.PREDICTION_CREATED: "prediction.created",
    EventType.PREDICTION_COMPLETED: "prediction.completed",
    EventType.PREDICTION_FEEDBACK: "prediction.feedback",
}
