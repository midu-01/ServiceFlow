from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple
import uuid
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.service_request import RequestStatus, ServiceRequest
from app.repositories.base_repository import BaseRepository


class ServiceRequestRepository(BaseRepository[ServiceRequest]):
    """Repository handling persistence operations for ServiceRequest entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ServiceRequest, session)

    async def list_filtered(
        self,
        created_by_id: Optional[uuid.UUID] = None,
        status: Optional[RequestStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[ServiceRequest], int]:
        """Query requests with role scoping, status filtering, and search text."""
        base_query = select(ServiceRequest)
        count_query = select(func.count(ServiceRequest.id))

        filters = []
        if created_by_id is not None:
            filters.append(ServiceRequest.created_by_id == created_by_id)
        if status is not None:
            filters.append(ServiceRequest.status == status)
        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    ServiceRequest.title.ilike(search_pattern),
                    ServiceRequest.description.ilike(search_pattern),
                )
            )

        if filters:
            base_query = base_query.where(*filters)
            count_query = count_query.where(*filters)

        # Count total matching rows
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Fetch paginated slice ordered by created_at DESC
        paginated_query = (
            base_query.order_by(ServiceRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(paginated_query)
        items = result.scalars().all()

        return items, total

    async def atomic_cancel(
        self,
        request_id: uuid.UUID,
        created_by_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Atomically transitions status to CANCELLED only if currently QUEUED.
        
        Returns True if cancellation succeeded, False if state was not QUEUED or row not found.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(ServiceRequest)
            .where(
                ServiceRequest.id == request_id,
                ServiceRequest.status == RequestStatus.QUEUED,
            )
            .values(
                status=RequestStatus.CANCELLED,
                cancelled_at=now,
                updated_at=now,
            )
        )

        if created_by_id is not None:
            stmt = stmt.where(ServiceRequest.created_by_id == created_by_id)

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def update_progress(
        self,
        request_id: uuid.UUID,
        progress_percent: int,
        current_step: Optional[str] = None,
        status: Optional[RequestStatus] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ServiceRequest]:
        """Updates progress, current step, and status for a service request."""
        now = datetime.now(timezone.utc)
        values: dict = {
            "progress_percent": progress_percent,
            "updated_at": now,
        }
        if current_step is not None:
            values["current_step"] = current_step
        if status is not None:
            values["status"] = status
            if status == RequestStatus.PROCESSING and values.get("started_at") is None:
                values["started_at"] = now
            elif status == RequestStatus.COMPLETED:
                values["completed_at"] = now
            elif status == RequestStatus.FAILED:
                values["completed_at"] = now
        if error_message is not None:
            values["error_message"] = error_message

        stmt = (
            update(ServiceRequest)
            .where(ServiceRequest.id == request_id)
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_by_id(request_id)
