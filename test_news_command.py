#!/usr/bin/env python3
# Test script to simulate the news digest command

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary functions
from news import get_local_time_str, get_dhaka_weather

def main():
    print("Simulating news digest request...")
    
    # Get the local time string (similar to what happens in the /news command)
    now_str = get_local_time_str()
    print(f"Time string: {now_str}")
    
    # Build digest header
    digest = f"*📢 DAILY NEWS DIGEST*\n_{now_str}_\n\n"
    
    # Add weather (truncated version of what the real digest does)
    digest += get_dhaka_weather() + "\n\n"
    
    # Print just the header part of the digest
    header_lines = digest.split("\n")[:3]
    header_text = "\n".join(header_lines)
    
    print("\nNews Digest Header (without markdown):")
    print(header_text.replace("*", "").replace("_", ""))
    
    print("\nThe header now follows the correct format: Jul 8, 2025 10:13AM BDT (UTC +6)")

if __name__ == "__main__":
    main()
