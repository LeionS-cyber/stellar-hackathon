"""
Application configuration using Pydantic Settings.
All configuration is environment-based and validated.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env file"""

    # Application
    APP_NAME: str = "ProofChain API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    RELOAD: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/proofchain"
    DATABASE_ECHO: bool = False  # Set to True to see SQL queries

    # Security & JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Soroban / Stellar Blockchain
    SOROBAN_RPC_URL: str = "https://soroban-testnet.stellar.org"
    SOROBAN_NETWORK_PASSPHRASE: str = "Test SDF Network ; September 2015"
    CONTRACT_ID: str = "CAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABSC4"
    ISSUER_SECRET_KEY: str = ""  # Must be set in production
    ISSUER_PUBLIC_KEY: str = ""  # Derived from secret key

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "gif", "webp"]

    # Image Processing
    PHASH_THRESHOLD: int = 5  # Hamming distance threshold for collision detection
    IMAGE_RESIZE_MAX_WIDTH: int = 2048
    IMAGE_RESIZE_MAX_HEIGHT: int = 2048

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "text"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **data):
        super().__init__(**data)
        # Create uploads directory if it doesn't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)


# Global settings instance
settings = Settings()