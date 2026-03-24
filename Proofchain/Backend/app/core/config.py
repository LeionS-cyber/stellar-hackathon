from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/proofchain"
    SECRET_KEY: str = "super-secret-key-min-32-chars-long-hackathon"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Web3 / EVM Blockchain (As per Sepolia docs)
    WEB3_PROVIDER_URL: str = "https://sepolia.infura.io/v3/your-api-key"
    CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    
    # Upload Settings
    UPLOAD_DIR: str = "uploads"
    PHASH_THRESHOLD: int = 5  # Distance < 5 means collision

    class Config:
        env_file = ".env"

settings = Settings()