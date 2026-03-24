import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class File(Base):
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    wallet_address = Column(String(56), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 = 64 hex chars
    file_location = Column(String(255), nullable=False)  # IPFS CID
    file_type = Column(String(50), nullable=False)       # pdf, png, jpg, docx
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to user
    owner = relationship("User", backref="files")
