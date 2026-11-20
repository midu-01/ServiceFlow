from datetime import timedelta
from typing import Tuple
import uuid
from app.core.config import settings
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.db.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Service encapsulating user authentication and credential validation."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def authenticate(self, username: str, password: str) -> Tuple[User, str, int]:
        user = await self.user_repo.get_by_username(username)
        # Use constant-time or safe failure handling to avoid timing attacks
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError(message="Invalid username or password")

        if not user.is_active:
            raise ForbiddenError(message="Account is inactive. Please contact your administrator.")

        expires_in = settings.JWT_ACCESS_TOKEN_MINUTES * 60
        token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
            expires_delta=timedelta(seconds=expires_in),
        )

        return user, token, expires_in

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(message="User not found")
        if not user.is_active:
            raise ForbiddenError(message="Account is inactive")
        return user
