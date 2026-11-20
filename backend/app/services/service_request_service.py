from datetime import datetime, timezone
import math
from typing import Optional, Sequence, Tuple
import uuid
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.logging import logger
from app.db.models.service_request import RequestStatus, ServiceRequest
from app.db.models.user import User, UserRole
from app.realtime.publisher import event_publisher
from app.repositories.service_request_repository import ServiceRequestRepository
from app.schemas.service_request import ServiceRequestCreate


class ServiceRequestService:
    """Service orchestrating business rules, authorization scoping, and lifecycle transitions."""

    def __init__(self, sr_repo: ServiceRequestRepository) -> None:
        self.sr_repo = sr_repo

    async def create_request(
        self,
        payload: ServiceRequestCreate,
        creator: User,
    ) -> ServiceRequest:
        """Creates and commits a new service request, then enqueues background processing."""
        sr = ServiceRequest(
            title=payload.title,
            description=payload.description,
            created_by_id=creator.id,
            status=RequestStatus.QUEUED,
            progress_percent=0,
        )
        self.sr_repo.add(sr)
        await self.sr_repo.commit()
        await self.sr_repo.refresh(sr)

        # Dispatch Celery background task
        try:
            from app.workers.tasks.request_tasks import process_service_request
            process_service_request.delay(request_id=str(sr.id))
            logger.info(f"Dispatched Celery task for service request id={sr.id}")
        except Exception as exc:
            # If Celery broker is temporarily offline during unit test or dev, log warning gracefully
            logger.warning(f"Could not dispatch Celery task for id={sr.id}: {exc}")

        # Publish WebSocket event
        event_envelope = {
            "event_id": str(uuid.uuid4()),
            "event_type": "service_request.created",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "request_id": str(sr.id),
            "data": {
                "title": sr.title,
                "status": sr.status.value,
                "progress_percent": sr.progress_percent,
                "created_by_id": str(sr.created_by_id),
                "created_at": sr.created_at.isoformat(),
            },
        }
        await event_publisher.publish_event(event_envelope)

        return sr

    async def list_requests(
        self,
        current_user: User,
        status: Optional[RequestStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[ServiceRequest], int]:
        """Lists service requests with role-based scoping."""
        # Operators see only their own requests; Supervisors and Admins see all
        created_by_id: Optional[uuid.UUID] = None
        if current_user.role == UserRole.OPERATOR:
            created_by_id = current_user.id

        return await self.sr_repo.list_filtered(
            created_by_id=created_by_id,
            status=status,
            search=search,
            skip=skip,
            limit=limit,
        )

    async def get_request_by_id(
        self,
        request_id: uuid.UUID,
        current_user: User,
    ) -> ServiceRequest:
        """Retrieves request details with ownership and supervisor authorization checks."""
        sr = await self.sr_repo.get_by_id(request_id)
        if sr is None:
            raise NotFoundError(message=f"Service request with id {request_id} not found")

        # Enforce operator ownership boundary
        if current_user.role == UserRole.OPERATOR and sr.created_by_id != current_user.id:
            raise ForbiddenError(message="You do not have permission to access this service request")

        return sr

    async def cancel_request(
        self,
        request_id: uuid.UUID,
        current_user: User,
    ) -> ServiceRequest:
        """Atomically cancels a service request if it is still in QUEUED state."""
        # 1. Existence and ownership check
        sr = await self.get_request_by_id(request_id, current_user)

        # 2. Check current status
        if sr.status != RequestStatus.QUEUED:
            raise ConflictError(
                message=f"Request is in {sr.status.value} state and cannot be cancelled. Only QUEUED requests can be cancelled."
            )

        # 3. Perform atomic update in DB
        owner_filter = current_user.id if current_user.role == UserRole.OPERATOR else None
        cancelled = await self.sr_repo.atomic_cancel(request_id=request_id, created_by_id=owner_filter)
        if not cancelled:
            raise ConflictError(message="Request status changed concurrently and is no longer cancellable")

        # 4. Refresh entity state
        updated_sr = await self.sr_repo.get_by_id(request_id)

        # 5. Publish real-time cancellation event
        event_envelope = {
            "event_id": str(uuid.uuid4()),
            "event_type": "service_request.cancelled",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "request_id": str(request_id),
            "data": {
                "status": RequestStatus.CANCELLED.value,
                "progress_percent": 0,
                "cancelled_at": updated_sr.cancelled_at.isoformat() if updated_sr.cancelled_at else None,
            },
        }
        await event_publisher.publish_event(event_envelope)

        return updated_sr
