"""
Celery Tasks for Async Predictions
"""
import logging
from uuid import UUID

from celery import current_task

from app.tasks.celery_app import celery_app
from app.ml.model_loader import get_model_loader
from app.services.image_processor import ImageProcessor
from app.services.storage import get_storage_service
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.prediction_tasks.predict_async")
def predict_async(self, prediction_id: str, image_path: str):
    """
    Async prediction task.

    Args:
        prediction_id: ID of the prediction record
        image_path: Path to image in MinIO

    Returns:
        Prediction result dict
    """
    logger.info(f"Starting async prediction: {prediction_id}")

    try:
        # Update task state
        self.update_state(state="STARTED", meta={"progress": 10})

        # Initialize services
        storage = get_storage_service()
        image_processor = ImageProcessor()
        model_loader = get_model_loader()

        # Download image from storage
        self.update_state(state="STARTED", meta={"progress": 20})
        image_data = storage.download_image(image_path)

        # Validate image
        self.update_state(state="STARTED", meta={"progress": 30})
        is_valid, error_msg = image_processor.validate_image(image_data)
        if not is_valid:
            raise ValueError(error_msg)

        # Preprocess image
        self.update_state(state="STARTED", meta={"progress": 50})
        image = image_processor.load_image(image_data)
        tensor = image_processor.preprocess(image)

        # Run inference
        self.update_state(state="STARTED", meta={"progress": 70})
        import time
        start_time = time.time()
        predicted_idx, probabilities = model_loader.predict(tensor)
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Get results
        self.update_state(state="STARTED", meta={"progress": 90})
        top_predictions = model_loader.get_top_predictions(probabilities, top_k=3)
        predicted_class = model_loader.class_names[predicted_idx]
        confidence = probabilities[predicted_idx]
        is_malignant = settings.MALIGNANCY_MAP.get(predicted_class, False)

        result = {
            "prediction_id": prediction_id,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "is_malignant": is_malignant,
            "top_predictions": top_predictions,
            "processing_time_ms": processing_time_ms,
            "status": "completed"
        }

        logger.info(f"Async prediction completed: {prediction_id} - {predicted_class}")
        return result

    except Exception as e:
        logger.error(f"Async prediction failed: {prediction_id} - {e}")
        return {
            "prediction_id": prediction_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name="app.tasks.prediction_tasks.health_check")
def health_check():
    """Health check task for Celery worker"""
    return {"status": "healthy", "worker": "prediction-worker"}
