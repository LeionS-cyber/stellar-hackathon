from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class LicenseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    license_type: str  # EXCLUSIVE, NON_EXCLUSIVE, PERSONAL
    price: Decimal

class AssetResponse(BaseModel):
    id: UUID
    file_path: str
    phash: str

class LicenseResponse(BaseModel):
    id: UUID
    title: str
    price: Decimal
    license_type: str
    owner_id: UUID
    creator_id: UUID
    created_at: datetime
    assets: List[AssetResponse]

    class Config:
        from_attributes = True

class VerificationResponse(BaseModel):
    status: str
    license_id: Optional[UUID] = None
    title: Optional[str] = None
    original_creator: Optional[str] = None
    current_owner: Optional[str] = None
    license_type: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None