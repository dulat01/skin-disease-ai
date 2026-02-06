"""
Predictions Router
"""
import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.prediction import PredictionResponse, TaskStatusResponse, TopPrediction
from app.services.predictor import PredictorService
from app.services.storage import get_storage_service
from app.services.image_processor import ImageProcessor
from app.tasks.prediction_tasks import predict_async
from app.events.publisher import EventPublisher

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])


def get_user_id_from_header(x_user_id: str = Header(..., description="User ID from gateway")) -> str:
    """Extract user ID from header (set by API gateway after JWT validation)"""
    return x_user_id


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    image: UploadFile = File(..., description="Image file to analyze"),
    user_id: str = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a synchronous prediction.

    Upload an image and get immediate classification result.
    Supported formats: JPEG, PNG
    Max size: 10MB
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Read image data
    image_data = await image.read()

    # Run prediction
    predictor = PredictorService(db)

    try:
        prediction = await predictor.predict_sync(
            user_id=user_id,
            image_data=image_data,
            original_filename=image.filename or "image.jpg"
        )

        # Publish event
        publisher = EventPublisher()
        await publisher.publish_prediction_completed(prediction)

        # Format response
        top_predictions = None
        if prediction.top_predictions:
            top_predictions = [
                TopPrediction(
                    class_name=p["class_name"],
                    confidence=p["confidence"],
                    is_malignant=p["is_malignant"]
                )
                for p in prediction.top_predictions
            ]

        return {
            "success": True,
            "message": "Prediction completed successfully",
            "data": PredictionResponse(
                id=str(prediction.id),
                user_id=str(prediction.user_id),
                image_path=prediction.image_path,
                original_filename=prediction.original_filename,
                predicted_class=prediction.predicted_class,
                confidence=prediction.confidence,
                is_malignant=prediction.is_malignant,
                top_predictions=top_predictions,
                processing_time_ms=prediction.processing_time_ms,
                model_version=prediction.model_version,
                status=prediction.status,
                created_at=prediction.created_at,
                completed_at=prediction.completed_at
            )
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/async", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_async_prediction(
    image: UploadFile = File(..., description="Image file to analyze"),
    user_id: str = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Create an asynchronous prediction.

    Upload an image and receive a task ID to poll for results.
    Use GET /task/{task_id} to check status and get results.
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Read and validate image
    image_data = await image.read()
    image_processor = ImageProcessor()

    is_valid, error_msg = image_processor.validate_image(image_data)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Upload to storage
    storage = get_storage_service()
    object_name = storage.generate_object_name(user_id, image.filename or "image.jpg")
    image_path = storage.upload_image(io.BytesIO(image_data), object_name)

    # Create prediction record
    predictor = PredictorService(db)

    # Submit Celery task
    task = predict_async.delay(
        prediction_id="pending",  # Will be updated
        image_path=image_path
    )

    # Create prediction record with task ID
    prediction = await predictor.create_prediction_record(
        user_id=user_id,
        image_path=image_path,
        original_filename=image.filename,
        image_size_bytes=len(image_data),
        celery_task_id=task.id
    )

    # Resubmit task with correct prediction ID
    task = predict_async.delay(
        prediction_id=str(prediction.id),
        image_path=image_path
    )

    # Update prediction with new task ID
    prediction.celery_task_id = task.id
    await db.flush()

    # Publish event
    publisher = EventPublisher()
    await publisher.publish_prediction_created(prediction)

    return {
        "success": True,
        "message": "Prediction task submitted",
        "data": {
            "prediction_id": str(prediction.id),
            "task_id": task.id,
            "status": "pending"
        }
    }


@router.get("/task/{task_id}", response_model=dict)
async def get_task_status(
    task_id: str,
    user_id: str = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of an async prediction task.

    Returns task status and result if completed.
    """
    from celery.result import AsyncResult

    task_result = AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None,
        "error": None,
        "progress": None
    }

    if task_result.status == "PENDING":
        response["progress"] = 0
    elif task_result.status == "STARTED":
        meta = task_result.info or {}
        response["progress"] = meta.get("progress", 0)
    elif task_result.status == "SUCCESS":
        response["result"] = task_result.result
        response["progress"] = 100
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.info)

    return {
        "success": True,
        "message": f"Task status: {task_result.status}",
        "data": response
    }


@router.get("/{prediction_id}", response_model=dict)
async def get_prediction(
    prediction_id: str,
    user_id: str = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a prediction by ID.
    """
    predictor = PredictorService(db)

    try:
        prediction = await predictor.get_prediction(UUID(prediction_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid prediction ID"
        )

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    # Check ownership
    if str(prediction.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Format response
    top_predictions = None
    if prediction.top_predictions:
        top_predictions = [
            TopPrediction(
                class_name=p["class_name"],
                confidence=p["confidence"],
                is_malignant=p["is_malignant"]
            )
            for p in prediction.top_predictions
        ]

    return {
        "success": True,
        "message": "Prediction retrieved successfully",
        "data": PredictionResponse(
            id=str(prediction.id),
            user_id=str(prediction.user_id),
            image_path=prediction.image_path,
            original_filename=prediction.original_filename,
            predicted_class=prediction.predicted_class,
            confidence=prediction.confidence,
            is_malignant=prediction.is_malignant,
            top_predictions=top_predictions,
            processing_time_ms=prediction.processing_time_ms,
            model_version=prediction.model_version,
            status=prediction.status,
            error_message=prediction.error_message,
            celery_task_id=prediction.celery_task_id,
            created_at=prediction.created_at,
            completed_at=prediction.completed_at
        )
    }
