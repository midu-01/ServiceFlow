from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.dependencies import CurrentUserDep, DbDep
from app.repositories.user_repository import UserRepository
from app.schemas.common import DataResponse
from app.schemas.user import LoginRequest, TokenData, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=DataResponse[TokenData], status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    response: Response,
    db: DbDep,
) -> DataResponse[TokenData]:
    """Authenticates user credentials, sets HttpOnly cookie, and returns JWT access token."""
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    user, token, expires_in = await auth_service.authenticate(
        username=payload.username,
        password=payload.password,
    )

    # Set secure HttpOnly cookie for browser sessions
    is_secure = settings.APP_ENV.lower() not in ("development", "dev", "test")
    response.set_cookie(
        key="serviceflow_access_token",
        value=token,
        max_age=expires_in,
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/",
    )

    return DataResponse(
        data=TokenData(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse.model_validate(user),
        )
    )


@router.get("/me", response_model=DataResponse[UserResponse], status_code=status.HTTP_200_OK)
async def get_me(
    current_user: CurrentUserDep,
) -> DataResponse[UserResponse]:
    """Returns profile and role information for currently authenticated user."""
    return DataResponse(
        data=UserResponse.model_validate(current_user)
    )


@router.post("/logout", response_model=DataResponse[dict], status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
) -> DataResponse[dict]:
    """Clears authentication session cookies."""
    response.delete_cookie(
        key="serviceflow_access_token",
        path="/",
    )
    return DataResponse(
        data={"message": "Successfully logged out"}
    )
