"""
Application configuration settings.
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Upload settings
    MAX_UPLOAD_SIZE_MB: int = 100
    TEMP_DIR: Path = Path("/tmp")
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "info"
    
    # CORS (for local development only)
    ENABLE_CORS: bool = False
    
    # Application metadata
    APP_NAME: str = "OpenStack Admin Assistant Portal"
    APP_VERSION: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
