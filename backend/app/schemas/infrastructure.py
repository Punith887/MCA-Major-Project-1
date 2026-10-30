from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.infrastructure_resource import ResourceStatus


class ResourceRead(BaseModel):
    id: UUID
    project_id: UUID
    resource_name: str
    resource_type: str
    environment: str
    status: ResourceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
