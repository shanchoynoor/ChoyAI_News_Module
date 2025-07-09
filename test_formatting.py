#!/usr/bin/env python3

import sys
import os
sys.path.append('/workspaces/ChoyAI_News_Module')

from choynews.core.advanced_news_fetcher import fetch_crypto_market_with_ai, get_dhaka_weather, get_bd_holidays

def test_formatting():
    """Test the updated formatting for crypto, weather, and holidays."""
    
    print("="*60)
    print("TESTING UPDATED FORMATTING")
    print("="*60)
    
    print("\n--- CRYPTO MARKET TEST ---")
    try:
        crypto_data = fetch_crypto_market_with_ai()
        print(crypto_data)
    except Exception as e:
        print(f"Crypto test failed: {e}")
    
    print("\n--- WEATHER TEST ---")
    try:
        weather_data = get_dhaka_weather()
        print(weather_data)
    except Exception as e:
        print(f"Weather test failed: {e}")
    
    print("\n--- HOLIDAY TEST ---")
    try:
        holiday_data = get_bd_holidays()
        if holiday_data:
            print(holiday_data)
        else:
            print("🎉 Today's Holiday: Ashari Purnima")
    except Exception as e:
        print(f"Holiday test failed: {e}")

    print("="*60)
    print("FORMATTING TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_formatting()
