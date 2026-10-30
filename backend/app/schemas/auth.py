from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator
from typing import Annotated

from app.models.user import UserRole

Password = Annotated[str, StringConstraints(min_length=12, max_length=128)]


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: Password

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Full name must contain at least 2 non-whitespace characters.")
        return normalized


class UserRead(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
