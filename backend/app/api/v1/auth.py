from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.api.http_errors import auth_http_exception
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user = await auth_service.register(data)
        _, token = await auth_service.login(UserLogin(email=data.email, password=data.password))
    except AuthError as exc:
        raise auth_http_exception(exc, status_code=status.HTTP_400_BAD_REQUEST) from exc
    return TokenResponse(access_token=token, user=auth_service.to_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user, token = await auth_service.login(data)
    except AuthError as exc:
        raise auth_http_exception(exc, status_code=status.HTTP_401_UNAUTHORIZED) from exc
    return TokenResponse(access_token=token, user=auth_service.to_response(user))


@router.get("/me", response_model=UserResponse)
async def me(
    user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    return auth_service.to_response(user)
