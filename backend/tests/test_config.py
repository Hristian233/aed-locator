from app.core.config import Settings, get_settings


def test_gcs_settings_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "gcs")
    monkeypatch.setenv("GCS_TEMP_BUCKET", "aed-locator-prod-inbox")
    monkeypatch.setenv("GCS_IMAGES_BUCKET", "aed-locator-prod-aed-images")
    monkeypatch.setenv("MAX_IMAGE_BYTES", "10485760")
    monkeypatch.setenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/webp")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.storage_backend == "gcs"
    assert settings.gcs_temp_bucket == "aed-locator-prod-inbox"
    assert settings.gcs_images_bucket == "aed-locator-prod-aed-images"
    assert settings.max_image_bytes == 10_485_760
    assert settings.allowed_image_mime_types == {"image/jpeg", "image/png", "image/webp"}
    assert settings.uses_gcs_storage is True


def test_development_defaults_use_local_storage_and_dev_buckets() -> None:
    settings = Settings()

    assert settings.storage_backend == "local"
    assert settings.gcs_temp_bucket == "aed-locator-dev-inbox"
    assert settings.gcs_images_bucket == "aed-locator-dev-aed-images"
    assert settings.max_image_bytes == 10 * 1024 * 1024
