from typing import Annotated, Any, Dict
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_token_payload(
    authorization: Annotated[str | None, Header()] = None,
) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError(message="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        return payload
    except Exception as exc:
        raise UnauthorizedError(message="Invalid or expired access token") from exc


TokenPayloadDep = Annotated[Dict[str, Any], Depends(get_current_token_payload)]


def require_role(*allowed_roles: str):
    async def role_checker(payload: TokenPayloadDep) -> Dict[str, Any]:
        user_role = payload.get("role")
        if user_role not in allowed_roles:
            raise ForbiddenError(message="Insufficient permissions for this operation")
        return payload

    return role_checker
