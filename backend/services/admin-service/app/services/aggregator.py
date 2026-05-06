"""
Event Aggregator - Processes events from RabbitMQ
"""
import logging
from datetime import datetime, date

from app.config import settings

logger = logging.getLogger(__name__)


class EventAggregator:
    """Aggregates events into statistics"""

    def __init__(self, statistics_service):
        self.statistics_service = statistics_service

    async def process_user_registered(self, event_data: dict) -> None:
        """Process user registered event"""
        try:
            payload = event_data.get("payload", {})
            logger.info(f"Processing user registered event: {payload.get('email')}")

            today = date.today()
            await self.statistics_service.increment_daily_stat(today, "new_users")
            await self.statistics_service.increment_daily_stat(today, "total_users")

        except Exception as e:
            logger.error(f"Error processing user registered event: {e}")

    async def process_user_logged_in(self, event_data: dict) -> None:
        """Process user logged in event"""
        try:
            payload = event_data.get("payload", {})
            logger.info(f"Processing user login event: {payload.get('email')}")

            today = date.today()
            await self.statistics_service.increment_daily_stat(today, "active_users")

        except Exception as e:
            logger.error(f"Error processing user login event: {e}")

    async def process_prediction_created(self, event_data: dict) -> None:
        """Process prediction created event"""
        try:
            payload = event_data.get("payload", {})
            logger.info(f"Processing prediction created event: {payload.get('prediction_id')}")

            # We track predictions when they complete, not when created

        except Exception as e:
            logger.error(f"Error processing prediction created event: {e}")

    async def process_prediction_completed(self, event_data: dict) -> None:
        """Process prediction completed event"""
        try:
            payload = event_data.get("payload", {})
            logger.info(f"Processing prediction completed event: {payload.get('prediction_id')}")

            today = date.today()
            predicted_class = payload.get("predicted_class")
            is_malignant = payload.get("is_malignant", False)
            processing_time = payload.get("processing_time_ms")

            # Update prediction counts
            await self.statistics_service.increment_daily_stat(today, "total_predictions")
            await self.statistics_service.increment_daily_stat(today, "successful_predictions")

            # Update malignant/benign counts
            if is_malignant:
                await self.statistics_service.increment_daily_stat(today, "malignant_count")
            else:
                await self.statistics_service.increment_daily_stat(today, "benign_count")

            # Update disease distribution
            stats = await self.statistics_service.get_or_create_daily_statistics(today)
            distribution = stats.disease_distribution or {}
            distribution[predicted_class] = distribution.get(predicted_class, 0) + 1
            await self.statistics_service.update_daily_statistics(
                today,
                disease_distribution=distribution
            )

            # Update average processing time
            if processing_time and stats.total_predictions > 0:
                current_avg = stats.avg_processing_time_ms or processing_time
                new_avg = (current_avg * (stats.total_predictions - 1) + processing_time) / stats.total_predictions
                await self.statistics_service.update_daily_statistics(
                    today,
                    avg_processing_time_ms=new_avg
                )

        except Exception as e:
            logger.error(f"Error processing prediction completed event: {e}")

    async def process_prediction_feedback(self, event_data: dict) -> None:
        """Process prediction feedback event"""
        try:
            payload = event_data.get("payload", {})
            logger.info(f"Processing prediction feedback event: {payload.get('prediction_id')}")

            today = date.today()
            is_correct = payload.get("is_correct", False)

            await self.statistics_service.increment_daily_stat(today, "feedback_count")

            if is_correct:
                await self.statistics_service.increment_daily_stat(today, "positive_feedback")
            else:
                await self.statistics_service.increment_daily_stat(today, "negative_feedback")

        except Exception as e:
            logger.error(f"Error processing prediction feedback event: {e}")

    async def handle_event(self, event_data: dict) -> None:
        """Route event to appropriate handler"""
        event_type = event_data.get("event_type", "")

        handlers = {
            "user.registered": self.process_user_registered,
            "user.logged_in": self.process_user_logged_in,
            "prediction.created": self.process_prediction_created,
            "prediction.completed": self.process_prediction_completed,
            "prediction.feedback": self.process_prediction_feedback,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")
