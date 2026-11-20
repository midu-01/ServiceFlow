import asyncio
import json
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger
from app.realtime.manager import ws_manager

CHANNEL_NAME = "service_flow:events"


async def start_event_subscriber() -> None:
    """Asynchronous background task listening for Redis Pub/Sub events with automatic reconnection."""
    logger.info("Starting Redis Pub/Sub background subscriber...")
    backoff = 1.0
    max_backoff = 30.0

    while True:
        redis_client = None
        pubsub = None
        try:
            redis_client = aioredis.from_url(settings.REDIS_PUBSUB_URL, socket_timeout=5.0)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(CHANNEL_NAME)
            logger.info(f"Subscribed to Redis channel '{CHANNEL_NAME}'")
            backoff = 1.0  # Reset backoff on successful connection

            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        try:
                            payload = json.loads(message["data"])
                            await ws_manager.broadcast_event(payload)
                        except json.JSONDecodeError as json_err:
                            logger.warning(f"Discarding non-JSON Redis Pub/Sub message: {json_err}")
                except asyncio.CancelledError:
                    raise
                except Exception as msg_err:
                    logger.warning(f"Error reading message from Redis: {msg_err}")
                    await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            logger.info("Redis Pub/Sub subscriber task cancelled. Shutting down cleanly.")
            if pubsub:
                try:
                    await pubsub.unsubscribe(CHANNEL_NAME)
                except Exception:
                    pass
            if redis_client:
                try:
                    await redis_client.aclose()
                except Exception:
                    pass
            break

        except Exception as conn_err:
            logger.debug(f"Redis Pub/Sub subscriber connection issue (retrying in {backoff:.1f}s): {conn_err}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        finally:
            if redis_client:
                try:
                    await redis_client.aclose()
                except Exception:
                    pass

