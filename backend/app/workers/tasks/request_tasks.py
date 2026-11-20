import asyncio
from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.models.service_request import RequestStatus, ServiceRequest
from app.db.session import get_worker_session
from app.realtime.publisher import event_publisher
from app.repositories.service_request_repository import ServiceRequestRepository
from app.workers.celery_app import celery_app

PROCESSING_STEPS = [
    (1, "Step 1: Validating request payload & preconditions", 20),
    (2, "Step 2: Preparing execution environment", 40),
    (3, "Step 3: Executing multi-stage service workload", 60),
    (4, "Step 4: Verifying operational constraints & checksums", 80),
    (5, "Step 5: Finalizing request and committing output", 100),
]


async def run_service_request_pipeline(
    request_id_str: str,
    session: Optional[AsyncSession] = None,
    step_delay: Optional[float] = None,
) -> Optional[ServiceRequest]:
    """Asynchronous worker pipeline executing sequential multi-step request processing."""
    try:
        request_id = uuid.UUID(request_id_str)
    except ValueError:
        logger.error(f"Invalid UUID string passed to worker pipeline: {request_id_str}")
        return None

    delay = step_delay if step_delay is not None else settings.PROCESSING_STEP_DELAY_SECONDS

    async def _execute(db_session: AsyncSession) -> Optional[ServiceRequest]:
        repo = ServiceRequestRepository(db_session)
        sr = await repo.get_by_id(request_id)

        # 1. Verification & Idempotency check
        if sr is None:
            logger.warning(f"Task pipeline aborted: ServiceRequest id={request_id} not found in database.")
            return None

        if sr.status == RequestStatus.CANCELLED:
            logger.info(f"Task pipeline aborted: ServiceRequest id={request_id} was cancelled before worker pickup.")
            return sr

        if sr.status != RequestStatus.QUEUED:
            logger.warning(
                f"Task pipeline skipped: ServiceRequest id={request_id} is in status '{sr.status.value}', expected 'QUEUED'."
            )
            return sr

        # 2. Transition from QUEUED to PROCESSING
        logger.info(f"Starting processing for ServiceRequest id={request_id}")
        sr = await repo.update_progress(
            request_id=request_id,
            progress_percent=0,
            current_step="Starting processing pipeline",
            status=RequestStatus.PROCESSING,
        )

        # Publish status changed event
        await event_publisher.publish_event({
            "event_id": str(uuid.uuid4()),
            "event_type": "service_request.status_changed",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "request_id": str(request_id),
            "data": {
                "status": RequestStatus.PROCESSING.value,
                "progress_percent": 0,
                "current_step": "Starting processing pipeline",
                "created_by_id": str(sr.created_by_id),
                "started_at": sr.started_at.isoformat() if sr.started_at else None,
            },
        })

        # 3. Multi-Step Execution Loop
        try:
            for step_num, step_label, target_progress in PROCESSING_STEPS:
                # Check for cancellation race condition during processing
                check_sr = await repo.get_by_id(request_id)
                if check_sr and check_sr.status == RequestStatus.CANCELLED:
                    logger.info(f"ServiceRequest id={request_id} was cancelled concurrently during step {step_num}.")
                    return check_sr

                # Simulate discrete compute step delay
                if delay > 0:
                    await asyncio.sleep(delay)

                # Update progress and step in database
                sr = await repo.update_progress(
                    request_id=request_id,
                    progress_percent=target_progress,
                    current_step=step_label,
                    status=RequestStatus.PROCESSING if target_progress < 100 else RequestStatus.COMPLETED,
                )

                # Publish step progress event
                if target_progress < 100:
                    await event_publisher.publish_event({
                        "event_id": str(uuid.uuid4()),
                        "event_type": "service_request.progress_updated",
                        "occurred_at": datetime.now(timezone.utc).isoformat(),
                        "request_id": str(request_id),
                        "data": {
                            "status": RequestStatus.PROCESSING.value,
                            "progress_percent": target_progress,
                            "current_step": step_label,
                            "created_by_id": str(sr.created_by_id),
                        },
                    })

            # 4. Final Completion
            logger.info(f"ServiceRequest id={request_id} completed successfully (100%).")
            await event_publisher.publish_event({
                "event_id": str(uuid.uuid4()),
                "event_type": "service_request.completed",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "request_id": str(request_id),
                "data": {
                    "status": RequestStatus.COMPLETED.value,
                    "progress_percent": 100,
                    "current_step": PROCESSING_STEPS[-1][1],
                    "created_by_id": str(sr.created_by_id),
                    "completed_at": sr.completed_at.isoformat() if sr.completed_at else None,
                },
            })
            return sr

        except Exception as step_exc:
            logger.exception(f"Execution error processing ServiceRequest id={request_id}: {step_exc}")
            safe_error_msg = "Workload processing failed during execution step."
            failed_sr = await repo.update_progress(
                request_id=request_id,
                progress_percent=sr.progress_percent if sr else 0,
                current_step="Processing failed",
                status=RequestStatus.FAILED,
                error_message=safe_error_msg,
            )
            await event_publisher.publish_event({
                "event_id": str(uuid.uuid4()),
                "event_type": "service_request.failed",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "request_id": str(request_id),
                "data": {
                    "status": RequestStatus.FAILED.value,
                    "progress_percent": failed_sr.progress_percent,
                    "current_step": "Processing failed",
                    "error_message": safe_error_msg,
                    "created_by_id": str(sr.created_by_id) if sr else None,
                },
            })
            return failed_sr

    if session is not None:
        return await _execute(session)
    else:
        async with get_worker_session() as worker_session:
            return await _execute(worker_session)


@celery_app.task(
    name="serviceflow.process_service_request",
    bind=True,
    acks_late=True,
    max_retries=1,
)
def process_service_request(self, request_id: str) -> None:
    """Celery entrypoint executing the asynchronous service request processing pipeline."""
    logger.info(f"Celery task received for execution: request_id={request_id}")
    asyncio.run(run_service_request_pipeline(request_id))

