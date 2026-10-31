from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnomalyDetectionRequest(BaseModel):
    resource_id: UUID


class AnomalyRead(BaseModel):
    id: UUID
    resource_id: UUID
    resource: str
    incident_id: UUID | None
    detected_at: datetime
    anomaly_score: float
    detected_features: dict[str, float]
    severity: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyDetectionResult(BaseModel):
    resource_id: UUID
    prometheus_job: str
    sample_count: int
    lookback_minutes: int
    anomaly_count: int
    incidents_created: int
    anomalies: list[AnomalyRead]
