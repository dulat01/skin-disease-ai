"""
History Router
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.prediction import PredictionResponse, FeedbackCreate, FeedbackResponse, TopPrediction
from app.services.predictor import PredictorService
from app.events.publisher import EventPublisher

router = APIRouter(prefix="/api/v1/predictions", tags=["History"])


def get_user_id_from_header(x_user_id: str = Header(..., description="User ID from gateway")) -> str:
    """Extract user ID from header (set by API gateway after JWT validation)"""
    return x_user_id


@router.get("/history", response_model=dict)
async def get_prediction_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: str = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's prediction history.

    Returns paginated list of predictions, most recent first.
    """
    predictor = PredictorService(db)

    skip = (page - 1) * page_size
    predictions, total = await predictor.get_user_history(
        user_id=user_id,
        skip=skip,
        limit=page_size
    )

    # Format predictions
    items = []
    for pred in predictions:
        top_predictions = None
        if pred.top_predictions:
            top_predictions = [
                TopPrediction(
                    class_name=p["class_name"],
                    confidence=p["confidence"],
                    is_malignant=p["is_malignant"]
                )
                for p in pred.top_predictions
            ]

        items.append(PredictionResponse(
            id=str(pred.id),
            user_id=str(pred.user_id),
            image_path=pred.image_path,
            original_filename=pred.original_filename,
            predicted_class=pred.predicted_class,
            confidence=pred.confidence,
            is_malignant=pred.is_malignant,
            top_predictions=top_predictions,
            processing_time_ms=pred.processing_time_ms,
            model_version=pred.model_version,
            status=pred.status,
            error_message=pred.error_message,
            celery_task_id=pred.celery_task_id,
            created_at=pred.created_at,
            completed_at=pred.completed_at
        ))

    total_pages = (total + page_size - 1) // page_size

    return {
        "success": True,
        "message": "Prediction history retrieved",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    }


@router.post("/{prediction_id}/feedback", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    prediction_id: str,
    feedback: FeedbackCreate,
    user_id: str = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for a prediction.

    This helps improve the model over time.
    - **is_correct**: Whether the prediction was correct
    - **actual_class**: If incorrect, what was the actual diagnosis
    - **comment**: Optional additional feedback
    """
    predictor = PredictorService(db)

    try:
        feedback_record = await predictor.add_feedback(
            prediction_id=UUID(prediction_id),
            user_id=user_id,
            feedback_data=feedback
        )

        # Publish event
        publisher = EventPublisher()
        await publisher.publish_prediction_feedback(feedback_record)

        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "data": FeedbackResponse(
                id=str(feedback_record.id),
                prediction_id=str(feedback_record.prediction_id),
                user_id=str(feedback_record.user_id),
                is_correct=feedback_record.is_correct,
                actual_class=feedback_record.actual_class,
                comment=feedback_record.comment,
                created_at=feedback_record.created_at
            )
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
