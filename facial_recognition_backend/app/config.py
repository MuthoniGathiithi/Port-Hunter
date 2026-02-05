import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    DETECTION_CONFIDENCE_THRESHOLD: float = float(os.getenv("DETECTION_CONFIDENCE_THRESHOLD", 0.3))
    RECOGNITION_SIMILARITY_THRESHOLD: float = float(os.getenv("RECOGNITION_SIMILARITY_THRESHOLD", 0.5))
    LIVENESS_MIN_FRAMES_PER_POSE: int = int(os.getenv("LIVENESS_MIN_FRAMES_PER_POSE", 15))
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")

settings = Settings()
