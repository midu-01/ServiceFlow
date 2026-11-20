from functools import lru_cache
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "ServiceFlow"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Security & Tokens
    APP_SECRET_KEY: str = "dev-insecure-app-secret-key-change-in-production-32chars"
    JWT_SECRET_KEY: str = "dev-insecure-jwt-secret-key-change-in-production-32chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_MINUTES: int = 30

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/serviceflow"

    # Redis & Broker
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    REDIS_PUBSUB_URL: str = "redis://localhost:6379/1"

    # Concurrency & Workflows
    CELERY_WORKER_CONCURRENCY: int = 4
    PROCESSING_STEP_DELAY_SECONDS: float = 2.0

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if self.APP_ENV.lower() in ("production", "prod"):
            if "dev-insecure" in self.APP_SECRET_KEY or len(self.APP_SECRET_KEY) < 32:
                raise ValueError("APP_SECRET_KEY must be a secure key with at least 32 characters in production.")
            if "dev-insecure" in self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY must be a secure key with at least 32 characters in production.")
            if self.DEBUG:
                raise ValueError("DEBUG must be disabled in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
