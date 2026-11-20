import math
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Query, Response, status

from app.db.models.service_request import RequestStatus
from app.dependencies import CurrentUserDep, DbDep
from app.repositories.service_request_repository import ServiceRequestRepository
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.service_request import (
    ServiceRequestCancelResponse,
    ServiceRequestCreate,
    ServiceRequestResponse,
)
from app.services.service_request_service import ServiceRequestService

router = APIRouter(prefix="/service-requests", tags=["Service Requests"])


@router.post(
    "",
    response_model=DataResponse[ServiceRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create and enqueue a new service request",
)
async def create_service_request(
    payload: ServiceRequestCreate,
    response: Response,
    current_user: CurrentUserDep,
    db: DbDep,
) -> DataResponse[ServiceRequestResponse]:
    """Submits a new service request and enqueues background processing."""
    repo = ServiceRequestRepository(db)
    service = ServiceRequestService(repo)

    created_sr = await service.create_request(payload, current_user)
    response.headers["Location"] = f"/api/v1/service-requests/{created_sr.id}"

    return DataResponse(
        data=ServiceRequestResponse.model_validate(created_sr)
    )


@router.get(
    "",
    response_model=PaginatedResponse[ServiceRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="List service requests with role scoping and filters",
)
async def list_service_requests(
    current_user: CurrentUserDep,
    db: DbDep,
    status_filter: Optional[RequestStatus] = Query(None, alias="status", description="Filter by lifecycle status"),
    search: Optional[str] = Query(None, description="Search query matching title or description"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> PaginatedResponse[ServiceRequestResponse]:
    """Lists requests with role-based scoping (Operators see only their own; Supervisors/Admins see all)."""
    repo = ServiceRequestRepository(db)
    service = ServiceRequestService(repo)

    items, total = await service.list_requests(
        current_user=current_user,
        status=status_filter,
        search=search,
        skip=offset,
        limit=limit,
    )

    total_pages = math.ceil(total / limit) if total > 0 else 0
    current_page = (offset // limit) + 1 if limit > 0 else 1

    return PaginatedResponse(
        data=[ServiceRequestResponse.model_validate(item) for item in items],
        meta=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            total_pages=total_pages,
            current_page=current_page,
        ),
    )


@router.get(
    "/{request_id}",
    response_model=DataResponse[ServiceRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get service request details",
)
async def get_service_request(
    request_id: UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> DataResponse[ServiceRequestResponse]:
    """Retrieves full details of a specific service request with ownership checks."""
    repo = ServiceRequestRepository(db)
    service = ServiceRequestService(repo)

    sr = await service.get_request_by_id(request_id, current_user)
    return DataResponse(
        data=ServiceRequestResponse.model_validate(sr)
    )


@router.post(
    "/{request_id}/cancel",
    response_model=DataResponse[ServiceRequestCancelResponse],
    status_code=status.HTTP_200_OK,
    summary="Cancel a queued service request",
)
async def cancel_service_request(
    request_id: UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> DataResponse[ServiceRequestCancelResponse]:
    """Atomically cancels a service request if it is still in QUEUED status."""
    repo = ServiceRequestRepository(db)
    service = ServiceRequestService(repo)

    cancelled_sr = await service.cancel_request(request_id, current_user)
    return DataResponse(
        data=ServiceRequestCancelResponse(
            id=cancelled_sr.id,
            status=cancelled_sr.status,
            progress_percent=cancelled_sr.progress_percent,
            cancelled_at=cancelled_sr.cancelled_at,
            message="Service request cancelled successfully",
        )
    )
