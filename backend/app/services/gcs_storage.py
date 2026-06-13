import uuid
from datetime import timedelta
from typing import Any

import google.auth
import google.auth.transport.requests
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.image_validation import ImageValidationError, validate_image_metadata

logger = get_logger(__name__)


class GCSStorageError(Exception):
    pass


class GCSStorageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: storage.Client | None = None

    @property
    def client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client()
        return self._client

    def build_temp_object_key(self) -> str:
        return f"{uuid.uuid4().hex}"

    def build_final_object_key(self) -> str:
        return f"{uuid.uuid4().hex}.webp"

    def _cloud_run_signing_kwargs(self) -> dict[str, Any]:
        """Use IAM signBlob when the runtime credentials have no private key (Cloud Run)."""
        credentials, _ = google.auth.default()
        if getattr(credentials, "signer", None) is not None:
            return {}

        credentials.refresh(google.auth.transport.requests.Request())
        service_account_email = getattr(credentials, "service_account_email", None)
        if not service_account_email:
            raise GCSStorageError(
                "Could not determine service account for signed URL generation."
            )

        return {
            "access_token": credentials.token,
            "service_account_email": service_account_email,
        }

    def _generate_signed_url(self, blob: storage.Blob, **kwargs: Any) -> str:
        try:
            return blob.generate_signed_url(
                version="v4",
                **kwargs,
                **self._cloud_run_signing_kwargs(),
            )
        except (GoogleCloudError, AttributeError, ValueError) as exc:
            logger.warning("gcs_signed_url_failed", error=str(exc))
            raise GCSStorageError(
                "Could not prepare image upload. Please try again."
            ) from exc

    def create_signed_upload_url(
        self,
        *,
        content_type: str,
        content_length: int,
    ) -> tuple[str, str, int]:
        validate_image_metadata(
            content_type,
            content_length,
            settings=self.settings,
        )
        object_key = self.build_temp_object_key()
        try:
            bucket = self.client.bucket(self.settings.gcs_temp_bucket)
            blob = bucket.blob(object_key)
            upload_url = self._generate_signed_url(
                blob,
                expiration=timedelta(seconds=self.settings.gcs_signed_upload_ttl_seconds),
                method="PUT",
                content_type=content_type,
            )
        except (GCSStorageError, ImageValidationError) as exc:
            if isinstance(exc, ImageValidationError):
                raise
            raise
        except GoogleCloudError as exc:
            logger.warning("gcs_signed_upload_failed", error=str(exc))
            raise GCSStorageError(
                "Could not prepare image upload. Please try again."
            ) from exc

        return (
            upload_url,
            object_key,
            self.settings.gcs_signed_upload_ttl_seconds,
        )

    def create_signed_read_url(self, object_key: str) -> str | None:
        if not object_key or object_key.startswith("/"):
            return object_key or None
        try:
            bucket = self.client.bucket(self.settings.gcs_images_bucket)
            blob = bucket.blob(object_key)
            return self._generate_signed_url(
                blob,
                expiration=timedelta(seconds=self.settings.gcs_signed_read_ttl_seconds),
                method="GET",
            )
        except GCSStorageError:
            return None
        except GoogleCloudError as exc:
            logger.warning(
                "gcs_signed_read_failed",
                object_key=object_key,
                error=str(exc),
            )
            return None

    async def download_object_bytes(self, bucket_name: str, object_key: str) -> bytes:
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_key)
            return blob.download_as_bytes()
        except GoogleCloudError as exc:
            logger.warning(
                "gcs_download_failed",
                bucket=bucket_name,
                object_key=object_key,
                error=str(exc),
            )
            raise GCSStorageError("Could not read processed image.") from exc
