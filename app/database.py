"""
Supabase Database Client
Handles all database connections and operations
"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """Supabase database client wrapper"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def get_client(self) -> Client:
        """Get Supabase client instance"""
        if not self.client:
            self._initialize_client()
        return self.client


# Global database instance
db = Database()


def get_db() -> Client:
    """Dependency for FastAPI routes"""
    return db.get_client()