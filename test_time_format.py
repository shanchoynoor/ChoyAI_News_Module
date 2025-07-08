#!/usr/bin/env python3
# Test script to verify time string formatting

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary functions
from news import get_local_time_str, get_bd_time_str

def main():
    # Test the local time string function (should use Asia/Dhaka by default)
    local_time_str = get_local_time_str()
    print(f"Local time string: {local_time_str}")
    
    # Test the BD time string function
    bd_time_str = get_bd_time_str()
    print(f"BD time string: {bd_time_str}")
    
    # Both should have a similar format: Jul 8, 2025 10:13AM BDT (UTC +6)
    
if __name__ == "__main__":
    main()
