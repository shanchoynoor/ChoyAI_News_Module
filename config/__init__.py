"""
Configuration factory for ChoyNewsBot.
"""
import os
from .base_config import BaseConfig
from .dev_config import DevelopmentConfig
from .prod_config import ProductionConfig
from .test_config import TestingConfig


def get_config():
    """
    Get configuration based on environment.
    
    Returns:
        Config class appropriate for current environment
    """
    env = os.getenv("ENVIRONMENT", "production").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
        "production": ProductionConfig,
        "prod": ProductionConfig,
        "testing": TestingConfig,
        "test": TestingConfig
    }
    
    config_class = config_map.get(env, ProductionConfig)
    
    # Initialize app-specific settings
    config_class.init_app()
    
    return config_class


def create_config_from_env():
    """Create and validate configuration from environment."""
    config = get_config()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        import logging
        logging.error(f"Configuration validation failed: {e}")
        raise
    
    return config


# For backward compatibility with existing code
Config = get_config()
