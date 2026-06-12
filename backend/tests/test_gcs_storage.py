from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.gcs_storage import GCSStorageError, GCSStorageService


@pytest.fixture
def gcs_service() -> GCSStorageService:
    settings = Settings(
        storage_backend="gcs",
        gcs_temp_bucket="aed-locator-dev-inbox",
        gcs_images_bucket="aed-locator-dev-images",
    )
    return GCSStorageService(settings)


def test_cloud_run_signing_kwargs_use_access_token_when_no_signer(
    gcs_service: GCSStorageService,
) -> None:
    credentials = MagicMock()
    credentials.signer = None
    credentials.token = "access-token"
    credentials.service_account_email = "api@project.iam.gserviceaccount.com"
    credentials.refresh = MagicMock()

    with patch("app.services.gcs_storage.google.auth.default", return_value=(credentials, "project")):
        kwargs = gcs_service._cloud_run_signing_kwargs()

    credentials.refresh.assert_called_once()
    assert kwargs == {
        "access_token": "access-token",
        "service_account_email": "api@project.iam.gserviceaccount.com",
    }


def test_cloud_run_signing_kwargs_empty_when_private_key_available(
    gcs_service: GCSStorageService,
) -> None:
    credentials = MagicMock()
    credentials.signer = object()

    with patch("app.services.gcs_storage.google.auth.default", return_value=(credentials, "project")):
        assert gcs_service._cloud_run_signing_kwargs() == {}


def test_cloud_run_signing_kwargs_fail_without_service_account_email(
    gcs_service: GCSStorageService,
) -> None:
    credentials = MagicMock()
    credentials.signer = None
    credentials.token = "access-token"
    credentials.service_account_email = None
    credentials.refresh = MagicMock()

    with patch("app.services.gcs_storage.google.auth.default", return_value=(credentials, "project")):
        with pytest.raises(GCSStorageError, match="service account"):
            gcs_service._cloud_run_signing_kwargs()
