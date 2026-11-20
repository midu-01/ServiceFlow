from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.db.models.user import UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="Unique account username")
    password: str = Field(min_length=8, max_length=100, description="Account password")


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserCreateInternal(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.OPERATOR
