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
    """Configuration class for the Choy News Bot."""

    # Load environment variables from .env file if it exists
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # Telegram Bot Configuration
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

    # News API Configuration
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

    # Weather API Configuration
    WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY', '')

    # Holiday API Configuration
    CALENDARIFIC_API_KEY = os.getenv('CALENDARIFIC_API_KEY', '')

    # DeepSeek API Configuration
    DEEPSEEK_API = os.getenv('DEEPSEEK_API', '')

    # Twelve Data API Configuration
    TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', '')

    # Bot Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # File paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'choynews.log')

    @classmethod
    def validate_required_config(cls):
        """Validate that required configuration is present."""
        required_vars = {
            'TELEGRAM_BOT_TOKEN': cls.TELEGRAM_TOKEN,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        return True