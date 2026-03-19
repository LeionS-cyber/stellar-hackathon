from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import ChallengeRequest, ChallengeResponse, VerifyRequest, TokenResponse, UserResponse
from app.dependencies.auth_deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/challenge", response_model=ChallengeResponse)
async def get_challenge(
    request: ChallengeRequest,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    challenge = await auth_service.generate_challenge(request.wallet_address)
    
    return ChallengeResponse(
        challenge=challenge.challenge_text,
        expires_at=challenge.expires_at
    )

@router.post("/verify", response_model=TokenResponse)
async def verify_signature(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(
        request.wallet_address,
        request.challenge,
        request.signature
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature or expired challenge"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token = auth_service.create_access_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)