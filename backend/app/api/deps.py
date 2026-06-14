from typing import Annotated

from fastapi import Depends
from app.api.http_errors import forbidden, unauthorized
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.aed_repository import AEDRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.services.aed_service import AEDService
from app.services.auth_service import AuthService
from app.services.report_service import ReportService

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User | None:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    user_repo = UserRepository(db)
    return await user_repo.get_by_id(int(payload["sub"]))


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if not user:
        raise unauthorized("not_authenticated", "Not authenticated")
    return user


async def get_admin_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role != UserRole.admin:
        raise forbidden("admin_required", "Admin access required")
    return user


def get_aed_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AEDService:
    return AEDService(AEDRepository(db))


def get_report_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ReportService:
    return ReportService(ReportRepository(db), AEDRepository(db))


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(UserRepository(db))
