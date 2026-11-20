from typing import Annotated, Any, Dict, Optional
import uuid
from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_token_payload(
    authorization: Annotated[Optional[str], Header()] = None,
    serviceflow_access_token: Annotated[Optional[str], Cookie()] = None,
) -> Dict[str, Any]:
    """Extracts and verifies JWT token from Authorization header or HttpOnly cookie."""
    token: Optional[str] = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    elif serviceflow_access_token:
        token = serviceflow_access_token

    if not token:
        raise UnauthorizedError(message="Authentication credentials were not provided")

    try:
        payload = decode_access_token(token)
        return payload
    except Exception as exc:
        raise UnauthorizedError(message="Invalid or expired access token") from exc


TokenPayloadDep = Annotated[Dict[str, Any], Depends(get_current_token_payload)]


async def get_current_user(
    payload: TokenPayloadDep,
    db: DbDep,
) -> User:
    """Loads authoritative User instance from PostgreSQL based on token subject."""
    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError(message="Token does not contain valid user identifier")

    try:
        user_uuid = uuid.UUID(sub)
    except ValueError as exc:
        raise UnauthorizedError(message="Invalid user identifier format in token") from exc

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)
    if user is None:
        raise UnauthorizedError(message="User account associated with token not found")

    if not user.is_active:
        raise ForbiddenError(message="User account is inactive")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: UserRole):
    """Enforces server-side role validation using trusted database user record."""
    async def role_checker(current_user: CurrentUserDep) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(message="Insufficient permissions for this operation")
        return current_user

    return role_checker

