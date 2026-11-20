from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.db.models.service_request import RequestStatus


class ServiceRequestCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=100,
        description="Concise service request title (3-100 characters)",
        examples=["Customer Data Sync Pipeline"],
    )
    description: str = Field(
        min_length=10,
        max_length=1000,
        description="Detailed service request description (10-1000 characters)",
        examples=["Trigger full synchronization of customer orders and billing history across secondary systems."],
    )


class ServiceRequestResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: RequestStatus
    progress_percent: int
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestCancelResponse(BaseModel):
    id: uuid.UUID
    status: RequestStatus
    progress_percent: int
    cancelled_at: Optional[datetime]
    message: str
