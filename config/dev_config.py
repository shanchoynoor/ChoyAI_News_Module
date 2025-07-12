"""
Development configuration for ChoyNewsBot.
"""
import os
from .base_config import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    # Debug settings
    DEBUG = True
    TESTING = False
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FILE = os.getenv("LOG_FILE", "logs/choynews_dev.log")
    
    # Database (use local SQLite for development)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/choynews_dev.db")
    
    # API timeouts (shorter for development)
    API_TIMEOUT = 10
    REQUEST_TIMEOUT = 5
    
    # Cache settings (shorter TTL for development)
    CACHE_TTL = 300  # 5 minutes
    REDIS_TTL = 600  # 10 minutes
    
    # Rate limiting (more lenient for development)
    RATE_LIMIT_PER_MINUTE = 100
    RATE_LIMIT_BURST = 20
    
    # News settings (smaller batches for faster testing)
    MAX_NEWS_PER_CATEGORY = 3
    NEWS_FETCH_INTERVAL = 300  # 5 minutes
    
    # Development features
    ENABLE_DEBUG_ENDPOINTS = True
    MOCK_EXTERNAL_APIS = os.getenv("MOCK_EXTERNAL_APIS", "false").lower() == "true"
    
    # Test data
    USE_SAMPLE_DATA = True
    SAMPLE_DATA_PATH = "tests/fixtures/sample_data.py"
    
    @classmethod
    def init_app(cls, app=None):
        """Initialize development-specific settings."""
        # Ensure development directories exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/cache", exist_ok=True)
        
        # Development logging setup
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
