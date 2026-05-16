from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_aed_service, get_current_user_optional
from app.core.config import get_settings
from app.models.user import User
from app.schemas.aed import AEDCreate, AEDListResponse, AEDResponse, NearestAEDQuery, SubmissionResult
from app.services.aed_service import AEDService

router = APIRouter(prefix="/aeds", tags=["aeds"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=AEDListResponse)
async def list_aeds(
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    page: int = 1,
    page_size: int = 50,
    status: str | None = None,
) -> AEDListResponse:
    return await aed_service.list_aeds(page=page, page_size=page_size, status=status)


@router.get("/nearest", response_model=list[AEDResponse])
async def nearest_aeds(
    query: Annotated[NearestAEDQuery, Depends()],
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
) -> list[AEDResponse]:
    return await aed_service.find_nearest(
        query.latitude,
        query.longitude,
        limit=query.limit,
        max_distance_meters=query.max_distance_meters,
    )


@router.get("/{aed_id}", response_model=AEDResponse)
async def get_aed(
    aed_id: int,
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
) -> AEDResponse:
    aed = await aed_service.get_aed(aed_id)
    if not aed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="AED not found")
    return aed


@router.post("", response_model=SubmissionResult, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().rate_limit_reports)
async def submit_aed(
    request: Request,
    aed_service: Annotated[AEDService, Depends(get_aed_service)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str | None = Form(None),
    description: str | None = Form(None),
    image: UploadFile | None = File(None),
) -> SubmissionResult:
    settings = get_settings()
    image_content: bytes | None = None
    content_type: str | None = None

    if image and image.filename:
        content_type = image.content_type or ""
        if content_type not in settings.allowed_image_types:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image type. Allowed: {settings.allowed_image_types}",
            )
        image_content = await image.read()
        if len(image_content) > settings.max_upload_bytes:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Image too large")

    data = AEDCreate(
        latitude=latitude,
        longitude=longitude,
        address=address,
        description=description,
    )
    try:
        return await aed_service.submit_aed(
            data,
            submitter=user,
            image_content=image_content,
            image_content_type=content_type,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
