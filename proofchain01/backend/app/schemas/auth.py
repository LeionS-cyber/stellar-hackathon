"""
Pydantic schemas for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserRegisterRequest(BaseModel):
    """Request body for user registration"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    password_confirm: str = Field(..., min_length=8, max_length=255)

    def validate_password_match(self) -> bool:
        return self.password == self.password_confirm


class UserLoginRequest(BaseModel):
    """Request body for user login"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User response - safe to send to frontend"""

    id: UUID
    first_name: str
    last_name: str
    username: str
    email: str
    wallet_address: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh"""

    refresh_token: str