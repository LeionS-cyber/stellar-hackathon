"""
Authentication service - handles user registration, login, and token management.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import PasswordHasher, TokenManager
from app.core.exceptions import UnauthorizedException, ConflictException, NotFoundException


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_hasher = PasswordHasher()
        self.token_manager = TokenManager()

    async def register_user(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        password: str,
        wallet_address: str = None,
    ) -> User:
        """
        Register a new user.
        
        Args:
            first_name: User's first name
            last_name: User's last name
            username: Unique username
            email: Unique email
            password: Plain text password (will be hashed)
            wallet_address: Optional Stellar wallet address
            
        Returns:
            Created User object
            
        Raises:
            ConflictException: If username or email already exists
        """
        # Check if user already exists
        result = await self.db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if result.scalar_one_or_none():
            raise ConflictException("Email or username already registered")

        # Hash password
        password_hash = self.password_hasher.hash_password(password)

        # Generate Stellar keypair for custodial wallet
        if not wallet_address:
            from stellar_sdk import Keypair
            keypair = Keypair.random()
            wallet_address = keypair.public_key

        # Create user
        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password_hash=password_hash,
            wallet_address=wallet_address,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.
        
        Returns:
            User object if authentication successful, None otherwise
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not self.password_hasher.verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await self.db.get(User, user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    def create_tokens(self, user_id: str) -> dict:
        """
        Create access and refresh tokens for user.
        
        Returns:
            Dictionary with access_token, refresh_token, expires_in
        """
        access_token = self.token_manager.create_access_token(user_id)
        refresh_token = self.token_manager.create_refresh_token(user_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 60 * 60 * 24,  # 24 hours in seconds
        }

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode a token"""
        return self.token_manager.decode_token(token)