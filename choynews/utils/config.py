"""
Configuration management for the Choy News application.

This module loads and provides access to all configuration settings
from environment variables and config files.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class that loads from environment variables."""
    
    # Telegram configuration
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    AUTO_NEWS_CHAT_ID = os.getenv("AUTO_NEWS_CHAT_ID")
    
    # API keys
    DEEPSEEK_API = os.getenv("DEEPSEEK_API")
    CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY")
    WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")
    TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
    
    # Application settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/choynews.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 3))
    
    # Scheduled times (24-hour format)
    SCHEDULED_TIMES = [(8, 0), (13, 0), (19, 0), (23, 0)]
    
    # Data file paths
    COINLIST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "coinlist.json")
    USER_TIMEZONE_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "user_timezones.db")
    USER_SUBSCRIPTIONS_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "user_subscriptions.db")
    USER_LOGS_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "user_logs.db")
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        missing = []
        
        if not cls.TELEGRAM_TOKEN:
            missing.append("TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
