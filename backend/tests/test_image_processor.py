from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.config import get_settings
from app.services.image_processor import ImageProcessorError, ImageProcessorService


@pytest.mark.asyncio
async def test_process_temp_image_returns_final_object_key(gcs_settings) -> None:
    mock_response = httpx.Response(
        200,
        json={"success": True, "final_object_key": "aed-images/abc.webp"},
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await ImageProcessorService(gcs_settings).process_temp_image(
            temp_object_key="inbox/temp123",
            content_type="image/jpeg",
            content_length=5000,
            final_object_key="aed-images/abc.webp",
        )

    assert result.final_object_key == "aed-images/abc.webp"


@pytest.mark.asyncio
async def test_process_temp_image_surfaces_cloud_function_error(gcs_settings) -> None:
    mock_response = httpx.Response(
        400,
        json={"success": False, "error": "Uploaded file is not a valid image"},
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(ImageProcessorError, match="not a valid image"):
            await ImageProcessorService(gcs_settings).process_temp_image(
                temp_object_key="inbox/bad",
                final_object_key="aed-images/bad.webp",
            )


@pytest.mark.asyncio
async def test_process_temp_image_requires_processor_url(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "gcs")
    monkeypatch.setenv("IMAGE_PROCESSOR_URL", "")
    get_settings.cache_clear()

    with pytest.raises(ImageProcessorError, match="not configured"):
        await ImageProcessorService().process_temp_image(
            temp_object_key="inbox/temp",
            final_object_key="aed-images/temp.webp",
        )
