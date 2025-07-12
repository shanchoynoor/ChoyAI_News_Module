"""
Time and timezone utilities for the Choy News application.

This module provides functions for handling time zones, formatting timestamps,
and scheduling logic based on time conditions.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone, all_timezones
from timezonefinder import TimezoneFinder
from .config import Config
from .logging import setup_logging

logger = setup_logging(__name__)

def get_bd_now():
    """Get current time in Bangladesh timezone (UTC+6)."""
    return datetime.now(timezone.utc) + timedelta(hours=6)

def get_bd_time_str(dt=None):
    """
    Return Bangladesh time as 'Jul 8, 2025 1:24AM BDT (UTC +6)'.
    
    Args:
        dt: Optional datetime object (defaults to current time)
        
    Returns:
        str: Formatted time string
    """
    if dt is None:
        dt = get_bd_now()
    date_str = dt.strftime("%b %-d, %Y %-I:%M%p")
    offset_hr = 6  # For Bangladesh
    return f"{date_str} BDT (UTC +{offset_hr})"

def set_user_timezone(user_id, tz_str):
    """
    Store a user's preferred timezone in the database.
    
    Args:
        user_id (int): Telegram user ID
        tz_str (str): Timezone string (e.g., 'Asia/Dhaka', 'Europe/London')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(Config.USER_TIMEZONE_DB)
        c = conn.cursor()
        # Create table if it doesn't exist
        c.execute("CREATE TABLE IF NOT EXISTS user_timezones (user_id INTEGER PRIMARY KEY, tz TEXT)")
        # Insert or update user's timezone
        c.execute("INSERT OR REPLACE INTO user_timezones (user_id, tz) VALUES (?, ?)", (user_id, tz_str))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to set user timezone: {e}")
        return False

def get_user_timezone(user_id):
    """
    Retrieve a user's preferred timezone from the database.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        str: Timezone string if found, None otherwise
    """
    try:
        conn = sqlite3.connect(Config.USER_TIMEZONE_DB)
        c = conn.cursor()
        # Create table if it doesn't exist
        c.execute("CREATE TABLE IF NOT EXISTS user_timezones (user_id INTEGER PRIMARY KEY, tz TEXT)")
        # Query user's timezone
        c.execute("SELECT tz FROM user_timezones WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return None
    except Exception as e:
        logger.error(f"Failed to get user timezone: {e}")
        return None

def parse_timezone_input(tz_input):
    """
    Parse user input to determine timezone.
    
    Handles various formats:
    - UTC offsets (e.g., '+6', '-5.5')
    - City names (e.g., 'dhaka', 'london')
    - Standard timezone names (e.g., 'Asia/Dhaka')
    
    Args:
        tz_input (str): User's timezone input
        
    Returns:
        str: Valid timezone string or None if not recognized
    """
    tz_input = tz_input.strip().lower()
    
    # Try UTC offset: +6, -5.5, etc.
    if tz_input.startswith("+utc"):
        tz_input = tz_input[4:].strip()
        
    if tz_input.startswith("+") or tz_input.startswith("-"):
        try:
            offset = float(tz_input)
            hours = int(offset)
            minutes = int((abs(offset) - abs(hours)) * 60)
            
            # Find a timezone with this offset
            utc_now = datetime.now(timezone.utc)
            for tz_name in all_timezones:
                tz = pytz_timezone(tz_name)
                tz_offset = utc_now.astimezone(tz).utcoffset().total_seconds() / 3600
                if abs(tz_offset - offset) < 0.01:  # Allow small difference due to floating point
                    return tz_name
                    
            # If no match found but valid offset, use a generic timezone name
            if -12 <= hours <= 14:
                sign = "+" if hours >= 0 else "-"
                return f"Etc/GMT{sign}{abs(hours)}"
        except Exception:
            pass
    
    # Try exact match with timezone database
    for tz in all_timezones:
        if tz_input == tz.lower():
            return tz
    
    # Try partial match (city name)
    for tz in all_timezones:
        if tz_input in tz.lower():
            return tz
    
    # Try common city names
    common_cities = {
        "dhaka": "Asia/Dhaka",
        "london": "Europe/London",
        "new york": "America/New_York",
        "la": "America/Los_Angeles",
        "tokyo": "Asia/Tokyo",
        "sydney": "Australia/Sydney",
        "berlin": "Europe/Berlin",
        "paris": "Europe/Paris",
        "delhi": "Asia/Kolkata",
        "moscow": "Europe/Moscow",
        "singapore": "Asia/Singapore"
    }
    
    for city, tz in common_cities.items():
        if city in tz_input or tz_input in city:
            return tz
            
    return None

def get_local_time_str(user_location=None, user_id=None):
    """
    Return current time string in user's local timezone.
    
    Format: 'Jul 7, 2025 8:38PM BST (UTC +1)'
    
    Args:
        user_location (dict, optional): Dictionary containing latitude and longitude.
        user_id (int, optional): User ID to look up timezone preference.
        
    Returns:
        str: Formatted time string with timezone abbreviation and UTC offset.
    """
    try:
        tz_str = None
        
        # First try to get timezone from user_id
        if user_id:
            tz_str = get_user_timezone(user_id)
        
        # Then try to get timezone from location
        if not tz_str and user_location:
            lat = user_location.get("latitude")
            lon = user_location.get("longitude")
            if lat and lon:
                tf = TimezoneFinder()
                tz_str = tf.timezone_at(lng=lon, lat=lat)
        
        # Default to Dhaka if no timezone specified
        if not tz_str:
            tz_str = "Asia/Dhaka"
            
        # Get the timezone object
        local_tz = pytz_timezone(tz_str)
        
        # Get current time in UTC and convert to the local timezone
        utc_now = datetime.utcnow()
        utc_now = pytz_timezone('UTC').localize(utc_now)
        local_now = utc_now.astimezone(local_tz)
        
        # Format: Jul 7, 2025 8:38PM
        date_str = local_now.strftime("%b %-d, %Y %-I:%M%p")
        
        # Get UTC offset in hours
        offset_hr = int(local_now.utcoffset().total_seconds() // 3600)
        
        # Common timezone abbreviations
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
        }
        
        # Get the timezone abbreviation
        tz_abbr = common_tz_abbr.get(tz_str, local_now.strftime('%Z'))
        
        # If the abbreviation is not helpful (sometimes it's just 'GMT+x' or '+xx')
        if not tz_abbr or tz_abbr.startswith('GMT') or len(tz_abbr) > 4 or tz_abbr.startswith('+'):
            tz_abbr = f"UTC{offset_hr:+d}"
        
        # Format the final timestamp
        if tz_abbr:
            return f"{date_str} {tz_abbr} (UTC {offset_hr:+d})"
        else:
            return f"{date_str} (UTC {offset_hr:+d})"
            
    except Exception as e:
        logger.error(f"Error formatting local time: {e}")
        # Fallback to a simple format
        return datetime.now().strftime("%b %-d, %Y %-I:%M%p")

def should_send_news(now=None):
    """
    Check if the current time (BDT) matches one of the scheduled send times:
    8:00am, 1:00pm, 7:00pm, or 11:00pm.
    
    Returns True only during the first minute of each scheduled hour.
    
    Args:
        now (datetime, optional): Datetime to check (defaults to current BDT time)
        
    Returns:
        bool: True if it's time to send news, False otherwise
    """
    if now is None:
        now = get_bd_now()
    
    # List of (hour, minute) tuples for sending news
    send_times = Config.SCHEDULED_TIMES
    
    # Only trigger on the exact minute
    current_time = (now.hour, now.minute)
    should_send = current_time in send_times
    
    if should_send:
        logger.info(f"Scheduled time matched: {now.hour}:{now.minute}")
    
    return should_send

def time_in_range(start, end, current):
    """
    Check if current time is in range [start, end].
    
    Args:
        start (tuple): Starting time as (hour, minute) tuple
        end (tuple): Ending time as (hour, minute) tuple
        current (tuple): Current time as (hour, minute) tuple
        
    Returns:
        bool: True if current time is within the range, False otherwise
    """
    start_mins = start[0] * 60 + start[1]
    end_mins = end[0] * 60 + end[1]
    current_mins = current[0] * 60 + current[1]
    
    if start_mins <= end_mins:
        return start_mins <= current_mins <= end_mins
    else:
        # Handle overnight ranges (e.g., 22:00 to 06:00)
        return start_mins <= current_mins or current_mins <= end_mins
