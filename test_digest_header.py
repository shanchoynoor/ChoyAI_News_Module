#!/usr/bin/env python3
# Test script to verify news digest header formatting

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting digest header test...")

try:
    # Import the necessary functions
    from news import get_local_time_str, build_news_digest

    # Test individual time string function
    print("Testing get_local_time_str:")
    time_str = get_local_time_str()
    print(f"Time string result: {time_str}")
    
    # Format a sample header using just get_local_time_str
    digest_header = f"*📢 DAILY NEWS DIGEST*\n_{time_str}_\n\n"
    header_plain = digest_header.replace("*", "").replace("_", "")
    print("Sample header (using get_local_time_str):")
    print(header_plain)
    
    # Now test the actual build_news_digest function to see what it outputs
    print("\nTesting build_news_digest:")
    full_digest = build_news_digest(return_msg=True)
    header_lines = full_digest.split("\n")[:3]  # Get first three lines
    header_text = "\n".join(header_lines)
    print("Actual digest header (from build_news_digest):")
    print(header_text.replace("*", "").replace("_", ""))
    
    print("\nBoth should show BDT as the timezone abbreviation.")
except Exception as e:
    print(f"Error: {e}")

print("Test complete.")
