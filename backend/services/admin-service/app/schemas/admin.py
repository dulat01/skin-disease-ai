"""
Admin schemas
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class DashboardResponse(BaseModel):
    """Dashboard overview response"""
    # Today's stats
    today_predictions: int = 0
    today_users: int = 0
    today_feedback: int = 0

    # Overall stats
    total_users: int = 0
    total_predictions: int = 0
    total_feedback: int = 0

    # Health
    model_accuracy: Optional[float] = None
    avg_processing_time_ms: Optional[float] = None

    # Recent activity
    recent_predictions: List[Dict[str, Any]] = []
    disease_distribution: Dict[str, int] = {}


class DailyStatisticsResponse(BaseModel):
    """Daily statistics response"""
    id: str
    date: date
    total_users: int
    new_users: int
    active_users: int
    total_predictions: int
    successful_predictions: int
    failed_predictions: int
    avg_processing_time_ms: Optional[float]
    disease_distribution: Optional[Dict[str, int]]
    malignant_count: int
    benign_count: int
    feedback_count: int
    positive_feedback: int
    negative_feedback: int

    class Config:
        from_attributes = True


class ModelMetricsResponse(BaseModel):
    """Model metrics response"""
    model_version: str
    total_predictions: int
    avg_confidence: Optional[float]
    min_confidence: Optional[float]
    max_confidence: Optional[float]
    feedback_count: int
    correct_predictions: int
    accuracy: Optional[float]
    class_metrics: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    type: str
    title: str
    message: str
    priority: str
    is_read: bool
    is_dismissed: bool
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list item (from auth service)"""
    id: str
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    predictions_count: int = 0
