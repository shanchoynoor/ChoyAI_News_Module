#!/usr/bin/env python3
"""
Test UV Index formatting with fallback behavior.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_uv_formatting():
    """Test UV Index formatting logic."""
    print("Testing UV Index formatting logic...")
    
    # Test with valid UV values
    test_values = [0, 0.0, 3.5, 7, 11.2, None, "5.3", "invalid", ""]
    
    for test_uv in test_values:
        print(f"\nTesting UV value: {repr(test_uv)}")
        
        # Apply the same logic as in the weather function
        uv = test_uv
        if uv is None:
            uv = 0
        
        # Ensure UV is a number and format it properly
        try:
            uv = float(uv)
            uv_str = f"{uv:.1f}"
        except (ValueError, TypeError):
            uv_str = "0.0"
        
        print(f"  → Formatted as: '{uv_str}'")
        
        # Test in weather section format
        weather_line = f"☀️ UV Index: {uv_str}"
        print(f"  → In weather format: '{weather_line}'")
    
    print("\n" + "="*50)
    print("Testing fallback weather section:")
    
    fallback_weather = """🌤️ WEATHER - Dhaka:
🌡️ Temperature: 25°C
☁️ Condition: Partly Cloudy
💧 Humidity: 70%
💨 Wind: 10 km/h N
☀️ UV Index: 3.0
🌬️ Air Quality: Moderate

"""
    
    print("Fallback weather output:")
    print(repr(fallback_weather))
    print("\nFormatted:")
    print(fallback_weather)
    
    # Check UV line in fallback
    if "☀️ UV Index:" in fallback_weather:
        lines = fallback_weather.split('\n')
        for line in lines:
            if "☀️ UV Index:" in line:
                print(f"✅ Found UV line: '{line}'")
                uv_value = line.split("☀️ UV Index:")[1].strip()
                print(f"✅ UV value extracted: '{uv_value}'")
                break

if __name__ == "__main__":
    test_uv_formatting()
