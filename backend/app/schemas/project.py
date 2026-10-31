from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Project name cannot be blank.")
        return normalized


class ProjectRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    environment: str
    owner_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
