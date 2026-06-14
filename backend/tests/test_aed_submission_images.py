from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.models.aed import ReportType, VerificationStatus
from app.repositories.aed_repository import AEDRepository
from app.schemas.aed import AEDCreate, TempImageUploadMeta
from app.core.api_errors import ApiValidationError
from app.core.upload_limits import ImageTooManyError
from app.services.aed_service import AEDService
from app.services.image_processor import ImageProcessorError, ImageProcessorResult


def _created_aed(image_keys: list[str]) -> MagicMock:
    aed = MagicMock()
    aed.id = 42
    aed.latitude = 42.6977
    aed.longitude = 23.3219
    aed.address = None
    aed.location_name = None
    aed.is_restricted_access = False
    aed.description = None
    aed.image_url = image_keys[0] if image_keys else None
    aed.image_object_keys = '["' + '","'.join(image_keys) + '"]' if image_keys else None
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
async def test_submit_aed_stores_multiple_final_object_keys(gcs_settings) -> None:
    repo = MagicMock(spec=AEDRepository)
    repo.find_duplicate_nearby = AsyncMock(return_value=None)
    repo.create = AsyncMock(
        side_effect=lambda aed: _created_aed(
            __import__("json").loads(aed.image_object_keys or "[]")
        )
    )

    storage = MagicMock()
    storage.build_final_object_key.side_effect = [
        "aed-images/one.webp",
        "aed-images/two.webp",
    ]
    storage.resolve_display_url.side_effect = lambda key: f"https://signed.example/{key}"
    storage.load_image_bytes = AsyncMock(return_value=b"webp-bytes")

    processor = MagicMock()
    processor.process_temp_image = AsyncMock(
        side_effect=[
            ImageProcessorResult(final_object_key="aed-images/one.webp"),
            ImageProcessorResult(final_object_key="aed-images/two.webp"),
        ]
    )

    service = AEDService(repo, storage=storage, ai=MagicMock(), image_processor=processor)
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)
    service.ai.analyze_image.return_value = MagicMock(likely_aed=True, confidence=0.8)

    result = await service.submit_aed(
        AEDCreate(latitude=42.6977, longitude=23.3219, report_type="new_location"),
        submitter=None,
        temp_images=[
            TempImageUploadMeta(
                temp_object_key="inbox/temp1",
                content_type="image/jpeg",
                content_length=5000,
            ),
            TempImageUploadMeta(
                temp_object_key="inbox/temp2",
                content_type="image/png",
                content_length=6000,
            ),
        ],
    )

    created = repo.create.await_args.args[0]
    assert created.image_url == "aed-images/one.webp"
    assert __import__("json").loads(created.image_object_keys) == [
        "aed-images/one.webp",
        "aed-images/two.webp",
    ]
    assert result.aed.image_urls == [
        "https://signed.example/aed-images/one.webp",
        "https://signed.example/aed-images/two.webp",
    ]
    assert processor.process_temp_image.await_count == 2


@pytest.mark.asyncio
async def test_submit_aed_rejects_too_many_images(gcs_settings) -> None:
    repo = MagicMock(spec=AEDRepository)
    storage = MagicMock()
    processor = MagicMock()
    service = AEDService(repo, storage=storage, ai=MagicMock(), image_processor=processor)
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)

    temp_images = [
        TempImageUploadMeta(temp_object_key=f"inbox/temp{i}") for i in range(6)
    ]

    with pytest.raises(ImageTooManyError, match="At most 5"):
        await service.submit_aed(
            AEDCreate(latitude=42.6977, longitude=23.3219, report_type="new_location"),
            submitter=None,
            temp_images=temp_images,
        )

    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_submit_aed_requires_at_least_one_image_for_new_location() -> None:
    repo = MagicMock(spec=AEDRepository)
    service = AEDService(repo, storage=MagicMock(), ai=MagicMock(), image_processor=MagicMock())
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)

    with pytest.raises(ApiValidationError, match="image_required"):
        await service.submit_aed(
            AEDCreate(latitude=42.6977, longitude=23.3219, report_type="new_location"),
            submitter=None,
        )


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

    with pytest.raises(ApiValidationError) as exc_info:
        await service.submit_aed(
            AEDCreate(latitude=42.6977, longitude=23.3219, report_type="new_location"),
            submitter=None,
            temp_images=[TempImageUploadMeta(temp_object_key="inbox/temp123")],
        )
    assert exc_info.value.code == "image_processing_failed"

    repo.create.assert_not_awaited()
