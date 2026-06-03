from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
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

    storage_backend: Literal["local", "gcs"] = "local"
    upload_dir: str = "uploads"
    gcs_temp_bucket: str = "aed-locator-dev-inbox"
    gcs_images_bucket: str = "aed-locator-dev-aed-images"
    gcs_signed_upload_ttl_seconds: int = 900
    gcs_signed_read_ttl_seconds: int = 3600
    gcs_image_prefix: str = "aed-images"
    image_processor_url: str = ""
    max_image_bytes: int = 10 * 1024 * 1024
    max_images_per_submission: int = 5
    min_images_new_location: int = 1
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    google_maps_api_key: str = ""

    rate_limit_reports: str = "5/minute"
    duplicate_radius_meters: float = 25.0
    min_aed_confidence: float = 0.35

    admin_emails: list[str] = Field(default_factory=list)

    @property
    def allowed_image_mime_types(self) -> set[str]:
        return {item.strip() for item in self.allowed_image_types.split(",") if item.strip()}

    @property
    def uses_gcs_storage(self) -> bool:
        return self.storage_backend == "gcs"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_image_bytes


@lru_cache
def get_settings() -> Settings:
    return Settings()
