#!/usr/bin/env python3
# Test script to verify news digest header formatting

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary functions
from news import get_local_time_str

def main():
    # Get the local time string
    now_str = get_local_time_str()
    print(f"Time string: {now_str}")
    
    # Format the digest header
    digest_header = f"*📢 DAILY NEWS DIGEST*\n_{now_str}_\n\n"
    
    print("News Digest Header (without markdown):")
    header_plain = digest_header.replace("*", "").replace("_", "")
    print(header_plain)
    
if __name__ == "__main__":
    main()
