"""
Base configuration class for ChoyNewsBot.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BaseConfig:
    """Base configuration with common settings."""
    
    # Application info
    APP_NAME = "ChoyNewsBot"
    APP_VERSION = "2.0.0"
    
    # Telegram configuration
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    AUTO_NEWS_CHAT_ID = os.getenv("AUTO_NEWS_CHAT_ID")
    
    # API keys
    DEEPSEEK_API = os.getenv("DEEPSEEK_API")
    CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY")
    WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")
    TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
    
    # Scheduled times (24-hour format)
    SCHEDULED_TIMES = [(8, 0), (13, 0), (19, 0), (23, 0)]
    
    # Data file paths (relative to project root)
    COINLIST_PATH = "data/static/coinlist.json"
    USER_TIMEZONE_DB = "data/user_timezones.db"
    USER_SUBSCRIPTIONS_DB = "data/user_subscriptions.db"
    USER_LOGS_DB = "data/user_logs.db"
    
    # Default settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/choynews.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 3))
    
    # API settings
    API_TIMEOUT = 30
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3
    
    # News settings
    MAX_NEWS_PER_CATEGORY = 5
    NEWS_FETCH_INTERVAL = 900  # 15 minutes
    MAX_ARTICLES_PER_SOURCE = 3
    NEWS_RETENTION_DAYS = 7
    NEWS_TIME_WINDOW_HOURS = 3
    
    # Cache settings
    CACHE_TTL = 1800  # 30 minutes
    CRYPTO_CACHE_TTL = 300  # 5 minutes
    WEATHER_CACHE_TTL = 1800  # 30 minutes
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_BURST = 10
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        missing = []
        
        if not cls.TELEGRAM_TOKEN:
            missing.append("TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def get_config_summary(cls):
        """Get a summary of current configuration (safe for logging)."""
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "log_level": cls.LOG_LEVEL,
            "telegram_configured": bool(cls.TELEGRAM_TOKEN),
            "deepseek_configured": bool(cls.DEEPSEEK_API),
            "weather_configured": bool(cls.WEATHERAPI_KEY),
            "calendar_configured": bool(cls.CALENDARIFIC_API_KEY),
            "scheduled_times": cls.SCHEDULED_TIMES,
            "max_news_per_category": cls.MAX_NEWS_PER_CATEGORY
        }
