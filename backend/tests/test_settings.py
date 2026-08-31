import pytest
from pydantic import ValidationError

from app.core.config import DEV_JWT_SECRET, Settings


def test_development_allows_default_jwt_secret() -> None:
    settings = Settings(environment="development", jwt_secret=DEV_JWT_SECRET)

    assert settings.environment == "development"
    assert settings.jwt_secret == DEV_JWT_SECRET


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret=DEV_JWT_SECRET)


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret="too-short-to-be-production")


def test_production_accepts_unique_jwt_secret() -> None:
    secret = "production-jwt-secret-must-be-32b+"
    settings = Settings(environment="production", jwt_secret=secret)

    assert settings.environment == "production"
    assert settings.jwt_secret == secret
