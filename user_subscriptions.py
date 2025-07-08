"""
User Subscription Management for News Digest Bot.

This module provides functionality to manage user subscriptions
for automatic news digest delivery at specific times in their local timezone.
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)

# Database file
SUBSCRIPTIONS_DB = "user_subscriptions.db"

def init_db():
    """Initialize the subscriptions database."""
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_active INTEGER DEFAULT 1,
                subscribed_at TEXT,
                last_news_sent TEXT,
                daily_count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Failed to initialize subscriptions database: {e}")
        return False

def subscribe_user(user_id, username=None, first_name=None, last_name=None):
    """
    Subscribe a user to receive automatic news digests.
    
    Args:
        user_id (int): Telegram user ID
        username (str, optional): Telegram username
        first_name (str, optional): User's first name
        last_name (str, optional): User's last name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if user already exists
        c.execute("SELECT is_active FROM subscriptions WHERE user_id = ?", (user_id,))
        existing = c.fetchone()
        
        if existing:
            # User exists, update subscription status
            c.execute("""
                UPDATE subscriptions 
                SET is_active = 1, username = ?, first_name = ?, last_name = ?, subscribed_at = ?
                WHERE user_id = ?
            """, (username, first_name, last_name, now, user_id))
            result = "updated"
        else:
            # New user, insert record
            c.execute("""
                INSERT INTO subscriptions 
                (user_id, username, first_name, last_name, is_active, subscribed_at) 
                VALUES (?, ?, ?, ?, 1, ?)
            """, (user_id, username, first_name, last_name, now))
            result = "created"
        
        conn.commit()
        conn.close()
        logging.info(f"User {user_id} subscription {result}")
        return True, result
    except Exception as e:
        logging.error(f"Failed to subscribe user {user_id}: {e}")
        return False, "error"

def unsubscribe_user(user_id):
    """
    Unsubscribe a user from receiving automatic news digests.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT is_active FROM subscriptions WHERE user_id = ?", (user_id,))
        existing = c.fetchone()
        
        if existing:
            # Set is_active to 0 instead of deleting the record
            c.execute("UPDATE subscriptions SET is_active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            logging.info(f"User {user_id} unsubscribed")
            return True
        else:
            conn.close()
            logging.warning(f"Attempted to unsubscribe non-existent user {user_id}")
            return False
    except Exception as e:
        logging.error(f"Failed to unsubscribe user {user_id}: {e}")
        return False

def get_all_subscribed_users():
    """
    Get a list of all active subscribed users.
    
    Returns:
        list: List of user_id integers
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        c.execute("SELECT user_id FROM subscriptions WHERE is_active = 1")
        users = [row[0] for row in c.fetchall()]
        conn.close()
        return users
    except Exception as e:
        logging.error(f"Failed to get subscribed users: {e}")
        return []

def get_users_for_local_time(target_hour):
    """
    Get users who should receive news based on their local time.
    
    Args:
        target_hour (int): The hour (0-23) in local time to target
        
    Returns:
        list: List of user_id integers
    """
    from news import get_user_timezone
    
    users_to_notify = []
    all_users = get_all_subscribed_users()
    
    for user_id in all_users:
        try:
            # Get user's timezone
            tz_str = get_user_timezone(user_id)
            if not tz_str:
                tz_str = 'Asia/Dhaka'  # Default to Dhaka if not set
                
            # Get current time in user's timezone
            user_tz = pytz.timezone(tz_str)
            user_time = datetime.now(pytz.UTC).astimezone(user_tz)
            
            # Check if user's local hour matches target hour
            if user_time.hour == target_hour:
                users_to_notify.append(user_id)
                
        except Exception as e:
            logging.error(f"Error checking time for user {user_id}: {e}")
    
    return users_to_notify

def get_users_for_scheduled_times():
    """
    Get users who should receive news based on the scheduled times (8am, 1pm, 7pm, 11pm)
    in their local timezone.
    
    Returns:
        list: List of user_id integers
    """
    # Get current UTC time
    now_utc = datetime.now(pytz.UTC)
    
    # Scheduled hours (in 24-hour format)
    scheduled_hours = [8, 13, 19, 23]  # 8am, 1pm, 7pm, 11pm
    
    # Check if the current UTC hour is a scheduled hour for any timezone
    users_to_notify = []
    
    # Since timezones range from UTC-12 to UTC+14, check all possible hours
    for hour_offset in range(-12, 15):
        # Calculate what hour it is in this timezone
        target_hour_utc = (now_utc.hour - hour_offset) % 24
        
        # If this hour is a scheduled time, get users in this timezone
        if target_hour_utc in scheduled_hours:
            local_hour = (now_utc.hour + hour_offset) % 24
            users = get_users_for_local_time(local_hour)
            users_to_notify.extend(users)
    
    return users_to_notify

def update_last_sent(user_id):
    """
    Update the last_news_sent timestamp and increment the daily count.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get current daily count
        c.execute("SELECT last_news_sent, daily_count FROM subscriptions WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        
        if row:
            last_sent_str, daily_count = row
            
            # Check if it's a new day
            if last_sent_str:
                last_sent = datetime.strptime(last_sent_str, "%Y-%m-%d %H:%M:%S")
                now_dt = datetime.utcnow()
                
                # Reset count if it's a new day
                if now_dt.date() > last_sent.date():
                    daily_count = 1
                else:
                    daily_count += 1
            else:
                daily_count = 1
                
            # Update the record
            c.execute("""
                UPDATE subscriptions 
                SET last_news_sent = ?, daily_count = ? 
                WHERE user_id = ?
            """, (now, daily_count, user_id))
            
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    except Exception as e:
        logging.error(f"Failed to update last_sent for user {user_id}: {e}")
        return False

def is_subscribed(user_id):
    """
    Check if a user is actively subscribed.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if subscribed, False otherwise
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        c.execute("SELECT is_active FROM subscriptions WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        return row is not None and row[0] == 1
    except Exception as e:
        logging.error(f"Failed to check subscription status for user {user_id}: {e}")
        return False

# Initialize the database when the module is imported
init_db()
