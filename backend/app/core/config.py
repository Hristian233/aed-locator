from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AED Locator API"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://aed:aed@localhost:5432/aed_locator",
        description="Async SQLAlchemy database URL",
    )

    secret_key: str = Field(default="change-me-in-production-use-secrets-manager")
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    upload_dir: str = "uploads"
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_image_types: set[str] = {"image/jpeg", "image/png", "image/webp"}

    maps_provider: Literal["google", "mapbox", "osm"] = "osm"
    google_maps_api_key: str = ""
    mapbox_access_token: str = ""

    rate_limit_reports: str = "5/minute"
    duplicate_radius_meters: float = 25.0
    min_aed_confidence: float = 0.35

    admin_emails: list[str] = Field(default_factory=list)


@lru_cache
def get_settings() -> Settings:
    return Settings()
