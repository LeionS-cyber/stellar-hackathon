"""
Asset and verification endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.services.asset_service import AssetService
from app.schemas.asset import (
    LicenseCreateRequest,
    LicenseResponse,
    VerificationResponse,
    AssetResponse,
)
from app.dependencies.auth import get_current_user
from app.models.user import User
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("/upload", response_model=LicenseResponse, status_code=status.HTTP_201_CREATED)
async def upload_protected_collection(
    title: str = Form(...),
    description: str = Form(None),
    license_type: str = Form(...),
    price: float = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a protected collection (Flow A: Proof of Creation).
    
    - Saves files and generates pHashes
    - Checks for collisions (anti-theft)
    - Mints on blockchain
    - Returns license details
    
    **Parameters:**
    - title: Bundle name (e.g., "Tokyo Street Photos")
    - description: Optional description
    - license_type: EXCLUSIVE, NON_EXCLUSIVE, or PERSONAL
    - price: Price in USD (or 0 for PERSONAL)
    - files: Image files to upload
    """
    asset_service = AssetService(db)

    license_record = await asset_service.create_protected_collection(
        creator=current_user,
        files=files,
        title=title,
        description=description,
        license_type=license_type,
        price=Decimal(str(price)),
    )

    return LicenseResponse.model_validate(license_record)


@router.post("/verify", response_model=VerificationResponse)
async def verify_asset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify an asset (Flow C: Verification Workflow).
    
    - User uploads any image (original or screenshot)
    - System generates pHash and searches database
    - Returns ownership certificate with blockchain proof
    
    **No authentication required** - anyone can verify assets.
    """
    asset_service = AssetService(db)
    report = await asset_service.verify_asset(file)
    return VerificationResponse(**report)


@router.get("/licenses/{license_id}", response_model=LicenseResponse)
async def get_license(
    license_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed license information"""
    asset_service = AssetService(db)
    license_rec = await asset_service.get_license_details(license_id)

    if not license_rec:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("License not found")

    return LicenseResponse.model_validate(license_rec)


@router.get("/my-licenses", response_model=List[LicenseResponse])
async def get_my_licenses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all licenses owned by current user"""
    asset_service = AssetService(db)
    licenses = await asset_service.get_user_licenses(str(current_user.id))
    return [LicenseResponse.model_validate(lic) for lic in licenses]