from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AIOps Intelligence Platform"
    environment: str = "development"
    database_url: str = "sqlite:///./aiops_dev.db"
    secret_key: SecretStr = SecretStr("")
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_secret(self) -> "Settings":
        secret = self.secret_key.get_secret_value()
        if self.environment.lower() == "test" and not secret:
            self.secret_key = SecretStr("test-only-secret-key-not-for-production")
        elif len(secret) < 32 or secret.lower().startswith("replace-with-"):
            raise ValueError("Set SECRET_KEY to a locally generated value of at least 32 characters.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
