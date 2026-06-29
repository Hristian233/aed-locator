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


def test_development_defaults_use_local_storage_and_dev_buckets(monkeypatch) -> None:
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    get_settings.cache_clear()
    settings = Settings(_env_file=None)

    assert settings.storage_backend == "local"
    assert settings.gcs_temp_bucket == "aed-locator-dev-inbox"
    assert settings.gcs_images_bucket == "aed-locator-dev-aed-images"
    assert (
        settings.gcs_images_public_url_base
        == "https://storage.googleapis.com/aed-locator-dev-aed-images"
    )
    assert settings.max_image_bytes == 10 * 1024 * 1024


def test_max_images_per_submission_default(monkeypatch) -> None:
    monkeypatch.delenv("MAX_IMAGES_PER_SUBMISSION", raising=False)
    get_settings.cache_clear()
    settings = Settings(_env_file=None)
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
    assert (
        settings.gcs_images_public_url_base
        == "https://storage.googleapis.com/aed-locator-prod-aed-images"
    )


def test_explicit_gcs_buckets_override_environment_defaults(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("GCS_TEMP_BUCKET", "custom-temp-bucket")
    monkeypatch.setenv("GCS_IMAGES_BUCKET", "custom-images-bucket")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gcs_temp_bucket == "custom-temp-bucket"
    assert settings.gcs_images_bucket == "custom-images-bucket"
    assert (
        settings.gcs_images_public_url_base
        == "https://storage.googleapis.com/custom-images-bucket"
    )


def test_explicit_gcs_public_url_base_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "gcs")
    monkeypatch.setenv("GCS_IMAGES_BUCKET", "private-images-bucket")
    monkeypatch.setenv("GCS_IMAGES_PUBLIC_URL_BASE", "")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gcs_images_bucket == "private-images-bucket"
    assert settings.gcs_images_public_url_base == ""


def test_development_enables_docs_only(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    settings = Settings(_env_file=None)

    assert settings.docs_enabled is True


def test_staging_disables_docs(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    get_settings.cache_clear()
    settings = Settings(_env_file=None)

    assert settings.docs_enabled is False
