import json
from typing import Any, Dict
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger

CHANNEL_NAME = "service_flow:events"


class EventPublisher:
    """Publishes domain events to Redis Pub/Sub."""

    def __init__(self) -> None:
        self.redis_url = settings.REDIS_PUBSUB_URL

    async def publish_event(self, event_envelope: Dict[str, Any]) -> None:
        try:
            client = aioredis.from_url(self.redis_url, socket_timeout=1.0)
            await client.publish(CHANNEL_NAME, json.dumps(event_envelope))
            await client.aclose()
        except Exception as exc:
            logger.debug(f"Redis event publication skipped (broker offline or timeout): {exc}")


event_publisher = EventPublisher()
