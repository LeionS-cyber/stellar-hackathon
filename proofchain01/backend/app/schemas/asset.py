"""
Pydantic schemas for asset and license endpoints.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


class AssetResponse(BaseModel):
    """Asset response schema"""

    id: UUID
    file_path: str
    file_name: str
    file_size: int
    phash: str
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LicenseCreateRequest(BaseModel):
    """Request body for creating a protected collection (license)"""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    license_type: str = Field(..., pattern="^(EXCLUSIVE|NON_EXCLUSIVE|PERSONAL)$")
    price: Decimal = Field(..., ge=Decimal("0.00"), decimal_places=2)


class LicenseResponse(BaseModel):
    """License response schema"""

    id: UUID
    creator_id: UUID
    owner_id: UUID
    title: str
    description: Optional[str]
    license_type: str
    price: Decimal
    blockchain_tx_hash: Optional[str]
    assets: List[AssetResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerificationResponse(BaseModel):
    """Response for asset verification"""

    status: str  # VERIFIED, UNPROTECTED, ERROR
    license_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    original_creator: Optional[str] = None
    current_owner: Optional[str] = None
    license_type: Optional[str] = None
    price: Optional[Decimal] = None
    blockchain_tx_hash: Optional[str] = None
    verified_licensees: Optional[int] = None
    all_assets_in_bundle: Optional[int] = None
    created_at: Optional[datetime] = None


class TransactionHistoryResponse(BaseModel):
    """Transaction history response"""

    id: UUID
    license_id: UUID
    buyer_id: UUID
    seller_id: UUID
    tx_type: str
    price: Decimal
    blockchain_tx_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseLicenseRequest(BaseModel):
    """Request body for purchasing a license"""

    license_id: UUID
    license_type: str = Field(..., pattern="^(EXCLUSIVE|NON_EXCLUSIVE)$")