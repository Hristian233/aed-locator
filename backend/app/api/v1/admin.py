from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_admin_user, get_aed_service, get_report_service
from app.api.http_errors import not_found
from app.api.v1.aeds import limiter
from app.core.config import get_settings
from app.models.aed import VerificationStatus
from app.models.report import ReportStatus
from app.models.user import User
from app.schemas.aed import AEDListResponse, AEDResponse, AEDUpdate
from app.schemas.report import ReportListResponse, ReportResponse
from app.services.aed_service import AEDService
from app.services.report_service import ReportService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/aeds/pending", response_model=AEDListResponse)
async def list_pending(
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    _: Annotated[User, Depends(get_admin_user)],
    page: int = 1,
    page_size: int = 20,
) -> AEDListResponse:
    return await aed_service.list_aeds(
        page=page,
        page_size=page_size,
        status="pending",
        verified_only=False,
    )


@router.patch("/aeds/{aed_id}", response_model=AEDResponse)
async def update_aed(
    aed_id: int,
    payload: AEDUpdate,
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    _: Annotated[User, Depends(get_admin_user)],
) -> AEDResponse:
    result = await aed_service.update_aed(aed_id, payload)
    if not result:
        raise not_found("aed_not_found", "AED not found")
    return result


@router.post("/aeds/{aed_id}/verify", response_model=AEDResponse)
async def verify_aed(
    aed_id: int,
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    _: Annotated[User, Depends(get_admin_user)],
) -> AEDResponse:
    result = await aed_service.verify_aed(aed_id, VerificationStatus.verified)
    if not result:
        raise not_found("aed_not_found", "AED not found")
    return result


@router.post("/aeds/{aed_id}/reject", response_model=AEDResponse)
async def reject_aed(
    aed_id: int,
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    _: Annotated[User, Depends(get_admin_user)],
) -> AEDResponse:
    result = await aed_service.verify_aed(aed_id, VerificationStatus.rejected)
    if not result:
        raise not_found("aed_not_found", "AED not found")
    return result


@router.get("/reports/pending", response_model=ReportListResponse)
@limiter.limit(get_settings().rate_limit_reports)
async def list_pending_reports(
    request: Request,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[User, Depends(get_admin_user)],
    page: int = 1,
    page_size: int = 20,
) -> ReportListResponse:
    return await report_service.list_pending_reports(page=page, page_size=page_size)


@router.post("/reports/{report_id}/resolve", response_model=ReportResponse)
@limiter.limit(get_settings().rate_limit_reports)
async def resolve_report(
    request: Request,
    report_id: int,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[User, Depends(get_admin_user)],
) -> ReportResponse:
    result = await report_service.update_status(report_id, ReportStatus.resolved)
    if not result:
        raise not_found("report_not_found", "Report not found")
    return result


@router.post("/reports/{report_id}/dismiss", response_model=ReportResponse)
@limiter.limit(get_settings().rate_limit_reports)
async def dismiss_report(
    request: Request,
    report_id: int,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[User, Depends(get_admin_user)],
) -> ReportResponse:
    result = await report_service.update_status(report_id, ReportStatus.dismissed)
    if not result:
        raise not_found("report_not_found", "Report not found")
    return result
