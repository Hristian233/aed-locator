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
    assert settings.gcs_images_bucket == "aed-locator-dev-images"
    assert settings.max_image_bytes == 10 * 1024 * 1024


def test_max_images_per_submission_default() -> None:
    settings = Settings()
    assert settings.max_images_per_submission == 5
    assert settings.min_images_new_location == 1


def test_production_environment_resolves_prod_gcs_buckets(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("GCS_TEMP_BUCKET", "")
    monkeypatch.setenv("GCS_IMAGES_BUCKET", "")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.environment == "production"
    assert settings.gcs_temp_bucket == "aed-locator-prod-inbox"
    assert settings.gcs_images_bucket == "aed-locator-prod-aed-images"


def test_explicit_gcs_buckets_override_environment_defaults(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("GCS_TEMP_BUCKET", "custom-temp-bucket")
    monkeypatch.setenv("GCS_IMAGES_BUCKET", "custom-images-bucket")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gcs_temp_bucket == "custom-temp-bucket"
    assert settings.gcs_images_bucket == "custom-images-bucket"
