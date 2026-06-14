from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.http_errors import raise_bad_request
from app.core.api_errors import ApiValidationError
from app.core.config import get_settings
from app.core.upload_limits import ImageTooManyError, image_too_many_detail
from app.schemas.uploads import (
    SignedUploadBatchRequest,
    SignedUploadBatchResponse,
    SignedUploadRequest,
    SignedUploadResponse,
)
from app.services.gcs_storage import GCSStorageError
from app.services.image_validation import ImageValidationError
from app.services.storage_service import StorageService

router = APIRouter(prefix="/uploads", tags=["uploads"])


def get_storage_service() -> StorageService:
    return StorageService()


def _reject_if_too_many_images(count: int) -> None:
    settings = get_settings()
    if count > settings.max_images_per_submission:
        raise_bad_request(ImageTooManyError(settings.max_images_per_submission))


@router.get("/config")
async def upload_config() -> dict[str, object]:
    settings = get_settings()
    return {
        "storage_backend": settings.storage_backend,
        "environment": settings.environment,
        "max_image_bytes": settings.max_image_bytes,
        "max_images_per_submission": settings.max_images_per_submission,
        "min_images_new_location": settings.min_images_new_location,
        "allowed_image_types": sorted(settings.allowed_image_mime_types),
        "gcs_temp_bucket": settings.gcs_temp_bucket if settings.uses_gcs_storage else None,
        "gcs_images_bucket": settings.gcs_images_bucket if settings.uses_gcs_storage else None,
    }


def _create_signed_upload(
    payload: SignedUploadRequest,
    storage: StorageService,
) -> SignedUploadResponse:
    try:
        upload_url, object_key, expires_in = storage.create_signed_upload(
            content_type=payload.content_type,
            content_length=payload.content_length,
        )
    except ImageValidationError as exc:
        raise_bad_request(exc)
    except GCSStorageError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "storage_unavailable", "message": str(exc)},
        ) from exc

    return SignedUploadResponse(
        upload_url=upload_url,
        object_key=object_key,
        expires_in_seconds=expires_in,
    )


@router.post("/signed-url", response_model=SignedUploadResponse)
async def create_signed_upload_url(
    payload: SignedUploadRequest,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> SignedUploadResponse:
    settings = get_settings()
    if not settings.uses_gcs_storage:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "direct_upload_disabled", "message": "Direct image uploads are not enabled for this environment."},
        )
    _reject_if_too_many_images(payload.total_images)
    return _create_signed_upload(payload, storage)


@router.post("/signed-urls", response_model=SignedUploadBatchResponse)
async def create_signed_upload_urls(
    payload: SignedUploadBatchRequest,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> SignedUploadBatchResponse:
    settings = get_settings()
    if not settings.uses_gcs_storage:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "direct_upload_disabled", "message": "Direct image uploads are not enabled for this environment."},
        )
    _reject_if_too_many_images(len(payload.uploads))

    items = [_create_signed_upload(item, storage) for item in payload.uploads]
    return SignedUploadBatchResponse(
        items=items,
        max_images_per_submission=settings.max_images_per_submission,
    )
