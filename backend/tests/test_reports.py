from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_report_service
from app.core.config import get_settings
from app.main import create_app
from app.models.report import ReportStatus
from app.repositories.aed_repository import AEDRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportCreate, ReportResponse, ReportSubmissionResult
from app.core.api_errors import ApiValidationError
from app.services.aed_service import LocalImageUpload
from app.services.report_service import ReportService


def _created_report(**overrides) -> MagicMock:
    report = MagicMock()
    report.id = overrides.get("id", 7)
    report.aed_id = overrides.get("aed_id")
    report.description = overrides.get("description", "Broken cabinet door.")
    report.reporter_latitude = overrides.get("reporter_latitude")
    report.reporter_longitude = overrides.get("reporter_longitude")
    report.reporter_location = None
    report.image_url = overrides.get("image_url")
    report.image_object_keys = overrides.get("image_object_keys")
    report.contact_email = overrides.get("contact_email")
    report.submitter_id = None
    report.status = ReportStatus.pending
    report.spam_score = 0.0
    report.aed = overrides.get("aed")
    report.created_at = report.updated_at = MagicMock()
    return report


@pytest.fixture
def local_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_submit_report_description_only() -> None:
    report_repo = MagicMock(spec=ReportRepository)
    aed_repo = MagicMock(spec=AEDRepository)
    report_repo.create = AsyncMock(side_effect=lambda report: _created_report(description=report.description))

    storage = MagicMock()
    service = ReportService(report_repo, aed_repo, storage=storage, ai=MagicMock())
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)

    result = await service.submit_report(
        ReportCreate(description="The AED is missing."),
        submitter=None,
    )

    created = report_repo.create.await_args.args[0]
    assert created.description == "The AED is missing."
    assert created.aed_id is None
    assert created.reporter_latitude is None
    assert created.reporter_location is None
    assert result.report.description == "The AED is missing."
    assert result.warnings == []


@pytest.mark.asyncio
async def test_submit_report_with_optional_fields() -> None:
    report_repo = MagicMock(spec=ReportRepository)
    aed_repo = MagicMock(spec=AEDRepository)
    related = MagicMock()
    related.id = 12
    aed_repo.get_by_id = AsyncMock(return_value=related)
    report_repo.create = AsyncMock(
        side_effect=lambda report: _created_report(
            aed_id=report.aed_id,
            reporter_latitude=report.reporter_latitude,
            reporter_longitude=report.reporter_longitude,
            contact_email=report.contact_email,
            image_object_keys=report.image_object_keys,
            image_url=report.image_url,
        )
    )

    storage = MagicMock()
    storage.save_image = AsyncMock(return_value="uploads/report-photo.webp")
    storage.resolve_display_url.side_effect = lambda key: f"https://example/{key}"

    settings = MagicMock()
    settings.uses_gcs_storage = False
    settings.max_images_per_submission = 5

    service = ReportService(report_repo, aed_repo, storage=storage, ai=MagicMock())
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)
    service.ai.analyze_image.return_value = MagicMock(likely_aed=True, confidence=0.8)
    storage.load_image_bytes = AsyncMock(return_value=b"webp")
    storage.validate_upload_metadata = MagicMock()

    with patch("app.services.report_service.get_settings", return_value=settings):
        result = await service.submit_report(
            ReportCreate(
                description="Incorrect address listed.",
                aed_id=12,
                reporter_latitude=42.6977,
                reporter_longitude=23.3219,
                contact_email="reporter@example.com",
            ),
            submitter=None,
            local_images=[LocalImageUpload(content=b"x" * 2000, content_type="image/jpeg")],
        )

    created = report_repo.create.await_args.args[0]
    assert created.aed_id == 12
    assert created.reporter_latitude == 42.6977
    assert created.reporter_longitude == 23.3219
    assert created.reporter_location is not None
    assert created.contact_email == "reporter@example.com"
    assert result.report.aed_id == 12


@pytest.mark.asyncio
async def test_submit_report_rejects_missing_description() -> None:
    service = ReportService(
        MagicMock(spec=ReportRepository),
        MagicMock(spec=AEDRepository),
        storage=MagicMock(),
        ai=MagicMock(),
    )

    with pytest.raises(ApiValidationError, match="description_required"):
        await service.submit_report(ReportCreate(description="   "), submitter=None)


@pytest.mark.asyncio
async def test_submit_report_rejects_invalid_aed_id() -> None:
    aed_repo = MagicMock(spec=AEDRepository)
    aed_repo.get_by_id = AsyncMock(return_value=None)
    service = ReportService(
        MagicMock(spec=ReportRepository),
        aed_repo,
        storage=MagicMock(),
        ai=MagicMock(),
    )
    service.ai.check_spam.return_value = MagicMock(is_spam=False, score=0.0)

    with pytest.raises(ApiValidationError, match="related_aed_not_found"):
        await service.submit_report(
            ReportCreate(description="Issue with AED", aed_id=999),
            submitter=None,
        )


@pytest.mark.asyncio
async def test_update_status_resolve_and_dismiss() -> None:
    report_repo = MagicMock(spec=ReportRepository)
    pending = _created_report()
    report_repo.get_by_id = AsyncMock(return_value=pending)
    report_repo.update = AsyncMock(side_effect=lambda report: report)

    service = ReportService(
        report_repo,
        MagicMock(spec=AEDRepository),
        storage=MagicMock(),
        ai=MagicMock(),
    )

    resolved = await service.update_status(7, ReportStatus.resolved)
    assert resolved is not None
    assert pending.status == ReportStatus.resolved

    dismissed = await service.update_status(7, ReportStatus.dismissed)
    assert dismissed is not None
    assert pending.status == ReportStatus.dismissed


@pytest.mark.asyncio
async def test_list_pending_reports() -> None:
    report_repo = MagicMock(spec=ReportRepository)
    pending = _created_report(description="Needs review")
    report_repo.list_pending = AsyncMock(return_value=([pending], 1))

    service = ReportService(
        report_repo,
        MagicMock(spec=AEDRepository),
        storage=MagicMock(),
        ai=MagicMock(),
    )

    result = await service.list_pending_reports(page=1, page_size=20)
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].description == "Needs review"


def test_submit_report_http_description_only(local_client: TestClient) -> None:
    mock_service = MagicMock(spec=ReportService)
    mock_service.submit_report = AsyncMock(
        return_value=ReportSubmissionResult(
            report=ReportResponse(
                id=1,
                description="The AED cabinet is damaged.",
                status="pending",
                created_at="2026-06-14T00:00:00Z",
                updated_at="2026-06-14T00:00:00Z",
            ),
            warnings=[],
        )
    )
    app = local_client.app
    app.dependency_overrides[get_report_service] = lambda: mock_service

    response = local_client.post(
        "/api/v1/reports",
        data={"description": "The AED cabinet is damaged."},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    body = response.json()
    assert body["report"]["description"] == "The AED cabinet is damaged."
    assert body["warnings"] == []


def test_submit_report_http_rejects_missing_description(local_client: TestClient) -> None:
    response = local_client.post("/api/v1/reports", data={"description": "   "})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "description_required"


def test_submit_report_http_rejects_invalid_aed_id(local_client: TestClient) -> None:
    mock_service = MagicMock(spec=ReportService)
    mock_service.submit_report = AsyncMock(
        side_effect=ApiValidationError("related_aed_not_found")
    )
    app = local_client.app
    app.dependency_overrides[get_report_service] = lambda: mock_service

    response = local_client.post(
        "/api/v1/reports",
        data={"description": "Issue with AED", "aed_id": "999999"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "related_aed_not_found"


def test_submit_aed_rejects_aed_issue_report_type(local_client: TestClient) -> None:
    response = local_client.post(
        "/api/v1/aeds",
        data={
            "latitude": "42.6977",
            "longitude": "23.3219",
            "report_type": "aed_issue",
            "description": "Should use reports endpoint.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "wrong_report_endpoint"


def test_submit_report_rejects_more_than_max_images(local_client: TestClient) -> None:
    max_images = get_settings().max_images_per_submission
    files = [
        ("images", (f"photo{i}.jpg", b"x" * 2000, "image/jpeg"))
        for i in range(max_images + 1)
    ]
    data = {"description": "Too many photos attached."}

    response = local_client.post("/api/v1/reports", data=data, files=files)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "image_too_many"
    assert detail["max_images"] == max_images
