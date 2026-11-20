from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
import redis.asyncio as aioredis
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Liveness probe: returns 200 OK if server process is running."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(response: Response) -> ReadinessResponse:
    """Readiness probe: verifies connectivity to PostgreSQL and Redis."""
    deps: dict[str, str] = {}
    is_ready = True

    # 1. Check PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        deps["database"] = "connected"
    except Exception as exc:
        deps["database"] = f"unhealthy ({exc.__class__.__name__})"
        is_ready = False

    # 2. Check Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        await r.ping()
        await r.aclose()
        deps["redis"] = "connected"
    except Exception as exc:
        deps["redis"] = f"unhealthy ({exc.__class__.__name__})"
        is_ready = False

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        dependencies=deps,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
