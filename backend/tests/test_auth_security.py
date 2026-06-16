from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_register_route_removed(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()

    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "someone@example.com",
                "password": "secret123",
                "full_name": "Someone",
            },
        )

    assert response.status_code == 404


def test_openapi_available_in_development(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()

    with TestClient(create_app()) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


def test_openapi_hidden_outside_development(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    get_settings.cache_clear()

    with TestClient(create_app()) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
