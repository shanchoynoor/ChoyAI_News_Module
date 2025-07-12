# Pytest configuration for ChoyNewsBot
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test configuration
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch.dict(os.environ, {
        "TELEGRAM_TOKEN": "test_token_123456789",
        "LOG_LEVEL": "DEBUG",
        "DEEPSEEK_API": "test_deepseek_key",
        "WEATHERAPI_KEY": "test_weather_key"
    }):
        yield

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": 123456789,
        "username": "testuser", 
        "first_name": "Test",
        "last_name": "User",
        "chat_id": 123456789,
        "preferred_time": "08:00",
        "timezone": "Asia/Dhaka"
    }

# Configure test discovery
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Test markers
markers = [
    "unit: Unit tests",
    "integration: Integration tests", 
    "slow: Slow running tests",
    "api: Tests that require API access"
]
