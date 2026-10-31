from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.infrastructure_resource import ResourceStatus


class ResourceCreate(BaseModel):
    project_id: UUID
    prometheus_job: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")


class ResourceRead(BaseModel):
    id: UUID
    project_id: UUID
    resource_name: str
    resource_type: str
    prometheus_job: str | None
    environment: str
    status: ResourceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
