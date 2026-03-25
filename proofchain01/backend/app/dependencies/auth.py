"""
Authentication dependency injection.
"""

from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.core.security import TokenManager
from app.core.exceptions import UnauthorizedException
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()
token_manager = TokenManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Usage:
        @app.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials

    # Decode token
    payload = token_manager.decode_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")

    # Verify token type
    if not token_manager.verify_token_type(payload, "access"):
        raise UnauthorizedException("Invalid token type")

    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token")

    # Get user from database
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("User account is disabled")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    if not current_user.is_admin:
        raise UnauthorizedException(
            detail="Admin privileges required", status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user


def require_verified(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require verified user"""
    if not current_user.is_verified:
        raise UnauthorizedException(
            detail="Email verification required", status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user