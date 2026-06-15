import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def local_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


def test_submit_aed_rejects_more_than_max_multipart_images(local_client: TestClient) -> None:
    max_images = get_settings().max_images_per_submission
    files = [
        ("images", (f"photo{i}.jpg", b"x" * 2000, "image/jpeg"))
        for i in range(max_images + 1)
    ]
    data = {
        "latitude": "42.6977",
        "longitude": "23.3219",
        "report_type": "new_location",
        "description": "Too many photos attached.",
    }

    response = local_client.post("/api/v1/aeds", data=data, files=files)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "image_too_many"
    assert detail["max_images"] == max_images


def test_submit_aed_rejects_more_than_max_multipart_images_on_gcs(gcs_settings) -> None:
    max_images = get_settings().max_images_per_submission
    files = [
        ("images", (f"photo{i}.jpg", b"x" * 2000, "image/jpeg"))
        for i in range(max_images + 1)
    ]
    data = {
        "latitude": "42.6977",
        "longitude": "23.3219",
        "report_type": "new_location",
        "description": "Too many photos attached.",
    }

    with TestClient(create_app()) as client:
        response = client.post("/api/v1/aeds", data=data, files=files)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "image_too_many"
    assert detail["max_images"] == max_images


def test_submit_aed_rejects_more_than_max_temp_object_keys(gcs_settings) -> None:
    max_images = get_settings().max_images_per_submission
    data = {
        "latitude": 42.6977,
        "longitude": 23.3219,
        "report_type": "new_location",
        "description": "Too many temp keys attached.",
        "image_temp_object_key": [f"inbox/temp{index}" for index in range(max_images + 1)],
        "image_content_type": ["image/jpeg"] * (max_images + 1),
        "image_content_length": [5000] * (max_images + 1),
    }

    with TestClient(create_app()) as client:
        response = client.post("/api/v1/aeds", data=data)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "image_too_many"
    assert detail["max_images"] == max_images
