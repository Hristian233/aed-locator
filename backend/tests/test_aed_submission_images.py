from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.aed import ReportType, VerificationStatus
from app.repositories.aed_repository import AEDRepository
from app.schemas.aed import AEDCreate
from app.services.aed_service import AEDService
from app.services.image_processor import ImageProcessorError, ImageProcessorResult


def _created_aed(image_key: str) -> MagicMock:
    aed = MagicMock()
    aed.id = 42
    aed.latitude = 42.6977
    aed.longitude = 23.3219
    aed.address = None
    aed.description = None
    aed.image_url = image_key
    aed.verification_status = VerificationStatus.pending
    aed.accessibility_type.value = "24_7"
    aed.opening_hours = None
    aed.report_type = ReportType.new_location
    aed.contact_email = None
    aed.related_aed_id = None
    aed.ai_confidence = 0.8
    aed.created_at = aed.updated_at = MagicMock()
    return aed


@pytest.mark.asyncio
async def test_submit_aed_stores_final_object_key_after_processor_success(gcs_settings) -> None:
    repo = MagicMock(spec=AEDRepository)
    repo.find_duplicate_nearby = AsyncMock(return_value=None)
    repo.create = AsyncMock(side_effect=lambda aed: _created_aed(aed.image_url))

    storage = MagicMock()
    storage.build_final_object_key.return_value = "aed-images/final.webp"
    storage.resolve_display_url.return_value = "https://signed.example/final.webp"
    storage.load_image_bytes = AsyncMock(return_value=b"webp-bytes")

    processor = MagicMock()
    processor.process_temp_image = AsyncMock(
        return_value=ImageProcessorResult(final_object_key="aed-images/final.webp")
    )

    service = AEDService(repo, storage=storage, ai=MagicMock(), image_processor=processor)
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)
    service.ai.analyze_image.return_value = MagicMock(likely_aed=True, confidence=0.8)

    result = await service.submit_aed(
        AEDCreate(latitude=42.6977, longitude=23.3219, report_type="new_location"),
        submitter=None,
        image_temp_object_key="inbox/temp123",
        image_content_type="image/jpeg",
        image_content_length=5000,
    )

    created = repo.create.await_args.args[0]
    assert created.image_url == "aed-images/final.webp"
    assert result.aed.image_url == "https://signed.example/final.webp"
    processor.process_temp_image.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_aed_does_not_persist_when_processor_fails(gcs_settings) -> None:
    repo = MagicMock(spec=AEDRepository)
    repo.find_duplicate_nearby = AsyncMock(return_value=None)
    repo.create = AsyncMock()

    storage = MagicMock()
    storage.build_final_object_key.return_value = "aed-images/final.webp"

    processor = MagicMock()
    processor.process_temp_image = AsyncMock(
        side_effect=ImageProcessorError("Image processing failed")
    )

    service = AEDService(repo, storage=storage, ai=MagicMock(), image_processor=processor)
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)

    with pytest.raises(ValueError, match="Image processing failed"):
        await service.submit_aed(
            AEDCreate(latitude=42.6977, longitude=23.3219, report_type="new_location"),
            submitter=None,
            image_temp_object_key="inbox/temp123",
        )

    repo.create.assert_not_awaited()
