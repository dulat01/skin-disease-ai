"""
Event Publisher for Prediction Service
"""
import logging
from datetime import datetime

from app.config import settings
from app.models.prediction import Prediction, PredictionFeedback

# Import shared utilities
import sys
sys.path.append('/app')
try:
    from shared.utils.rabbitmq import get_rabbitmq_client
    from shared.schemas.events import (
        EventType,
        EXCHANGES,
        ROUTING_KEYS,
    )
except ImportError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))
    from shared.utils.rabbitmq import get_rabbitmq_client
    from shared.schemas.events import (
        EventType,
        EXCHANGES,
        ROUTING_KEYS,
    )

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes prediction events to RabbitMQ"""

    def __init__(self):
        self.exchange_name = EXCHANGES["prediction"]
        self._client = None

    async def _get_client(self):
        """Get or create RabbitMQ client"""
        if not self._client:
            self._client = get_rabbitmq_client(settings.RABBITMQ_URL)
            await self._client.connect()
        return self._client

    async def publish_prediction_created(self, prediction: Prediction) -> None:
        """Publish prediction created event"""
        try:
            client = await self._get_client()

            event_data = {
                "event_type": EventType.PREDICTION_CREATED.value,
                "source_service": settings.SERVICE_NAME,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "prediction_id": str(prediction.id),
                    "user_id": str(prediction.user_id),
                    "image_path": prediction.image_path,
                    "is_async": prediction.celery_task_id is not None,
                }
            }

            await client.publish(
                self.exchange_name,
                ROUTING_KEYS[EventType.PREDICTION_CREATED],
                event_data
            )
            logger.info(f"Published prediction created event: {prediction.id}")
        except Exception as e:
            logger.error(f"Failed to publish prediction created event: {e}")

    async def publish_prediction_completed(self, prediction: Prediction) -> None:
        """Publish prediction completed event"""
        try:
            client = await self._get_client()

            event_data = {
                "event_type": EventType.PREDICTION_COMPLETED.value,
                "source_service": settings.SERVICE_NAME,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "prediction_id": str(prediction.id),
                    "user_id": str(prediction.user_id),
                    "predicted_class": prediction.predicted_class,
                    "confidence": prediction.confidence,
                    "processing_time_ms": prediction.processing_time_ms,
                    "is_malignant": prediction.is_malignant,
                }
            }

            await client.publish(
                self.exchange_name,
                ROUTING_KEYS[EventType.PREDICTION_COMPLETED],
                event_data
            )
            logger.info(f"Published prediction completed event: {prediction.id}")
        except Exception as e:
            logger.error(f"Failed to publish prediction completed event: {e}")

    async def publish_prediction_feedback(self, feedback: PredictionFeedback) -> None:
        """Publish prediction feedback event"""
        try:
            client = await self._get_client()

            event_data = {
                "event_type": EventType.PREDICTION_FEEDBACK.value,
                "source_service": settings.SERVICE_NAME,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "prediction_id": str(feedback.prediction_id),
                    "user_id": str(feedback.user_id),
                    "is_correct": feedback.is_correct,
                    "actual_class": feedback.actual_class,
                    "comment": feedback.comment,
                }
            }

            await client.publish(
                self.exchange_name,
                ROUTING_KEYS[EventType.PREDICTION_FEEDBACK],
                event_data
            )
            logger.info(f"Published prediction feedback event: {feedback.prediction_id}")
        except Exception as e:
            logger.error(f"Failed to publish prediction feedback event: {e}")
