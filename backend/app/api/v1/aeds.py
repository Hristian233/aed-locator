from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_aed_service, get_current_user_optional
from app.core.config import get_settings
from app.models.user import User
from app.schemas.aed import AEDCreate, AEDListResponse, AEDResponse, NearestAEDQuery, SubmissionResult
from app.services.aed_service import AEDService
from app.services.image_validation import ImageValidationError
from app.services.storage_service import StorageService

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
        reachable_only=query.reachable_only,
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
    report_type: str = Form("new_location"),
    address: str | None = Form(None),
    description: str | None = Form(None),
    accessibility_type: str = Form("24_7"),
    opening_hours: str | None = Form(None),
    contact_email: str | None = Form(None),
    related_aed_id: int | None = Form(None),
    image: UploadFile | None = File(None),
    image_temp_object_key: str | None = Form(None),
    image_content_type: str | None = Form(None),
    image_content_length: int | None = Form(None),
) -> SubmissionResult:
    settings = get_settings()
    storage = StorageService(settings)
    image_content: bytes | None = None
    content_type: str | None = image_content_type

    if settings.uses_gcs_storage and image and image.filename:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Upload the image using a signed URL, then submit image_temp_object_key.",
        )

    if image and image.filename:
        content_type = image.content_type or ""
        image_content = await image.read()
        try:
            storage.validate_upload_metadata(content_type, len(image_content))
        except ImageValidationError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if image_temp_object_key and image_content_type and image_content_length:
        try:
            storage.validate_upload_metadata(image_content_type, image_content_length)
        except ImageValidationError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    data = AEDCreate(
        latitude=latitude,
        longitude=longitude,
        address=address,
        description=description,
        accessibility_type=accessibility_type,  # type: ignore[arg-type]
        opening_hours=opening_hours,
        report_type=report_type,  # type: ignore[arg-type]
        contact_email=contact_email or None,
        related_aed_id=related_aed_id,
    )
    try:
        return await aed_service.submit_aed(
            data,
            submitter=user,
            image_content=image_content,
            image_content_type=content_type,
            image_temp_object_key=image_temp_object_key,
            image_content_length=image_content_length,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
