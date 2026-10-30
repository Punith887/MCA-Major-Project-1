from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DeploymentRead(BaseModel):
    id: UUID
    project_id: UUID
    version: str
    environment: str
    status: str
    deployed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
