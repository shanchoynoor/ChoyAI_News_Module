"""
Tests for the config utility module.
"""
import pytest
from choynews.utils.config import Config

def test_config_exists():
    """Test that the Config class exists."""
    assert hasattr(Config, 'validate')

def test_config_validation():
    """Test that config validation works."""
    # This will pass if TELEGRAM_TOKEN is set or fail with a specific error
    try:
        Config.validate()
        # If we get here, validation passed (TELEGRAM_TOKEN is set)
        assert True
    except ValueError as e:
        # Validation failed, but we expect a specific error message
        assert "Missing required environment variables: TELEGRAM_TOKEN" in str(e)
