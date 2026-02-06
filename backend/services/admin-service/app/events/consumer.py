"""
Event Consumer for Admin Service
"""
import logging
import asyncio

from app.config import settings
from app.database import async_session_maker
from app.services.statistics import StatisticsService
from app.services.aggregator import EventAggregator

# Import shared utilities
import sys
sys.path.append('/app')
try:
    from shared.utils.rabbitmq import get_rabbitmq_client
    from shared.schemas.events import EXCHANGES, QUEUES
except ImportError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))
    from shared.utils.rabbitmq import get_rabbitmq_client
    from shared.schemas.events import EXCHANGES, QUEUES

logger = logging.getLogger(__name__)


class EventConsumer:
    """Consumes events from RabbitMQ for statistics aggregation"""

    def __init__(self):
        self._client = None
        self._running = False

    async def start(self):
        """Start consuming events"""
        self._running = True
        self._client = get_rabbitmq_client(settings.RABBITMQ_URL)

        try:
            await self._client.connect()
            logger.info("Connected to RabbitMQ")

            # Start consuming from statistics aggregator queue
            await self._client.consume(
                queue_name=QUEUES["statistics_aggregator"],
                callback=self._handle_message,
                exchange_name=EXCHANGES["auth"],
                routing_keys=["user.registered", "user.logged_in"]
            )

            # Also consume prediction events
            await self._client.consume(
                queue_name=f"{QUEUES['statistics_aggregator']}_predictions",
                callback=self._handle_message,
                exchange_name=EXCHANGES["prediction"],
                routing_keys=["prediction.created", "prediction.completed", "prediction.feedback"]
            )

            logger.info("Started consuming events")

            # Keep running
            while self._running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in event consumer: {e}")
            raise
        finally:
            if self._client:
                await self._client.disconnect()

    async def stop(self):
        """Stop consuming events"""
        self._running = False

    async def _handle_message(self, event_data: dict):
        """Handle incoming event message"""
        try:
            logger.debug(f"Received event: {event_data.get('event_type')}")

            # Create new database session for this event
            async with async_session_maker() as session:
                try:
                    stats_service = StatisticsService(session)
                    aggregator = EventAggregator(stats_service)

                    await aggregator.handle_event(event_data)
                    await session.commit()

                except Exception as e:
                    await session.rollback()
                    raise

        except Exception as e:
            logger.error(f"Error handling event: {e}")


# Global consumer instance
_consumer: EventConsumer = None


async def start_event_consumer():
    """Start the global event consumer"""
    global _consumer
    if _consumer is None:
        _consumer = EventConsumer()
        asyncio.create_task(_consumer.start())


async def stop_event_consumer():
    """Stop the global event consumer"""
    global _consumer
    if _consumer:
        await _consumer.stop()
        _consumer = None
