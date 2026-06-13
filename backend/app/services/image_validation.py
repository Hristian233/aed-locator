"""Shared validation for AED image upload metadata."""

from app.core.config import Settings


class ImageValidationError(ValueError):
    pass


def validate_image_metadata(
    content_type: str,
    content_length: int,
    *,
    settings: Settings,
) -> None:
    if content_type not in settings.allowed_image_mime_types:
        allowed = ", ".join(sorted(settings.allowed_image_mime_types))
        raise ImageValidationError(
            f"Unsupported image type '{content_type}'. Allowed: {allowed}"
        )
    if content_length < 1024:
        raise ImageValidationError("Image file is too small")
    if content_length > settings.max_image_bytes:
        raise ImageValidationError(
            f"Image too large. Maximum size is {settings.max_image_bytes} bytes"
        )
