"""
Configuration management for CareLens 360.
Handles environment variables and application settings.
"""

import os
from typing import Optional

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    # dotenv is optional, environment variables can be set directly
    pass


class Config:
    """Application configuration class."""
    
    # Google Cloud Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
    FIRESTORE_COLLECTION: str = os.getenv("FIRESTORE_COLLECTION", "clinical_summaries")
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Application Settings
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    SUPPORTED_IMAGE_FORMATS: list = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration values are set.
        
        Returns:
            bool: True if all required configs are present, False otherwise
        """
        required_configs = [
            cls.GCP_PROJECT_ID,
            cls.GCS_BUCKET_NAME,
            cls.GEMINI_API_KEY,
        ]
        return all(required_configs)
    
    @classmethod
    def get_missing_configs(cls) -> list:
        """
        Get list of missing required configuration values.
        
        Returns:
            list: List of missing configuration keys
        """
        missing = []
        if not cls.GCP_PROJECT_ID:
            missing.append("GCP_PROJECT_ID")
        if not cls.GCS_BUCKET_NAME:
            missing.append("GCS_BUCKET_NAME")
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        return missing

