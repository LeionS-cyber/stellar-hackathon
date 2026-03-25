"""
Asset service - handles asset upload, collision detection, and verification.
"""

import os
from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import UploadFile
from app.models.asset import License, Asset, TransactionHistory
from app.models.user import User
from app.services.image_service import ImageService
from app.services.blockchain_service import BlockchainService
from app.core.config import settings
from app.core.exceptions import ConflictException, ValidationException, NotFoundException
import logging

logger = logging.getLogger(__name__)


class AssetService:
    """Service for asset and license management"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.image_service = ImageService()
        self.blockchain_service = BlockchainService()

    async def check_collision(self, new_phash: str) -> Optional[License]:
        """
        Check if a similar asset already exists (collision detection).
        
        Returns:
            License object if collision found, None otherwise
        """
        result = await self.db.execute(select(Asset))
        all_assets = result.scalars().all()

        for existing_asset in all_assets:
            distance = self.image_service.calculate_hamming_distance(
                new_phash, existing_asset.phash
            )
            if distance < settings.PHASH_THRESHOLD:
                # Return the license that owns this asset
                license_rec = await self.db.get(License, existing_asset.license_id)
                return license_rec

        return None

    async def create_protected_collection(
        self,
        creator: User,
        files: List[UploadFile],
        title: str,
        description: Optional[str],
        license_type: str,
        price: Decimal,
    ) -> License:
        """
        Create a protected collection (Flow A: Proof of Creation).
        
        1. Save files and generate pHashes
        2. Check for collisions
        3. Save to database
        4. Record on blockchain
        """
        saved_files = []
        hashes = []

        try:
            # Step 1: Save files and generate pHashes
            for upload_file in files:
                file_path, file_size = await self.image_service.save_upload_file(upload_file)
                phash = self.image_service.generate_phash(file_path)

                # Step 2: Check for collision
                collision = await self.check_collision(phash)
                if collision:
                    # Cleanup and raise error
                    for saved_path, _ in saved_files:
                        self.image_service.cleanup_file(saved_path)
                    raise ConflictException(
                        f"Similarity detected! This asset (or very similar) is already registered by user: {collision.creator.username}"
                    )

                # Get image metadata
                metadata = self.image_service.get_image_metadata(file_path)

                saved_files.append((file_path, upload_file.filename))
                hashes.append((file_path, upload_file.filename, phash, file_size, metadata))

            # Step 3: Create License record in database
            license_record = License(
                creator_id=creator.id,
                owner_id=creator.id,
                title=title,
                description=description,
                license_type=license_type,
                price=price,
            )
            self.db.add(license_record)
            await self.db.flush()  # Get the ID without committing

            # Create Asset records for each file
            for file_path, file_name, phash, file_size, metadata in hashes:
                asset = Asset(
                    license_id=license_record.id,
                    file_path=file_path,
                    file_name=file_name,
                    file_size=file_size,
                    phash=phash,
                    mime_type=metadata["mime_type"],
                    width=metadata.get("width"),
                    height=metadata.get("height"),
                )
                self.db.add(asset)

            # Step 4: Record mint transaction on blockchain
            tx_hash = await self.blockchain_service.record_transaction(
                seller_address=creator.wallet_address,
                buyer_address="GBRPYHIL2CI3WHZDTOOQFC6EB4LEGBPL2FD5EBWWRLBTX4YB44QNYX",  # Burn address
                license_id=str(license_record.id),
                price=float(price),
                tx_type="MINT",
            )

            license_record.blockchain_tx_hash = tx_hash

            # Create transaction history record
            txn = TransactionHistory(
                license_id=license_record.id,
                buyer_id=creator.id,
                seller_id=creator.id,
                tx_type="MINT",
                price=price,
                blockchain_tx_hash=tx_hash,
            )
            self.db.add(txn)

            # Commit all changes
            await self.db.commit()
            await self.db.refresh(license_record)

            logger.info(
                f"Protected collection created: {license_record.id} by {creator.username}"
            )
            return license_record

        except Exception as e:
            # Rollback transaction
            await self.db.rollback()
            # Cleanup files
            for file_path, _ in saved_files:
                self.image_service.cleanup_file(file_path)
            raise

    async def verify_asset(self, file: UploadFile) -> dict:
        """
        Verify an asset (Flow C: Verification Workflow).
        
        User uploads any image (screenshot or original) and gets ownership report.
        """
        temp_path = None
        try:
            # Save and process uploaded image
            temp_path, _ = await self.image_service.save_upload_file(file)
            uploaded_phash = self.image_service.generate_phash(temp_path)

            # Search for matching asset
            result = await self.db.execute(select(Asset))
            all_assets = result.scalars().all()

            matched_asset = None
            min_distance = float("inf")

            for asset in all_assets:
                distance = self.image_service.calculate_hamming_distance(
                    uploaded_phash, asset.phash
                )
                if distance < min_distance:
                    min_distance = distance
                    if distance < settings.PHASH_THRESHOLD:
                        matched_asset = asset

            # If no match found
            if not matched_asset:
                return {"status": "UNPROTECTED"}

            # Gather ownership report
            license_rec = await self.db.get(License, matched_asset.license_id)
            creator = await self.db.get(User, license_rec.creator_id)
            owner = await self.db.get(User, license_rec.owner_id)

            # Get all assets in bundle
            assets_result = await self.db.execute(
                select(Asset).where(Asset.license_id == license_rec.id)
            )
            all_bundle_assets = assets_result.scalars().all()

            # Get verified licensees (non-exclusive buyers)
            txn_result = await self.db.execute(
                select(TransactionHistory).where(
                    and_(
                        TransactionHistory.license_id == license_rec.id,
                        TransactionHistory.tx_type == "NON_EXCLUSIVE",
                    )
                )
            )
            verified_licensees = len(txn_result.scalars().all())

            # Get mint transaction
            mint_result = await self.db.execute(
                select(TransactionHistory).where(
                    and_(
                        TransactionHistory.license_id == license_rec.id,
                        TransactionHistory.tx_type == "MINT",
                    )
                )
            )
            mint_tx = mint_result.scalar_one_or_none()

            return {
                "status": "VERIFIED ASSET ✅",
                "license_id": license_rec.id,
                "title": license_rec.title,
                "description": license_rec.description,
                "original_creator": creator.username,
                "current_owner": owner.username,
                "license_type": license_rec.license_type,
                "price": license_rec.price,
                "blockchain_tx_hash": mint_tx.blockchain_tx_hash if mint_tx else None,
                "verified_licensees": verified_licensees,
                "all_assets_in_bundle": len(all_bundle_assets),
                "created_at": license_rec.created_at,
            }

        finally:
            # Cleanup temporary file
            if temp_path:
                self.image_service.cleanup_file(temp_path)

    async def purchase_license(
        self, buyer: User, license_id: str, license_type: str
    ) -> TransactionHistory:
        """
        Purchase a license (Flow B: Exclusive or Non-Exclusive Purchase).
        
        Args:
            buyer: Buying user
            license_id: License to purchase
            license_type: EXCLUSIVE or NON_EXCLUSIVE
        """
        # Get license
        license_rec = await self.db.get(License, license_id)
        if not license_rec:
            raise NotFoundException("License not found")

        # Cannot buy your own license
        if license_rec.owner_id == buyer.id:
            raise ValidationException("Cannot purchase your own license")

        # Cannot buy exclusive license that's already exclusive
        if license_rec.license_type == "EXCLUSIVE" and license_type == "EXCLUSIVE":
            raise ValidationException("This license is already exclusive")

        # Record transaction on blockchain
        tx_hash = await self.blockchain_service.record_transaction(
            seller_address=license_rec.owner.wallet_address,
            buyer_address=buyer.wallet_address,
            license_id=str(license_rec.id),
            price=float(license_rec.price),
            tx_type=license_type,
        )

        # Create transaction history record
        txn = TransactionHistory(
            license_id=license_rec.id,
            buyer_id=buyer.id,
            seller_id=license_rec.owner_id,
            tx_type=license_type,
            price=license_rec.price,
            blockchain_tx_hash=tx_hash,
        )
        self.db.add(txn)

        # If exclusive purchase, update license owner
        if license_type == "EXCLUSIVE":
            license_rec.owner_id = buyer.id
            license_rec.blockchain_tx_hash = tx_hash

        await self.db.commit()
        await self.db.refresh(txn)

        logger.info(f"License {license_id} purchased by {buyer.username}")
        return txn

    async def get_user_licenses(self, user_id: str) -> List[License]:
        """Get all licenses owned by user"""
        result = await self.db.execute(
            select(License).where(License.owner_id == user_id)
        )
        return result.scalars().all()

    async def get_user_purchases(self, user_id: str) -> List[TransactionHistory]:
        """Get all purchases made by user"""
        result = await self.db.execute(
            select(TransactionHistory).where(TransactionHistory.buyer_id == user_id)
        )
        return result.scalars().all()

    async def get_license_details(self, license_id: str) -> Optional[License]:
        """Get detailed license information"""
        return await self.db.get(License, license_id)