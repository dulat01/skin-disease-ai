"""
Predictor Service - Main prediction logic
"""
import logging
import time
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction, PredictionFeedback
from app.schemas.prediction import PredictionCreate, FeedbackCreate, TopPrediction
from app.ml.model_loader import get_model_loader
from app.services.image_processor import ImageProcessor
from app.services.storage import get_storage_service
from app.config import settings

logger = logging.getLogger(__name__)


class PredictorService:
    """Service for running predictions"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.image_processor = ImageProcessor()
        self.storage = get_storage_service()
        self.model_loader = get_model_loader()

    async def create_prediction_record(
        self,
        user_id: str,
        image_path: str,
        original_filename: Optional[str] = None,
        image_size_bytes: Optional[int] = None,
        celery_task_id: Optional[str] = None
    ) -> Prediction:
        """Create a new prediction record"""
        prediction = Prediction(
            user_id=UUID(user_id),
            image_path=image_path,
            original_filename=original_filename,
            image_size_bytes=image_size_bytes,
            celery_task_id=celery_task_id,
            status="pending" if celery_task_id else "processing"
        )

        self.db.add(prediction)
        await self.db.flush()
        await self.db.refresh(prediction)
        return prediction

    def run_prediction(self, image_data: bytes) -> Tuple[dict, int]:
        """
        Run prediction on image data.

        Args:
            image_data: Raw image bytes

        Returns:
            Tuple of (prediction_result, processing_time_ms)
        """
        start_time = time.time()

        # Load and preprocess image
        image = self.image_processor.load_image(image_data)
        tensor = self.image_processor.preprocess(image)

        # Run inference
        predicted_idx, probabilities = self.model_loader.predict(tensor)

        # Get top predictions
        top_predictions = self.model_loader.get_top_predictions(probabilities, top_k=3)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Get main prediction
        predicted_class = self.model_loader.class_names[predicted_idx]
        confidence = probabilities[predicted_idx]
        is_malignant = settings.MALIGNANCY_MAP.get(predicted_class, False)

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "is_malignant": is_malignant,
            "top_predictions": top_predictions
        }, processing_time_ms

    async def predict_sync(
        self,
        user_id: str,
        image_data: bytes,
        original_filename: str
    ) -> Prediction:
        """
        Run synchronous prediction.

        Args:
            user_id: User ID
            image_data: Raw image bytes
            original_filename: Original filename

        Returns:
            Prediction record with results
        """
        # Validate image
        is_valid, error_msg = self.image_processor.validate_image(image_data)
        if not is_valid:
            raise ValueError(error_msg)

        # Upload to storage
        object_name = self.storage.generate_object_name(user_id, original_filename)
        import io
        image_path = self.storage.upload_image(
            io.BytesIO(image_data),
            object_name
        )

        # Create prediction record
        prediction = await self.create_prediction_record(
            user_id=user_id,
            image_path=image_path,
            original_filename=original_filename,
            image_size_bytes=len(image_data)
        )

        try:
            # Run prediction
            result, processing_time_ms = self.run_prediction(image_data)

            # Update prediction with results
            prediction.predicted_class = result["predicted_class"]
            prediction.confidence = result["confidence"]
            prediction.is_malignant = result["is_malignant"]
            prediction.top_predictions = result["top_predictions"]
            prediction.processing_time_ms = processing_time_ms
            prediction.status = "completed"
            prediction.completed_at = datetime.utcnow()

            await self.db.flush()
            await self.db.refresh(prediction)

            logger.info(f"Prediction completed: {prediction.id} - {prediction.predicted_class}")
            return prediction

        except Exception as e:
            # Update prediction with error
            prediction.status = "failed"
            prediction.error_message = str(e)
            await self.db.flush()
            logger.error(f"Prediction failed: {prediction.id} - {e}")
            raise

    async def get_prediction(self, prediction_id: UUID) -> Optional[Prediction]:
        """Get prediction by ID"""
        result = await self.db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def get_user_history(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Prediction], int]:
        """Get user's prediction history"""
        # Get total count
        count_result = await self.db.execute(
            select(Prediction.id).where(Prediction.user_id == UUID(user_id))
        )
        total = len(count_result.all())

        # Get predictions
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.user_id == UUID(user_id))
            .order_by(Prediction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        predictions = result.scalars().all()

        return list(predictions), total

    async def add_feedback(
        self,
        prediction_id: UUID,
        user_id: str,
        feedback_data: FeedbackCreate
    ) -> PredictionFeedback:
        """Add feedback for a prediction"""
        # Verify prediction exists and belongs to user
        prediction = await self.get_prediction(prediction_id)
        if not prediction:
            raise ValueError("Prediction not found")
        if str(prediction.user_id) != user_id:
            raise ValueError("Prediction does not belong to user")

        feedback = PredictionFeedback(
            prediction_id=prediction_id,
            user_id=UUID(user_id),
            is_correct=feedback_data.is_correct,
            actual_class=feedback_data.actual_class,
            comment=feedback_data.comment
        )

        self.db.add(feedback)
        await self.db.flush()
        await self.db.refresh(feedback)

        logger.info(f"Feedback added for prediction: {prediction_id}")
        return feedback

    async def update_prediction_status(
        self,
        prediction_id: UUID,
        status: str,
        result: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update prediction status (called by Celery task)"""
        update_data = {
            "status": status,
        }

        if result:
            update_data.update({
                "predicted_class": result.get("predicted_class"),
                "confidence": result.get("confidence"),
                "is_malignant": result.get("is_malignant"),
                "top_predictions": result.get("top_predictions"),
                "processing_time_ms": result.get("processing_time_ms"),
                "completed_at": datetime.utcnow()
            })

        if error_message:
            update_data["error_message"] = error_message

        await self.db.execute(
            update(Prediction)
            .where(Prediction.id == prediction_id)
            .values(**update_data)
        )
        await self.db.flush()
