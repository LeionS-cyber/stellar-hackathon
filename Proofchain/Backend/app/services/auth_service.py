import base64
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from stellar_sdk import Keypair
from app.models.user import User, AuthChallenge
from app.core.security import create_access_token

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_challenge(self, wallet_address: str) -> AuthChallenge:
        """Generate a cryptographically secure challenge"""
        challenge = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        challenge_text = f"ProofChainAuth:{challenge}:{wallet_address}:{int(datetime.utcnow().timestamp())}"
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        challenge_record = AuthChallenge(
            wallet_address=wallet_address,
            challenge_text=challenge_text,
            expires_at=expires_at,
            used=False
        )
        
        self.db.add(challenge_record)
        await self.db.commit()
        await self.db.refresh(challenge_record)
        return challenge_record
    
    @staticmethod
    def verify_stellar_signature(wallet_address: str, message: str, signature_b64: str) -> bool:
        """Verify ED25519 signature from Stellar wallet"""
        try:
            keypair = Keypair.from_public_key(wallet_address)
            message_bytes = message.encode('utf-8')
            signature_bytes = base64.b64decode(signature_b64)
            return keypair.verify(message_bytes, signature_bytes)
        except Exception:
            return False
    
    async def authenticate_user(self, wallet_address: str, challenge: str, signature: str) -> Optional[User]:
        """Verify signature and return/create user"""
        # Validate challenge
        result = await self.db.execute(
            select(AuthChallenge).where(
                AuthChallenge.wallet_address == wallet_address,
                AuthChallenge.challenge_text == challenge,
                AuthChallenge.used == False,
                AuthChallenge.expires_at > datetime.utcnow()
            )
        )
        challenge_record = result.scalar_one_or_none()
        
        if not challenge_record:
            return None
        
        # Verify signature
        if not self.verify_stellar_signature(wallet_address, challenge, signature):
            return None
        
        # Mark challenge as used
        challenge_record.used = True
        await self.db.commit()
        
        # Get or create user
        result = await self.db.execute(
            select(User).where(User.wallet_address == wallet_address)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(wallet_address=wallet_address)
            self.db.add(user)
        
        user.last_login = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    def create_access_token(self, user_id: str) -> str:
        """Create JWT token"""
        return create_access_token(user_id)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()