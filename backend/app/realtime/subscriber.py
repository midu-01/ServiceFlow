import asyncio
import json
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger
from app.realtime.manager import ws_manager

CHANNEL_NAME = "service_flow:events"


async def start_event_subscriber() -> None:
    """Asynchronous background task listening for Redis Pub/Sub events."""
    logger.info("Starting Redis Pub/Sub background subscriber...")
    try:
        redis_client = aioredis.from_url(settings.REDIS_PUBSUB_URL)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(CHANNEL_NAME)

        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    payload = json.loads(message["data"])
                    await ws_manager.broadcast_json(payload)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"Error processing pubsub message: {exc}")
                await asyncio.sleep(1.0)

        await pubsub.unsubscribe(CHANNEL_NAME)
        await redis_client.aclose()
    except Exception as exc:
        logger.error(f"Redis Pub/Sub subscriber encountered error: {exc}")
