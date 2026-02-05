"""
Application Configuration
Loads environment variables and provides typed config access
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Face Recognition Settings
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.3
    RECOGNITION_SIMILARITY_THRESHOLD: float = 0.5
    LIVENESS_MIN_FRAMES_PER_POSE: int = 15
    LIVENESS_POSE_DURATION_SECONDS: int = 2
    
    # Computed properties
    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()