#!/usr/bin/env python3
"""
Test script for the news fetching and digest building system.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from choynews.core.advanced_news_fetcher import (
    init_news_history_db, get_breaking_local_news, get_breaking_global_news,
    get_breaking_tech_news, get_breaking_crypto_news, fetch_crypto_market_with_ai,
    get_dhaka_weather, get_bd_holidays, get_individual_crypto_stats
)
from choynews.core.digest_builder import build_news_digest
from choynews.utils.config import Config

def test_news_functions():
    """Test individual news fetching functions."""
    print("🧪 Testing News Fetching Functions\n")
    
    # Initialize database
    init_news_history_db()
    print("✅ News history database initialized")
    
    # Test weather
    print("\n🌤️ Testing weather data:")
    weather = get_dhaka_weather()
    if weather:
        print(weather)
    else:
        print("❌ Weather data not available")
    
    # Test holidays
    print("\n🎉 Testing holiday data:")
    holidays = get_bd_holidays()
    if holidays:
        print(holidays)
    else:
        print("ℹ️ No holidays today")
    
    # Test crypto market
    print("\n💰 Testing crypto market with AI:")
    crypto_market = fetch_crypto_market_with_ai()
    if crypto_market:
        print(crypto_market[:300] + "..." if len(crypto_market) > 300 else crypto_market)
    else:
        print("❌ Crypto market data not available")
    
    # Test individual crypto
    print("\n₿ Testing individual crypto (BTC):")
    btc_data = get_individual_crypto_stats("btc")
    if btc_data:
        print(btc_data[:300] + "..." if len(btc_data) > 300 else btc_data)
    else:
        print("❌ BTC data not available")

def test_news_sections():
    """Test news section functions."""
    print("\n📰 Testing News Sections\n")
    
    sections = [
        ("Local News", get_breaking_local_news),
        ("Global News", get_breaking_global_news),
        ("Tech News", get_breaking_tech_news),
        ("Crypto News", get_breaking_crypto_news),
    ]
    
    for name, func in sections:
        print(f"\n📰 Testing {name}:")
        try:
            news = func()
            if news:
                print(f"✅ {name} fetched successfully")
                print(news[:200] + "..." if len(news) > 200 else news)
            else:
                print(f"⚠️ {name} returned empty")
        except Exception as e:
            print(f"❌ {name} failed: {e}")

def test_digest_builder():
    """Test the complete digest builder."""
    print("\n📋 Testing Complete Digest Builder\n")
    
    try:
        digest = build_news_digest()
        if digest:
            print("✅ Digest built successfully!")
            print(f"📏 Length: {len(digest)} characters")
            print("\n📰 Digest Preview:")
            print(digest[:500] + "..." if len(digest) > 500 else digest)
        else:
            print("❌ Digest builder returned empty")
    except Exception as e:
        print(f"❌ Digest builder failed: {e}")

def main():
    """Run all tests."""
    print("🚀 ChoyNewsBot Advanced News System Test")
    print("=" * 50)
    
    # Check API keys
    print("\n🔑 Checking API Configuration:")
    
    apis = [
        ("TELEGRAM_TOKEN", Config.TELEGRAM_TOKEN),
        ("DEEPSEEK_API", Config.DEEPSEEK_API),
        ("WEATHERAPI_KEY", Config.WEATHERAPI_KEY),
        ("CALENDARIFIC_API_KEY", Config.CALENDARIFIC_API_KEY),
    ]
    
    for name, value in apis:
        if value:
            print(f"✅ {name}: {'*' * 8}{value[-4:]}")
        else:
            print(f"❌ {name}: Not set")
    
    # Run tests
    test_news_functions()
    test_news_sections()
    test_digest_builder()
    
    print("\n" + "=" * 50)
    print("🎉 Test Complete!")

if __name__ == "__main__":
    main()
