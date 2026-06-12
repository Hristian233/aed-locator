from app.core.config import Settings
from app.services.storage_service import StorageService


def test_resolve_display_url_uses_placeholder_public_base_for_gcs() -> None:
    settings = Settings(
        storage_backend="gcs",
        gcs_temp_bucket="aed-locator-dev-inbox",
        gcs_images_bucket="aed-locator-dev-images",
        gcs_images_public_url_base="https://PLACEHOLDER.example/aed-images",
    )
    storage = StorageService(settings)

    url = storage.resolve_display_url("aed-images/photo.webp")

    assert url == "https://PLACEHOLDER.example/aed-images/aed-images/photo.webp"


def test_resolve_display_url_keeps_local_upload_paths() -> None:
    storage = StorageService(Settings())

    assert storage.resolve_display_url("/uploads/photo.jpg") == "/uploads/photo.jpg"
