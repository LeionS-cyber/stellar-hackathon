"""
License purchase and transaction endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.services.asset_service import AssetService
from app.schemas.asset import PurchaseLicenseRequest, TransactionHistoryResponse
from app.dependencies.auth import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/licenses", tags=["Licenses"])


@router.post("/purchase", response_model=TransactionHistoryResponse, status_code=status.HTTP_201_CREATED)
async def purchase_license(
    request: PurchaseLicenseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Purchase a license (Flow B).
    
    - EXCLUSIVE: Full ownership transfer (only one buyer can do this)
    - NON_EXCLUSIVE: License to use (multiple buyers allowed)
    
    **Requires authentication.**
    """
    asset_service = AssetService(db)

    txn = await asset_service.purchase_license(
        buyer=current_user,
        license_id=str(request.license_id),
        license_type=request.license_type,
    )

    return TransactionHistoryResponse.model_validate(txn)


@router.get("/my-purchases", response_model=List[TransactionHistoryResponse])
async def get_my_purchases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all licenses purchased by current user"""
    asset_service = AssetService(db)
    purchases = await asset_service.get_user_purchases(str(current_user.id))
    return [TransactionHistoryResponse.model_validate(p) for p in purchases]