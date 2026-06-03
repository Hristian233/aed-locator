import pytest

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def gcs_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("STORAGE_BACKEND", "gcs")
    monkeypatch.setenv("GCS_TEMP_BUCKET", "aed-locator-dev-inbox")
    monkeypatch.setenv("GCS_IMAGES_BUCKET", "aed-locator-dev-aed-images")
    monkeypatch.setenv("GCS_IMAGE_PREFIX", "aed-images")
    monkeypatch.setenv("IMAGE_PROCESSOR_URL", "https://processor.example/process")
    monkeypatch.setenv("MAX_IMAGE_BYTES", "10485760")
    monkeypatch.setenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/webp")
    get_settings.cache_clear()
    return get_settings()
