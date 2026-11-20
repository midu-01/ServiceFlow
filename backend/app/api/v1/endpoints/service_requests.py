from uuid import UUID
from fastapi import APIRouter, status
from app.schemas.common import DataResponse

router = APIRouter(prefix="/service-requests", tags=["Service Requests"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_service_request() -> DataResponse[dict]:
    """Placeholder for service request creation (Implemented in Phase 9)."""
    return DataResponse(data={"message": "Service request creation scaffolded"})


@router.get("")
async def list_service_requests() -> DataResponse[dict]:
    """Placeholder for service request listing (Implemented in Phase 9)."""
    return DataResponse(data={"message": "Service request list scaffolded"})


@router.get("/{request_id}")
async def get_service_request(request_id: UUID) -> DataResponse[dict]:
    """Placeholder for service request detail (Implemented in Phase 9)."""
    return DataResponse(data={"request_id": str(request_id), "message": "Service request detail scaffolded"})


@router.post("/{request_id}/cancel")
async def cancel_service_request(request_id: UUID) -> DataResponse[dict]:
    """Placeholder for service request cancellation (Implemented in Phase 9)."""
    return DataResponse(data={"request_id": str(request_id), "message": "Service request cancellation scaffolded"})
