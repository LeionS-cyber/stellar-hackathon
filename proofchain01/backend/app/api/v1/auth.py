"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
)
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.core.exceptions import UnauthorizedException, ValidationException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    
    - Validates passwords match
    - Checks email/username uniqueness
    - Generates custodial Stellar wallet
    - Creates JWT tokens
    """
    if not request.validate_password_match():
        raise ValidationException("Passwords do not match")

    auth_service = AuthService(db)
    user = await auth_service.register_user(
        first_name=request.first_name,
        last_name=request.last_name,
        username=request.username,
        email=request.email,
        password=request.password,
    )

    tokens = auth_service.create_tokens(str(user.id))

    return {
        "user": UserResponse.model_validate(user),
        "tokens": tokens,
    }


@router.post("/login", response_model=dict)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login user with email and password.
    
    Returns JWT access and refresh tokens.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(request.email, request.password)

    if not user:
        raise UnauthorizedException("Invalid email or password")

    tokens = auth_service.create_tokens(str(user.id))

    return {
        "user": UserResponse.model_validate(user),
        "tokens": tokens,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    payload = auth_service.verify_token(request.refresh_token)

    if not payload or not auth_service.token_manager.verify_token_type(payload, "refresh"):
        raise UnauthorizedException("Invalid refresh token")

    user_id = payload.get("sub")
    tokens = auth_service.create_tokens(user_id)

    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    Requires valid JWT token.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout():
    """
    Logout user (client-side token deletion).
    
    JWT tokens are stateless, so logout is handled client-side.
    """
    return {"message": "Logged out successfully"}