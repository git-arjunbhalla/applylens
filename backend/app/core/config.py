from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ApplyLens"
    environment: str = "development"
    debug: bool = True

    # Async SQLAlchemy URL. Example:
    # postgresql+asyncpg://postgres:postgres@localhost:5432/applylens
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/applylens"

    # Comma-separated list of allowed frontend origins.
    cors_origins: str = "http://localhost:5173"

    # JWT signing secret. Override this in every real environment.
    jwt_secret: str = "dev-only-change-me-use-32-plus-bytes"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # AI provider is backend-only. Never expose the key to the frontend.
    ai_provider: str = "gemini"
    ai_api_key: SecretStr = SecretStr("")
    ai_model: str = "gemini-2.5-flash"
    ai_timeout_seconds: float = 30.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ai_api_key_value(self) -> str:
        return self.ai_api_key.get_secret_value().strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
