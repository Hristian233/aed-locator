"""HTTP client for the synchronous image processor Cloud Function."""

from dataclasses import dataclass

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ImageProcessorResult:
    final_object_key: str


class ImageProcessorError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ImageProcessorService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def process_temp_image(
        self,
        *,
        temp_object_key: str,
        content_type: str | None = None,
        content_length: int | None = None,
        final_object_key: str,
    ) -> ImageProcessorResult:
        if not self.settings.image_processor_url:
            raise ImageProcessorError("Image processing is not configured")

        payload = {
            "temp_bucket": self.settings.gcs_temp_bucket,
            "temp_object_key": temp_object_key,
            "final_bucket": self.settings.gcs_images_bucket,
            "final_object_key": final_object_key,
            "content_type": content_type,
            "content_length": content_length,
            "max_bytes": self.settings.max_image_bytes,
            "allowed_content_types": sorted(self.settings.allowed_image_mime_types),
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.settings.image_processor_url,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            logger.warning("image_processor_request_failed", error=str(exc))
            raise ImageProcessorError(
                "Image processing service is unavailable. Please try again."
            ) from exc

        try:
            body = response.json()
        except ValueError as exc:
            logger.warning(
                "image_processor_invalid_response",
                status=response.status_code,
            )
            raise ImageProcessorError(
                "Image processing returned an invalid response."
            ) from exc

        if response.status_code >= 400 or not body.get("success"):
            error = body.get("error") or body.get("detail")
            message = (
                error
                if isinstance(error, str) and error.strip()
                else "Image processing failed. Please upload a valid photo and try again."
            )
            logger.info(
                "image_processor_failed",
                status=response.status_code,
                error=message,
            )
            raise ImageProcessorError(message)

        final_key = body.get("final_object_key")
        if not isinstance(final_key, str) or not final_key.strip():
            raise ImageProcessorError(
                "Image processing succeeded but did not return a final object key."
            )

        return ImageProcessorResult(final_object_key=final_key)
