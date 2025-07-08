#!/usr/bin/env python3
# Test script for timezone formatting with specific focus on Etc/GMT timezones

import os
import sys
import pytz
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Script started")

try:
    # Import the necessary functions
    from news import parse_timezone_input, get_local_time_str
    
    def test_timezone_format():
        # Test specifically with Etc/GMT-6 (which should be UTC+6)
        tz_str = 'Etc/GMT-6'
        
        # Get the timezone object
        local_tz = pytz.timezone(tz_str)
        
        # Get current time in UTC and convert to the local timezone
        utc_now = datetime.utcnow()
        utc_now = pytz.timezone('UTC').localize(utc_now)
        local_now = utc_now.astimezone(local_tz)
        
        # Get timezone abbreviation
        tz_abbr = local_now.strftime('%Z')
        print(f"Timezone abbreviation for '{tz_str}': '{tz_abbr}'")
        
        # Create a sample timestamp to see what it looks like with different formats
        date_str = local_now.strftime("%b %-d, %Y %-I:%M%p")
        offset_hr = int(local_now.utcoffset().total_seconds() // 3600)
        
        print(f"Date string: {date_str}")
        print(f"Offset hours: {offset_hr}")
        
        # Various formats
        print(f"Format 1: {date_str} {tz_abbr} (UTC {offset_hr:+d})")
        print(f"Format 2: {date_str} +{offset_hr:02d} (UTC +{offset_hr})")
        print(f"Format 3: {date_str} BDT (UTC +{offset_hr})")
        
        # Now test for Asia/Dhaka
        dhaka_tz = pytz.timezone('Asia/Dhaka')
        dhaka_now = utc_now.astimezone(dhaka_tz)
        dhaka_abbr = dhaka_now.strftime('%Z')
        dhaka_date_str = dhaka_now.strftime("%b %-d, %Y %-I:%M%p")
        dhaka_offset_hr = int(dhaka_now.utcoffset().total_seconds() // 3600)
        
        print(f"\nTimezone abbreviation for 'Asia/Dhaka': '{dhaka_abbr}'")
        print(f"Asia/Dhaka date string: {dhaka_date_str}")
        print(f"Asia/Dhaka offset hours: {dhaka_offset_hr}")
        
        print(f"Dhaka Format 1: {dhaka_date_str} {dhaka_abbr} (UTC {dhaka_offset_hr:+d})")
        print(f"Dhaka Format 2: {dhaka_date_str} +{dhaka_offset_hr:02d} (UTC +{dhaka_offset_hr})")
        print(f"Dhaka Format 3: {dhaka_date_str} BDT (UTC +{dhaka_offset_hr})")
    
    print("Testing timezone formats...")
    test_timezone_format()
    
    # Test what actually gets returned from get_local_time_str
    print("\nTesting get_local_time_str with different timezones:")
    
    # Test with Asia/Dhaka
    print(f"Asia/Dhaka: {get_local_time_str(None, None)}")
    
    # Test with simulated user_id that has Etc/GMT-6 timezone
    # Mock the get_user_timezone function for testing
    def mock_user_with_etc_gmt():
        # Create a test user and timezone in a temporary dict
        temp_user_tz = {'test_user': 'Etc/GMT-6'}
        
        # Define a temp get_timezone function
        def get_test_timezone(user_id):
            return temp_user_tz.get(user_id, None)
        
        # Now call get_local_time_str with this mocked function
        # Since we can't easily mock the function call, we'll try to test directly
        try:
            # Manual implementation of get_local_time_str logic for Etc/GMT-6
            tz_str = 'Etc/GMT-6'
            local_tz = pytz.timezone(tz_str)
            utc_now = datetime.utcnow()
            utc_now = pytz.timezone('UTC').localize(utc_now)
            local_now = utc_now.astimezone(local_tz)
            date_str = local_now.strftime("%b %-d, %Y %-I:%M%p")
            offset_hr = int(local_now.utcoffset().total_seconds() // 3600)
            
            # Common timezone abbreviations (from the function)
            common_tz_abbr = {
                'Asia/Dhaka': 'BDT',
                'Europe/London': 'BST', 
                'Europe/Paris': 'CEST',
                'America/New_York': 'EDT',
                'America/Chicago': 'CDT',
                'America/Denver': 'MDT',
                'America/Los_Angeles': 'PDT',
                'Asia/Kolkata': 'IST',
                'Asia/Tokyo': 'JST',
                'Asia/Singapore': 'SGT',
                'Australia/Sydney': 'AEST',
                'UTC': 'UTC',
                'Etc/GMT-6': 'BDT',  # Manually add this mapping for testing
            }
            
            # Get the timezone abbreviation
            tz_abbr = common_tz_abbr.get(tz_str, local_now.strftime('%Z'))
            
            # Format the final timestamp
            if tz_abbr:
                time_str = f"{date_str} {tz_abbr} (UTC {offset_hr:+d})"
            else:
                time_str = f"{date_str} (UTC {offset_hr:+d})"
                
            print(f"Simulated user with Etc/GMT-6: {time_str}")
        except Exception as e:
            print(f"Error in mock test: {e}")
    
    mock_user_with_etc_gmt()
    
except Exception as e:
    print(f"Error: {e}")
