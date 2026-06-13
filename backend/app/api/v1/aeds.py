from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_aed_service, get_current_user_optional
from app.core.config import get_settings
from app.core.upload_limits import ImageTooManyError, image_too_many_detail
from app.models.user import User
from app.schemas.aed import AEDCreate, AEDListResponse, AEDResponse, NearestAEDQuery, SubmissionResult
from app.schemas.aed import TempImageUploadMeta
from app.services.aed_service import AEDService, LocalImageUpload
from app.services.image_validation import ImageValidationError
from app.services.storage_service import StorageService

router = APIRouter(prefix="/aeds", tags=["aeds"])
limiter = Limiter(key_func=get_remote_address)


def _zip_temp_image_metadata(
    temp_keys: list[str],
    content_types: list[str],
    content_lengths: list[int],
) -> list[TempImageUploadMeta]:
    uploads: list[TempImageUploadMeta] = []
    for index, temp_key in enumerate(temp_keys):
        if not temp_key.strip():
            continue
        content_type = content_types[index] if index < len(content_types) else None
        content_length = content_lengths[index] if index < len(content_lengths) else None
        uploads.append(
            TempImageUploadMeta(
                temp_object_key=temp_key.strip(),
                content_type=content_type or None,
                content_length=content_length,
            )
        )
    return uploads


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
    location_name: str | None = Form(None),
    is_restricted_access: bool = Form(False),
    description: str | None = Form(None),
    accessibility_type: str = Form("24_7"),
    opening_hours: str | None = Form(None),
    contact_email: str | None = Form(None),
    related_aed_id: int | None = Form(None),
    image: UploadFile | None = File(None),
    images: list[UploadFile] = File(default=[]),
    image_temp_object_key: list[str] = Form(default=[]),
    image_content_type: list[str] = Form(default=[]),
    image_content_length: list[int] = Form(default=[]),
) -> SubmissionResult:
    settings = get_settings()
    storage = StorageService(settings)
    local_images: list[LocalImageUpload] = []

    upload_files: list[UploadFile] = []
    if image and image.filename:
        upload_files.append(image)
    upload_files.extend([item for item in images if item.filename])

    temp_images = _zip_temp_image_metadata(
        image_temp_object_key,
        image_content_type,
        image_content_length,
    )

    max_images = settings.max_images_per_submission
    if len(upload_files) > max_images or len(temp_images) > max_images:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=image_too_many_detail(max_images),
        )
    if len(upload_files) + len(temp_images) > max_images:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=image_too_many_detail(max_images),
        )

    if settings.uses_gcs_storage and upload_files:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Upload photos using signed URLs, then submit image_temp_object_key for each image.",
        )

    for upload_file in upload_files:
        content_type = upload_file.content_type or ""
        content = await upload_file.read()
        try:
            storage.validate_upload_metadata(content_type, len(content))
        except ImageValidationError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        local_images.append(LocalImageUpload(content=content, content_type=content_type))

    data = AEDCreate(
        latitude=latitude,
        longitude=longitude,
        address=address,
        location_name=location_name,
        is_restricted_access=is_restricted_access,
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
            local_images=local_images,
            temp_images=temp_images,
        )
    except ImageTooManyError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=image_too_many_detail(exc.max_images),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
