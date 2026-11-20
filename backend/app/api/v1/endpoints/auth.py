from fastapi import APIRouter
from app.schemas.common import DataResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login() -> DataResponse[dict]:
    """Placeholder for JWT login endpoint (Implemented in Phase 8)."""
    return DataResponse(data={"message": "Auth endpoint scaffolded"})


@router.get("/me")
async def get_me() -> DataResponse[dict]:
    """Placeholder for user profile endpoint (Implemented in Phase 8)."""
    return DataResponse(data={"message": "Current user endpoint scaffolded"})


@router.post("/logout")
async def logout() -> DataResponse[dict]:
    """Placeholder for logout endpoint."""
    return DataResponse(data={"message": "Successfully logged out"})
