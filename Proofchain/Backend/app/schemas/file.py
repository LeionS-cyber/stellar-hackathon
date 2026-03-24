from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class FileRegisterRequest(BaseModel):
    file_hash: str       # SHA-256 hex string
    file_location: str   # IPFS CID
    file_type: str       # pdf, png, etc.

class FileResponse(BaseModel):
    id: UUID
    user_id: UUID
    wallet_address: str
    file_hash: str
    file_location: str
    file_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True
