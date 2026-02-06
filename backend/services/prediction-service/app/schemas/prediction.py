"""
Prediction schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TopPrediction(BaseModel):
    """Single prediction result"""
    class_name: str
    confidence: float
    is_malignant: bool


class PredictionCreate(BaseModel):
    """Schema for creating a prediction (internal)"""
    user_id: str
    image_path: str
    original_filename: Optional[str] = None
    image_size_bytes: Optional[int] = None


class PredictionResult(BaseModel):
    """Schema for prediction result"""
    predicted_class: str
    confidence: float
    is_malignant: bool
    top_predictions: List[TopPrediction]
    processing_time_ms: int


class PredictionResponse(BaseModel):
    """Schema for prediction response"""
    id: str
    user_id: str
    image_path: str
    original_filename: Optional[str] = None
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    is_malignant: Optional[bool] = None
    top_predictions: Optional[List[TopPrediction]] = None
    processing_time_ms: Optional[int] = None
    model_version: str
    status: str
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    is_correct: bool
    actual_class: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: str
    prediction_id: str
    user_id: str
    is_correct: bool
    actual_class: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """Schema for async task status"""
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE
    result: Optional[PredictionResponse] = None
    error: Optional[str] = None
    progress: Optional[int] = None
