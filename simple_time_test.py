#!/usr/bin/env python3
# Simple time format test

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting test...")

try:
    from news import get_local_time_str
    print("Successfully imported get_local_time_str")
    
    time_str = get_local_time_str()
    print(f"Local time: {time_str}")
except Exception as e:
    print(f"Error: {e}")

print("Test complete.")
