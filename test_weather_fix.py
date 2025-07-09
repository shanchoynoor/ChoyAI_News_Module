#!/usr/bin/env python3
"""
Quick test to verify weather UV Index formatting is working properly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from choynews.core.advanced_news_fetcher import get_dhaka_weather

def test_weather_formatting():
    """Test that weather data includes properly formatted UV Index."""
    print("Testing weather formatting...")
    
    try:
        weather_data = get_dhaka_weather()
        print("Weather output:")
        print(repr(weather_data))  # Use repr to see raw string
        print("\nFormatted output:")
        print(weather_data)
        
        if not weather_data:
            print("❌ No weather data returned")
            return
        
        # Check if UV Index is properly formatted
        if "☀️ UV Index:" in weather_data:
            print("✅ UV Index section found")
            
            # Extract UV line
            lines = weather_data.split('\n')
            uv_line = None
            for line in lines:
                if "☀️ UV Index:" in line:
                    uv_line = line
                    break
            
            if uv_line:
                print(f"✅ UV Index line: '{uv_line}'")
                
                # Check if there's a value after the colon
                uv_part = uv_line.split("☀️ UV Index:")[1].strip()
                if uv_part:
                    print(f"✅ UV Index value: '{uv_part}'")
                    
                    # Check if it's a valid number format
                    try:
                        float(uv_part)
                        print("✅ UV Index is properly formatted as a number")
                    except ValueError:
                        print(f"❌ UV Index value '{uv_part}' is not a valid number")
                else:
                    print("❌ No UV Index value found")
            else:
                print("❌ UV Index line not found")
        else:
            print("❌ UV Index section not found")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_weather_formatting()
