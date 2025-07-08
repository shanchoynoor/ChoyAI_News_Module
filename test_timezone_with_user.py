#!/usr/bin/env python3
# Test timezone handling with user_id

import os
import sys
import sqlite3

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting user timezone test...")

try:
    # Import the necessary functions
    from news import get_local_time_str, set_user_timezone, get_user_timezone
    
    # Set up a test user ID
    test_user_id = 999999
    
    # Test timezones to try
    test_timezones = [
        "Asia/Dhaka",
        "Etc/GMT-6",
        "+6"  # This should be converted to Etc/GMT-6
    ]
    
    print("Testing each timezone option:")
    for tz in test_timezones:
        # First, if tz is "+6", we need to convert it
        if tz.startswith("+"):
            from news import parse_timezone_input
            tz_db = parse_timezone_input(tz)
            print(f"Converted '{tz}' to '{tz_db}'")
        else:
            tz_db = tz
        
        # Set the timezone for our test user
        set_user_timezone(test_user_id, tz_db)
        
        # Verify it was set correctly
        stored_tz = get_user_timezone(test_user_id)
        print(f"Set timezone '{tz_db}', retrieved from DB: '{stored_tz}'")
        
        # Now get the time string for this user
        time_str = get_local_time_str(user_id=test_user_id)
        print(f"Time string for user with '{tz_db}': {time_str}")
        print()
    
    # Clean up - remove test user from database
    try:
        conn = sqlite3.connect("user_timezones.db")
        c = conn.cursor()
        c.execute("DELETE FROM user_timezones WHERE user_id = ?", (test_user_id,))
        conn.commit()
        conn.close()
        print("Cleaned up test user from database.")
    except Exception as e:
        print(f"Error cleaning up: {e}")
    
except Exception as e:
    print(f"Error: {e}")

print("Test complete.")
