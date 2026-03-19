from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class ChallengeRequest(BaseModel):
    wallet_address: str = Field(..., min_length=56, max_length=56, pattern=r'^G[A-Z0-9]{55}$')

class ChallengeResponse(BaseModel):
    challenge: str
    expires_at: datetime

class VerifyRequest(BaseModel):
    wallet_address: str
    challenge: str
    signature: str  # Base64 encoded

class UserResponse(BaseModel):
    id: UUID
    wallet_address: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse