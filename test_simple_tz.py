#!/usr/bin/env python3
# Simple test for the timezone display

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting test...")

# Import the function from news.py
from news import get_local_time_str

# Test with default timezone (Asia/Dhaka)
default_time = get_local_time_str()
print(f"Default time (should use Asia/Dhaka): {default_time}")

print("Test complete.")
