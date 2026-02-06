"""
RabbitMQ client for inter-service communication
"""
import json
import asyncio
import logging
from typing import Any, Callable, Optional
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import Message, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractChannel, AbstractExchange

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Async RabbitMQ client for publishing and consuming messages"""

    def __init__(self, url: str):
        self.url = url
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._exchanges: dict[str, AbstractExchange] = {}

    async def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            self._connection = await aio_pika.connect_robust(self.url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ"""
        if self._connection:
            await self._connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def get_exchange(
        self,
        name: str,
        exchange_type: ExchangeType = ExchangeType.TOPIC
    ) -> AbstractExchange:
        """Get or create an exchange"""
        if name not in self._exchanges:
            if not self._channel:
                await self.connect()
            self._exchanges[name] = await self._channel.declare_exchange(
                name,
                exchange_type,
                durable=True
            )
        return self._exchanges[name]

    async def publish(
        self,
        exchange_name: str,
        routing_key: str,
        message: dict,
        correlation_id: Optional[str] = None
    ) -> None:
        """Publish a message to an exchange"""
        try:
            exchange = await self.get_exchange(exchange_name)

            msg = Message(
                body=json.dumps(message, default=str).encode(),
                content_type="application/json",
                correlation_id=correlation_id
            )

            await exchange.publish(msg, routing_key=routing_key)
            logger.debug(f"Published message to {exchange_name}/{routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def create_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_keys: list[str],
        durable: bool = True
    ) -> aio_pika.abc.AbstractQueue:
        """Create a queue and bind it to an exchange"""
        if not self._channel:
            await self.connect()

        exchange = await self.get_exchange(exchange_name)
        queue = await self._channel.declare_queue(queue_name, durable=durable)

        for routing_key in routing_keys:
            await queue.bind(exchange, routing_key=routing_key)

        return queue

    async def consume(
        self,
        queue_name: str,
        callback: Callable[[dict], Any],
        exchange_name: Optional[str] = None,
        routing_keys: Optional[list[str]] = None
    ) -> None:
        """Start consuming messages from a queue"""
        if not self._channel:
            await self.connect()

        # Create and bind queue if exchange info provided
        if exchange_name and routing_keys:
            queue = await self.create_queue(queue_name, exchange_name, routing_keys)
        else:
            queue = await self._channel.declare_queue(queue_name, durable=True)

        async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    raise

        await queue.consume(process_message)
        logger.info(f"Started consuming from queue: {queue_name}")

    @asynccontextmanager
    async def session(self):
        """Context manager for RabbitMQ session"""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()


# Singleton instance factory
_clients: dict[str, RabbitMQClient] = {}


def get_rabbitmq_client(url: str) -> RabbitMQClient:
    """Get or create a RabbitMQ client instance"""
    if url not in _clients:
        _clients[url] = RabbitMQClient(url)
    return _clients[url]
