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
    prometheus_url: str = "http://localhost:9090"
    anomaly_lookback_minutes: int = Field(default=60, ge=15, le=1440)
    anomaly_minimum_samples: int = Field(default=30, ge=10, le=10000)
    anomaly_contamination: float = Field(default=0.05, gt=0, lt=0.5)
    anomaly_severity_medium_cpu_cores: float = Field(default=0.5, gt=0, allow_inf_nan=False)
    anomaly_severity_high_cpu_cores: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    anomaly_severity_critical_cpu_cores: float = Field(default=2.0, gt=0, allow_inf_nan=False)
    anomaly_severity_medium_memory_bytes: float = Field(
        default=536_870_912, gt=0, allow_inf_nan=False
    )
    anomaly_severity_high_memory_bytes: float = Field(
        default=1_073_741_824, gt=0, allow_inf_nan=False
    )
    anomaly_severity_critical_memory_bytes: float = Field(
        default=2_147_483_648, gt=0, allow_inf_nan=False
    )
    anomaly_severity_medium_error_rate: float = Field(
        default=0.1, gt=0, allow_inf_nan=False
    )
    anomaly_severity_high_error_rate: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    anomaly_severity_critical_error_rate: float = Field(default=5.0, gt=0, allow_inf_nan=False)
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
        for metric in ("cpu_cores", "memory_bytes", "error_rate"):
            thresholds = (
                getattr(self, f"anomaly_severity_medium_{metric}"),
                getattr(self, f"anomaly_severity_high_{metric}"),
                getattr(self, f"anomaly_severity_critical_{metric}"),
            )
            if not thresholds[0] < thresholds[1] < thresholds[2]:
                raise ValueError(
                    f"Anomaly severity thresholds for {metric} must increase "
                    "from medium to critical."
                )

        secret = self.secret_key.get_secret_value()
        if self.environment.lower() == "test" and not secret:
            self.secret_key = SecretStr("test-only-secret-key-not-for-production")
        elif len(secret) < 32 or secret.lower().startswith("replace-with-"):
            raise ValueError("Set SECRET_KEY to a locally generated value of at least 32 characters.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
