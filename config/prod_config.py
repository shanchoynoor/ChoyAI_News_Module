"""
Production configuration for ChoyNewsBot.
"""
import os
from .base_config import BaseConfig


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    # Debug settings
    DEBUG = False
    TESTING = False
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/choynews.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 20971520))  # 20MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 10))
    
    # Database (prefer PostgreSQL for production)
    DATABASE_URL = os.getenv("DATABASE_URL", 
                            f"postgresql://{os.getenv('POSTGRES_USER', 'choynews')}:"
                            f"{os.getenv('POSTGRES_PASSWORD', '')}@"
                            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
                            f"{os.getenv('POSTGRES_PORT', '5432')}/"
                            f"{os.getenv('POSTGRES_DB', 'choynews')}")
    
    # Fallback to SQLite if PostgreSQL not configured
    if not all([os.getenv('POSTGRES_USER'), os.getenv('POSTGRES_PASSWORD')]):
        DATABASE_URL = "sqlite:///data/choynews_production.db"
    
    # API timeouts (production values)
    API_TIMEOUT = 30
    REQUEST_TIMEOUT = 15
    
    # Cache settings (longer TTL for production)
    CACHE_TTL = 1800  # 30 minutes
    REDIS_TTL = 3600  # 1 hour
    
    # Redis configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    
    # Rate limiting (stricter for production)
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_BURST = 10
    
    # News settings (production values)
    MAX_NEWS_PER_CATEGORY = 5
    NEWS_FETCH_INTERVAL = 900  # 15 minutes
    MAX_ARTICLES_PER_SOURCE = 3
    NEWS_RETENTION_DAYS = 7
    
    # Security settings
    ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",") if os.getenv("ALLOWED_USERS") else []
    ADMIN_USERS = os.getenv("ADMIN_USERS", "").split(",") if os.getenv("ADMIN_USERS") else []
    
    # SSL/TLS
    SSL_CERT_PATH = os.getenv("SSL_CERT_PATH")
    SSL_KEY_PATH = os.getenv("SSL_KEY_PATH")
    
    # Production features
    ENABLE_DEBUG_ENDPOINTS = False
    MOCK_EXTERNAL_APIS = False
    USE_SAMPLE_DATA = False
    
    # Monitoring
    ENABLE_METRICS = True
    METRICS_PORT = int(os.getenv("METRICS_PORT", 8080))
    HEALTH_CHECK_INTERVAL = 60
    
    # Performance optimization
    CONNECTION_POOL_SIZE = 20
    MAX_WORKERS = 4
    ASYNC_WORKERS = 8
    
    @classmethod
    def init_app(cls, app=None):
        """Initialize production-specific settings."""
        # Ensure production directories exist with proper permissions
        import stat
        
        directories = ["logs", "data", "data/cache", "data/static"]
        for directory in directories:
            os.makedirs(directory, mode=0o755, exist_ok=True)
        
        # Production logging setup with structured logging
        import logging.config
        import json
        
        try:
            with open("config/logging.json", "r") as f:
                logging_config = json.load(f)
                logging.config.dictConfig(logging_config)
        except FileNotFoundError:
            # Fallback to basic logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                handlers=[
                    logging.FileHandler(cls.LOG_FILE),
                    logging.StreamHandler()
                ]
            )
