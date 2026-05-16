from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service, get_current_user
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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TokenResponse(access_token=token, user=auth_service.to_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user, token = await auth_service.login(data)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=token, user=auth_service.to_response(user))


@router.get("/me", response_model=UserResponse)
async def me(
    user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    return auth_service.to_response(user)
