"""
Asset, License, and Transaction models per documentation.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Enum,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class License(Base):
    """License model - represents digital asset bundles"""

    __tablename__ = "licenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # License Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    license_type = Column(
        Enum("EXCLUSIVE", "NON_EXCLUSIVE", "PERSONAL", name="license_types"),
        nullable=False,
        default="PERSONAL",
    )
    price = Column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))

    # Blockchain Reference
    blockchain_tx_hash = Column(String(66), nullable=True)  # 0x...

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], backref="created_licenses")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_licenses")
    assets = relationship("Asset", back_populates="license", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_license_creator", "creator_id"),
        Index("idx_license_owner", "owner_id"),
        Index("idx_license_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<License(id={self.id}, title={self.title}, type={self.license_type})>"


class Asset(Base):
    """Asset model - individual files within a license"""

    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)

    # File Storage
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Numeric(15, 0), nullable=False)  # bytes

    # Perceptual Hash (Fingerprint)
    phash = Column(String(64), nullable=False, index=True)

    # Metadata
    mime_type = Column(String(100), nullable=False)
    width = Column(Numeric(10, 0), nullable=True)
    height = Column(Numeric(10, 0), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    license = relationship("License", back_populates="assets")

    __table_args__ = (Index("idx_asset_phash", "phash"),)

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, file_name={self.file_name})>"


class TransactionHistory(Base):
    """Transaction History model - blockchain transaction records"""

    __tablename__ = "transaction_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Transaction Details
    tx_type = Column(
        Enum("MINT", "EXCLUSIVE", "NON_EXCLUSIVE", name="tx_types"),
        nullable=False,
    )
    price = Column(Numeric(18, 2), nullable=False)

    # Blockchain Reference
    blockchain_tx_hash = Column(String(66), nullable=False, index=True)  # 0x...

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_txn_license", "license_id"),
        Index("idx_txn_buyer", "buyer_id"),
        Index("idx_txn_seller", "seller_id"),
        Index("idx_txn_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TransactionHistory(id={self.id}, type={self.tx_type})>"