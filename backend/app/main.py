import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import health
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, validation_error_handler
from app.core.logging import logger, setup_logging
from app.realtime.subscriber import start_event_subscriber


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} ({settings.APP_ENV})")

    # Start Redis Pub/Sub subscriber task in background
    subscriber_task = asyncio.create_task(start_event_subscriber())

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Real-Time Service Request Management System API",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # Root Level Health Probes
    app.include_router(health.router)

    # API v1 Router
    app.include_router(api_v1_router)

    return app


app = create_app()
