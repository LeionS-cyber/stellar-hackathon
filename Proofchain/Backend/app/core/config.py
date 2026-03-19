from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/proofchain"
    
    # Security
    SECRET_KEY: str = "your-super-secret-hackathon-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Stellar
    STELLAR_NETWORK: str = "TESTNET"
    HORIZON_URL: str = "https://horizon-testnet.stellar.org"
    
    class Config:
        env_file = ".env"

settings = Settings()