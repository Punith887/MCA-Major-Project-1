from datetime import datetime

from pydantic import BaseModel, Field


class HostMetricSample(BaseModel):
    timestamp: datetime
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)


class HostMetricsResponse(BaseModel):
    job: str
    lookback_minutes: int
    step_seconds: int
    queried_at: datetime
    samples: list[HostMetricSample]
