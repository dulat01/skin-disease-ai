"""
Event Publisher for Auth Service
"""
import logging
from typing import Optional
from datetime import datetime

from app.config import settings
from app.models.user import User

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
    # Fallback for local development
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
    """Publishes auth events to RabbitMQ"""

    def __init__(self):
        self.exchange_name = EXCHANGES["auth"]
        self._client = None

    async def _get_client(self):
        """Get or create RabbitMQ client"""
        if not self._client:
            self._client = get_rabbitmq_client(settings.RABBITMQ_URL)
            await self._client.connect()
        return self._client

    async def publish_user_registered(self, user: User) -> None:
        """Publish user registered event"""
        try:
            client = await self._get_client()

            event_data = {
                "event_type": EventType.USER_REGISTERED.value,
                "source_service": settings.SERVICE_NAME,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "user_id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat(),
                }
            }

            await client.publish(
                self.exchange_name,
                ROUTING_KEYS[EventType.USER_REGISTERED],
                event_data
            )
            logger.info(f"Published user registered event for {user.email}")
        except Exception as e:
            logger.error(f"Failed to publish user registered event: {e}")

    async def publish_user_logged_in(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Publish user logged in event"""
        try:
            client = await self._get_client()

            event_data = {
                "event_type": EventType.USER_LOGGED_IN.value,
                "source_service": settings.SERVICE_NAME,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "user_id": str(user.id),
                    "email": user.email,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                }
            }

            await client.publish(
                self.exchange_name,
                ROUTING_KEYS[EventType.USER_LOGGED_IN],
                event_data
            )
            logger.info(f"Published user logged in event for {user.email}")
        except Exception as e:
            logger.error(f"Failed to publish user logged in event: {e}")

    async def publish_user_logged_out(self, user_id: str) -> None:
        """Publish user logged out event"""
        try:
            client = await self._get_client()

            event_data = {
                "event_type": EventType.USER_LOGGED_OUT.value,
                "source_service": settings.SERVICE_NAME,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "user_id": user_id,
                }
            }

            await client.publish(
                self.exchange_name,
                ROUTING_KEYS[EventType.USER_LOGGED_OUT],
                event_data
            )
            logger.info(f"Published user logged out event for {user_id}")
        except Exception as e:
            logger.error(f"Failed to publish user logged out event: {e}")
