import contextvars
import logging
import sys
import uuid
from typing import Optional
from app.core.config import settings

# Context variable storing correlation request ID
correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


class CorrelationIdFilter(logging.Filter):
    """Injects the current request correlation ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = correlation_id_ctx.get() or "-"
        return True


def setup_logging() -> None:
    log_format = (
        "%(asctime)s | %(levelname)-8s | [%(request_id)s] | %(name)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    handler.addFilter(CorrelationIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root_logger.handlers = [handler]

    # Suppress verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


logger = logging.getLogger("serviceflow")

