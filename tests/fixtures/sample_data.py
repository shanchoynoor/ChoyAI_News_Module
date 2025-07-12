"""
Test fixtures and mock data for ChoyNewsBot testing.
"""
import json
from datetime import datetime

# Sample RSS feed response
SAMPLE_RSS_FEED = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test News Feed</title>
        <description>Sample news for testing</description>
        <item>
            <title>Bitcoin reaches new heights amid institutional adoption</title>
            <link>https://example.com/crypto-news-1</link>
            <description>Major financial institutions continue to embrace cryptocurrency</description>
            <pubDate>Fri, 12 Jul 2025 10:00:00 GMT</pubDate>
            <guid>crypto-news-1</guid>
        </item>
        <item>
            <title>Bangladesh announces new digital infrastructure initiative</title>
            <link>https://example.com/bd-news-1</link>
            <description>Government unveils comprehensive digital transformation plan</description>
            <pubDate>Fri, 12 Jul 2025 09:30:00 GMT</pubDate>
            <guid>bd-news-1</guid>
        </item>
        <item>
            <title>Global tech summit focuses on AI ethics and regulation</title>
            <link>https://example.com/tech-news-1</link>
            <description>Industry leaders discuss responsible AI development</description>
            <pubDate>Fri, 12 Jul 2025 09:00:00 GMT</pubDate>
            <guid>tech-news-1</guid>
        </item>
    </channel>
</rss>'''

# Sample crypto market data
SAMPLE_CRYPTO_DATA = {
    "bitcoin": {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 105000,
        "price_change_percentage_24h": 2.5,
        "market_cap": 2000000000000,
        "market_cap_rank": 1,
        "total_volume": 45000000000
    },
    "ethereum": {
        "id": "ethereum", 
        "symbol": "eth",
        "name": "Ethereum",
        "current_price": 3800,
        "price_change_percentage_24h": 1.8,
        "market_cap": 450000000000,
        "market_cap_rank": 2,
        "total_volume": 20000000000
    }
}

# Sample weather data
SAMPLE_WEATHER_DATA = {
    "location": {
        "name": "Dhaka",
        "country": "Bangladesh",
        "localtime": "2025-07-12 16:00"
    },
    "current": {
        "temp_c": 32.0,
        "condition": {
            "text": "Partly cloudy"
        },
        "humidity": 75,
        "wind_kph": 15.5,
        "vis_km": 8.0,
        "uv": 6,
        "air_quality": {
            "us-epa-index": 3
        }
    }
}

# Sample user data
SAMPLE_USER_DATA = {
    "user_id": 123456789,
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "chat_id": 123456789,
    "preferred_time": "08:00",
    "timezone": "Asia/Dhaka",
    "subscription_active": True,
    "created_at": "2025-07-12T10:00:00Z"
}

# Sample Telegram message
SAMPLE_TELEGRAM_MESSAGE = {
    "update_id": 123456,
    "message": {
        "message_id": 789,
        "from": SAMPLE_USER_DATA,
        "chat": {
            "id": 123456789,
            "type": "private"
        },
        "date": 1720785600,
        "text": "/start"
    }
}

# Sample API responses for mocking
MOCK_RESPONSES = {
    "telegram_getme": {
        "ok": True,
        "result": {
            "id": 987654321,
            "is_bot": True,
            "first_name": "ChoyNewsBot",
            "username": "choynewsbot",
            "can_join_groups": True,
            "can_read_all_group_messages": False,
            "supports_inline_queries": False
        }
    },
    "telegram_send_message": {
        "ok": True,
        "result": {
            "message_id": 790,
            "from": {
                "id": 987654321,
                "is_bot": True,
                "first_name": "ChoyNewsBot",
                "username": "choynewsbot"
            },
            "chat": {
                "id": 123456789,
                "type": "private"
            },
            "date": 1720785660,
            "text": "Message sent successfully"
        }
    }
}

def get_sample_rss_feed():
    """Return sample RSS feed for testing."""
    return SAMPLE_RSS_FEED

def get_sample_crypto_data():
    """Return sample cryptocurrency data."""
    return SAMPLE_CRYPTO_DATA

def get_sample_weather_data():
    """Return sample weather data."""
    return SAMPLE_WEATHER_DATA

def get_sample_user_data():
    """Return sample user data."""
    return SAMPLE_USER_DATA.copy()

def get_sample_telegram_message():
    """Return sample Telegram message."""
    return SAMPLE_TELEGRAM_MESSAGE

def get_mock_response(response_type):
    """Get mock API response by type."""
    return MOCK_RESPONSES.get(response_type, {})

# Test database configurations
TEST_DB_CONFIG = {
    "user_subscriptions_db": ":memory:",  # In-memory SQLite for testing
    "user_logs_db": ":memory:",
    "news_history_db": ":memory:"
}

def create_test_config():
    """Create test configuration with safe defaults."""
    return {
        "TELEGRAM_TOKEN": "test_token_123456789",
        "LOG_LEVEL": "DEBUG", 
        "LOG_FILE": "/tmp/test_choynews.log",
        "DEEPSEEK_API": "test_deepseek_key",
        "WEATHERAPI_KEY": "test_weather_key",
        "CALENDARIFIC_API_KEY": "test_calendar_key",
        **TEST_DB_CONFIG
    }
