import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_rejects_placeholder_jwt_secret():
    with pytest.raises(ValidationError, match="locally generated"):
        Settings(
            environment="development",
            secret_key="replace-with-a-locally-generated-secret",
        )


def test_production_requires_a_long_generated_jwt_secret():
    with pytest.raises(ValidationError, match="locally generated"):
        Settings(environment="production", secret_key="short-secret")
