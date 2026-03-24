import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class License(Base):
    __tablename__ = "licenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    license_type = Column(Enum("EXCLUSIVE", "NON_EXCLUSIVE", "PERSONAL", name="license_types"), nullable=False)
    price = Column(Numeric(18, 2), nullable=False, default=0.0)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    owner = relationship("User", foreign_keys=[owner_id])
    assets = relationship("Asset", back_populates="license")


class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    phash = Column(String(64), nullable=False, index=True)  # Fingerprint

    license = relationship("License", back_populates="assets")


class TransactionHistory(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tx_type = Column(Enum("MINT", "EXCLUSIVE", "NON_EXCLUSIVE", name="tx_types"), nullable=False)
    price = Column(Numeric(18, 2), nullable=False)
    blockchain_tx_hash = Column(String(66), nullable=False) # 0x...
    created_at = Column(DateTime, default=datetime.utcnow)