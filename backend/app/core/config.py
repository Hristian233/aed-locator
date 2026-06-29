from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
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
    gcs_temp_bucket: str = ""
    gcs_images_bucket: str = ""
    gcs_images_public_url_base: str | None = None
    gcs_signed_upload_ttl_seconds: int = 900
    gcs_signed_read_ttl_seconds: int = 3600
    image_processor_url: str = "https://aed-image-processor-dev-iuhz7yxnaa-uc.a.run.app"
    max_image_bytes: int = 10 * 1024 * 1024
    max_images_per_submission: int = 5
    min_images_new_location: int = 1
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    google_maps_api_key: str = ""

    rate_limit_reports: str = "5/minute"
    duplicate_radius_meters: float = 25.0
    min_aed_confidence: float = 0.35

    admin_emails: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def resolve_gcs_buckets(self) -> Self:
        if not self.gcs_temp_bucket.strip():
            self.gcs_temp_bucket = self._default_gcs_temp_bucket()
        if not self.gcs_images_bucket.strip():
            self.gcs_images_bucket = self._default_gcs_images_bucket()
        if self.gcs_images_public_url_base is None:
            self.gcs_images_public_url_base = (
                f"https://storage.googleapis.com/{self.gcs_images_bucket}"
            )
        return self

    def _gcs_env_suffix(self) -> str:
        return "prod" if self.environment == "production" else "dev"

    def _default_gcs_temp_bucket(self) -> str:
        return f"aed-locator-{self._gcs_env_suffix()}-inbox"

    def _default_gcs_images_bucket(self) -> str:
        return f"aed-locator-{self._gcs_env_suffix()}-aed-images"

    @property
    def allowed_image_mime_types(self) -> set[str]:
        return {item.strip() for item in self.allowed_image_types.split(",") if item.strip()}

    @property
    def uses_gcs_storage(self) -> bool:
        return self.storage_backend == "gcs"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_image_bytes

    @property
    def docs_enabled(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
