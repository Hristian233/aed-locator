from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserLogin, UserResponse


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, data: UserCreate) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise AuthError("Email already registered")

        settings = get_settings()
        role = UserRole.admin if data.email in settings.admin_emails else UserRole.user

        user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            role=role,
        )
        return await self.user_repo.create(user)

    async def login(self, data: UserLogin) -> tuple[User, str]:
        user = await self.user_repo.get_by_email(data.email.lower())
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise AuthError("Account disabled")

        token = create_access_token(
            str(user.id),
            extra={"email": user.email, "role": user.role.value},
        )
        return user, token

    @staticmethod
    def to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
        )
