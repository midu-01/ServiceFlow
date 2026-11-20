from app.core.logging import logger
from app.workers.celery_app import celery_app


@celery_app.task(name="serviceflow.process_service_request", acks_late=True)
def process_service_request(request_id: str) -> None:
    """Celery background task processing a service request asynchronously."""
    logger.info(f"Celery worker received service request task: request_id={request_id}")
    # Full multi-step simulation is implemented in Phase 10
