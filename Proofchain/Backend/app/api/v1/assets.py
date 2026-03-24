from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.services.asset_service import AssetService
from app.schemas.asset import LicenseResponse, VerificationResponse
from app.dependencies.auth_deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/assets", tags=["Assets & Fingerprinting"])

@router.post("/upload", response_model=LicenseResponse)
async def upload_protected_collection(
    title: str = Form(...),
    description: str = Form(None),
    license_type: str = Form(...), # EXCLUSIVE, NON_EXCLUSIVE
    price: float = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Flow A: Proof of Creation (pHash collision checking & minting)"""
    asset_service = AssetService(db)
    license_record = await asset_service.create_protected_collection(
        creator=current_user,
        files=files,
        title=title,
        description=description,
        license_type=license_type,
        price=price
    )
    return license_record

@router.post("/verify", response_model=VerificationResponse)
async def verify_asset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Flow C: Verification Workflow (Screenshot uploaded by anyone -> Ownership Report)"""
    asset_service = AssetService(db)
    report = await asset_service.verify_asset(file)
    return report