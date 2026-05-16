from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_admin_user, get_aed_service
from app.models.aed import VerificationStatus
from app.models.user import User
from app.schemas.aed import AEDListResponse, AEDResponse
from app.services.aed_service import AEDService

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


@router.post("/aeds/{aed_id}/verify", response_model=AEDResponse)
async def verify_aed(
    aed_id: int,
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    _: Annotated[User, Depends(get_admin_user)],
) -> AEDResponse:
    result = await aed_service.verify_aed(aed_id, VerificationStatus.verified)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="AED not found")
    return result


@router.post("/aeds/{aed_id}/reject", response_model=AEDResponse)
async def reject_aed(
    aed_id: int,
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    _: Annotated[User, Depends(get_admin_user)],
) -> AEDResponse:
    result = await aed_service.verify_aed(aed_id, VerificationStatus.rejected)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="AED not found")
    return result
