from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.api.deps import get_current_user_optional, get_report_service
from app.api.v1.aeds import limiter
from app.core.config import get_settings
from app.core.upload_limits import ImageTooManyError, image_too_many_detail
from app.models.user import User
from app.schemas.aed import TempImageUploadMeta
from app.schemas.report import ReportCreate, ReportSubmissionResult
from app.services.aed_service import LocalImageUpload
from app.services.image_validation import ImageValidationError
from app.services.report_service import ReportService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/reports", tags=["reports"])


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


@router.post("", response_model=ReportSubmissionResult, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().rate_limit_reports)
async def submit_report(
    request: Request,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
    description: str = Form(...),
    aed_id: int | None = Form(None),
    reporter_latitude: float | None = Form(None),
    reporter_longitude: float | None = Form(None),
    contact_email: str | None = Form(None),
    image: UploadFile | None = File(None),
    images: list[UploadFile] = File(default=[]),
    image_temp_object_key: list[str] = Form(default=[]),
    image_content_type: list[str] = Form(default=[]),
    image_content_length: list[int] = Form(default=[]),
) -> ReportSubmissionResult:
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

    data = ReportCreate(
        description=description,
        aed_id=aed_id,
        reporter_latitude=reporter_latitude,
        reporter_longitude=reporter_longitude,
        contact_email=contact_email or None,
    )
    try:
        return await report_service.submit_report(
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
