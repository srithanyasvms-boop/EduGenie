"""
Configuration management module for EduGenie.
Loads environment variables and provides structured settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Application settings and environment configuration."""
    
    # Application Metadata
    APP_NAME: str = "EduGenie"
    APP_TITLE: str = "EduGenie – Google Gemini Powered Learning Assistant"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "An intelligent AI-powered educational assistant for students and learners, "
        "featuring Q&A, concept explanations, summarization, quiz generation, and personalized learning roadmaps."
    )
    
    # Server Settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Gemini API Settings (supports both GEMINI_API_KEY and GOOGLE_API_KEY)
    GEMINI_API_KEY: str = (
        os.getenv("GEMINI_API_KEY") 
        or os.getenv("GOOGLE_API_KEY") 
        or ""
    ).strip()
    
    # Gemini Model configuration (configurable via .env)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    
    # Local Model Settings (LaMini-Flan-T5-783M)
    LOCAL_MODEL_NAME: str = os.getenv("LOCAL_MODEL_NAME", "MBZUAI/LaMini-Flan-T5-783M").strip()
    USE_LOCAL_MODEL: bool = os.getenv("USE_LOCAL_MODEL", "True").lower() in ("true", "1", "t")
    LOCAL_MODEL_CACHE_DIR: str = os.getenv(
        "LOCAL_MODEL_CACHE_DIR", 
        str(BASE_DIR / "models" / "cache")
    )

    @property
    def is_gemini_configured(self) -> bool:
        """Check if a valid Gemini API key is configured."""
        return bool(
            self.GEMINI_API_KEY 
            and self.GEMINI_API_KEY != "your_gemini_api_key_here"
            and len(self.GEMINI_API_KEY) > 5
        )


settings = Settings()
