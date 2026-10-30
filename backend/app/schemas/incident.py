from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentRead(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
