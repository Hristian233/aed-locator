from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.uploads import get_storage_service
from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def gcs_client(gcs_settings, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    storage = MagicMock()
    storage.create_signed_upload.return_value = (
        "https://storage.example/upload",
        "inbox/temp123",
        900,
    )

    app = create_app()
    app.dependency_overrides[get_storage_service] = lambda: storage

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def _upload_item(index: int = 0) -> dict[str, object]:
    return {
        "content_type": "image/jpeg",
        "content_length": 5000 + index,
    }


def test_batch_signed_urls_rejects_over_limit(gcs_client: TestClient) -> None:
    max_images = get_settings().max_images_per_submission
    uploads = [_upload_item(i) for i in range(max_images + 1)]

    response = gcs_client.post("/api/v1/uploads/signed-urls", json={"uploads": uploads})

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "image_too_many"
    assert detail["max_images"] == max_images
    assert f"At most {max_images}" in detail["message"]


def test_batch_signed_urls_allows_up_to_limit(gcs_client: TestClient) -> None:
    max_images = get_settings().max_images_per_submission
    uploads = [_upload_item(i) for i in range(max_images)]

    response = gcs_client.post("/api/v1/uploads/signed-urls", json={"uploads": uploads})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == max_images
    assert body["max_images_per_submission"] == max_images


def test_single_signed_url_rejects_when_total_images_over_limit(gcs_client: TestClient) -> None:
    max_images = get_settings().max_images_per_submission

    response = gcs_client.post(
        "/api/v1/uploads/signed-url",
        json={**_upload_item(), "total_images": max_images + 1},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "image_too_many"
    assert detail["max_images"] == max_images
    assert f"At most {max_images}" in detail["message"]


def test_single_signed_url_allows_default_total_images(gcs_client: TestClient) -> None:
    response = gcs_client.post("/api/v1/uploads/signed-url", json=_upload_item())

    assert response.status_code == 200
    body = response.json()
    assert body["upload_url"] == "https://storage.example/upload"
    assert body["object_key"] == "inbox/temp123"
