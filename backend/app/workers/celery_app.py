from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "serviceflow_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
)

celery_app.autodiscover_tasks(["app.workers.tasks"])
