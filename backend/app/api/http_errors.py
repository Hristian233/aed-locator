from fastapi import HTTPException, status

from app.core.api_errors import ApiValidationError, exception_to_detail
from app.core.upload_limits import ImageTooManyError, image_too_many_detail
from app.services.auth_service import AuthError
from app.services.image_validation import ImageValidationError


_AUTH_ERROR_CODES = {
    "Email already registered": "email_registered",
    "Invalid email or password": "invalid_credentials",
    "Account disabled": "account_disabled",
}


def _image_validation_detail(exc: ImageValidationError) -> dict:
    message = str(exc)
    if "Unsupported image type" in message:
        return ApiValidationError("image_type_invalid", message=message).to_detail()
    if "too small" in message.lower():
        return ApiValidationError("image_too_small", message=message).to_detail()
    if "too large" in message.lower():
        return ApiValidationError("image_too_large", message=message).to_detail()
    return ApiValidationError("image_invalid", message=message).to_detail()


def raise_bad_request(exc: Exception) -> None:
    if isinstance(exc, ApiValidationError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.to_detail()) from exc
    if isinstance(exc, ImageTooManyError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=image_too_many_detail(exc.max_images),
        ) from exc
    if isinstance(exc, ImageValidationError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=_image_validation_detail(exc),
        ) from exc
    if isinstance(exc, ValueError):
        detail = exception_to_detail(exc)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail) from exc
    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail={"code": "unknown", "message": str(exc)},
    ) from exc


def auth_http_exception(exc: AuthError, *, status_code: int) -> HTTPException:
    code = _AUTH_ERROR_CODES.get(str(exc), "auth_failed")
    return HTTPException(
        status_code,
        detail={"code": code, "message": str(exc)},
    )


def not_found(code: str, message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND,
        detail={"code": code, "message": message},
    )


def forbidden(code: str, message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_403_FORBIDDEN,
        detail={"code": code, "message": message},
    )


def unauthorized(code: str, message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail={"code": code, "message": message},
    )
