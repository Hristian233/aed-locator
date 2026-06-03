import pytest

from app.core.config import Settings
from app.services.image_validation import ImageValidationError, validate_image_metadata


def test_validate_image_metadata_rejects_unsupported_type() -> None:
    settings = Settings(allowed_image_types="image/jpeg,image/png")

    with pytest.raises(ImageValidationError, match="Unsupported image type"):
        validate_image_metadata("image/gif", 5000, settings=settings)


def test_validate_image_metadata_rejects_oversized_image() -> None:
    settings = Settings(max_image_bytes=10_485_760)

    with pytest.raises(ImageValidationError, match="too large"):
        validate_image_metadata("image/jpeg", 10_485_761, settings=settings)


def test_validate_image_metadata_accepts_allowed_upload() -> None:
    settings = Settings()

    validate_image_metadata("image/png", 2048, settings=settings)
