import os
import uuid
from PIL import Image
import imagehash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException
from app.models.asset import License, Asset, TransactionHistory
from app.models.user import User
from app.core.config import settings
from app.services.blockchain_service import BlockchainService

class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.blockchain_service = BlockchainService()

    @staticmethod
    def generate_phash(image_path: str) -> str:
        """Step 2: Fingerprint Extraction"""
        img = Image.open(image_path)
        hash_val = imagehash.phash(img)
        return str(hash_val)

    @staticmethod
    def calculate_hamming_distance(hash1_str: str, hash2_str: str) -> int:
        h1 = imagehash.hex_to_hash(hash1_str)
        h2 = imagehash.hex_to_hash(hash2_str)
        return h1 - h2

    async def check_collision(self, new_phash: str) -> bool:
        """Step 2: Collision Check"""
        result = await self.db.execute(select(Asset))
        all_assets = result.scalars().all()

        for existing_asset in all_assets:
            distance = self.calculate_hamming_distance(new_phash, existing_asset.phash)
            if distance < settings.PHASH_THRESHOLD:
                return True
        return False

    async def create_protected_collection(
        self, creator: User, files: List[UploadFile], title: str, description: str, license_type: str, price: float
    ) -> License:
        
        # 1. Save Files and Generate pHashes
        temp_paths = []
        hashes = []
        for file in files:
            file_ext = os.path.splitext(file.filename)[1]
            file_name = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(settings.UPLOAD_DIR, file_name)
            
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            phash = self.generate_phash(file_path)
            
            # 2. Collision Check
            if await self.check_collision(phash):
                # Clean up uploaded files if collision detected
                os.remove(file_path)
                for path in temp_paths: os.remove(path)
                raise HTTPException(status_code=400, detail="Similarity detected! Asset is already registered by another user.")

            temp_paths.append(file_path)
            hashes.append((file_path, phash))

        # 3. Create License & Save in DB
        license_record = License(
            creator_id=creator.id,
            owner_id=creator.id,
            license_type=license_type,
            price=price,
            title=title,
            description=description
        )
        self.db.add(license_record)
        await self.db.flush()

        for file_path, phash in hashes:
            asset = Asset(license_id=license_record.id, file_path=file_path, phash=phash)
            self.db.add(asset)

        # 4. Smart Contract Mint
        tx_hash = await self.blockchain_service.record_transaction(
            creator.wallet_address,
            "0x0000000000000000000000000000000000000000",
            str(license_record.id),
            price,
            "MINT",
            creator.encrypted_private_key # In practice decrypt this
        )

        txn = TransactionHistory(
            license_id=license_record.id,
            buyer_id=creator.id,
            seller_id=creator.id,
            tx_type="MINT",
            price=price,
            blockchain_tx_hash=tx_hash
        )
        self.db.add(txn)
        
        await self.db.commit()
        await self.db.refresh(license_record)
        return license_record

    async def verify_asset(self, file: UploadFile) -> dict:
        """Verification Engine (Upload any photo -> Get Certificate)"""
        temp_path = f"uploads/temp_{uuid.uuid4()}.png"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        uploaded_phash = self.generate_phash(temp_path)
        os.remove(temp_path)

        # Search DB for closest Match
        result = await self.db.execute(select(Asset))
        all_assets = result.scalars().all()

        matched_asset = None
        for asset in all_assets:
            if self.calculate_hamming_distance(uploaded_phash, asset.phash) < settings.PHASH_THRESHOLD:
                matched_asset = asset
                break

        if not matched_asset:
            return {"status": "UNPROTECTED"}

        # Gather Ownership Report
        result_license = await self.db.execute(
            select(License).where(License.id == matched_asset.license_id)
        )
        license_rec = result_license.scalar_one()

        creator = await self.db.get(User, license_rec.creator_id)
        owner = await self.db.get(User, license_rec.owner_id)

        # Get the mint transaction
        res_tx = await self.db.execute(
            select(TransactionHistory).where(TransactionHistory.license_id == license_rec.id, TransactionHistory.tx_type == "MINT")
        )
        mint_tx = res_tx.scalar_one_or_none()

        return {
            "status": "VERIFIED ASSET ✅",
            "license_id": license_rec.id,
            "title": license_rec.title,
            "original_creator": creator.username,
            "current_owner": owner.username,
            "license_type": license_rec.license_type,
            "blockchain_tx_hash": mint_tx.blockchain_tx_hash if mint_tx else "N/A"
        }