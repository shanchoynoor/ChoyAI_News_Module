"""
User Subscription Management for Choy News Bot.

This module provides functionality to manage user subscriptions
for automatic news digest delivery at specific times in their local timezone.
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
import pytz

from choynews.utils.logging import get_logger
from choynews.utils.config import Config

# Get logger
logger = get_logger(__name__)

# Database file path
SUBSCRIPTIONS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "user_subscriptions.db")

def init_db():
    """Initialize the subscriptions database."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(SUBSCRIPTIONS_DB), exist_ok=True)
        
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                preferred_time TEXT,
                timezone TEXT,
                is_active INTEGER DEFAULT 1,
                crypto_alerts INTEGER DEFAULT 1,
                market_updates INTEGER DEFAULT 1,
                weather_info INTEGER DEFAULT 1,
                world_news INTEGER DEFAULT 1,
                tech_news INTEGER DEFAULT 1,
                created_at TEXT,
                last_updated TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Subscription database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def add_subscription(user_id, chat_id, username, first_name, last_name, preferred_time, timezone):
    """
    Add a new user subscription to the database.
    
    Args:
        user_id (int): Telegram user ID
        chat_id (int): Telegram chat ID
        username (str): Telegram username
        first_name (str): User's first name
        last_name (str): User's last name
        preferred_time (str): Time in format "HH:MM" for news delivery
        timezone (str): IANA timezone string (e.g., "America/New_York")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute('''
            INSERT OR REPLACE INTO subscriptions 
            (user_id, chat_id, username, first_name, last_name, preferred_time, timezone, created_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, chat_id, username, first_name, last_name, preferred_time, timezone, now, now))
        
        conn.commit()
        conn.close()
        logger.info(f"Added subscription for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding subscription: {e}")
        return False

def update_subscription_preference(user_id, preference_name, value):
    """
    Update a user's subscription preference.
    
    Args:
        user_id (int): Telegram user ID
        preference_name (str): Name of the preference to update
        value (int): New value (0 for off, 1 for on)
        
    Returns:
        bool: True if successful, False otherwise
    """
    valid_preferences = [
        'is_active', 'crypto_alerts', 'market_updates', 
        'weather_info', 'world_news', 'tech_news'
    ]
    
    if preference_name not in valid_preferences:
        logger.error(f"Invalid preference name: {preference_name}")
        return False
    
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = f"UPDATE subscriptions SET {preference_name} = ?, last_updated = ? WHERE user_id = ?"
        c.execute(query, (value, now, user_id))
        
        if c.rowcount == 0:
            logger.warning(f"No subscription found for user {user_id}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        logger.info(f"Updated {preference_name} to {value} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating subscription preference: {e}")
        return False

def update_delivery_time(user_id, preferred_time, timezone=None):
    """
    Update a user's preferred delivery time and optionally timezone.
    
    Args:
        user_id (int): Telegram user ID
        preferred_time (str): Time in format "HH:MM" for news delivery
        timezone (str, optional): IANA timezone string (e.g., "America/New_York")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if timezone:
            c.execute('''
                UPDATE subscriptions 
                SET preferred_time = ?, timezone = ?, last_updated = ? 
                WHERE user_id = ?
            ''', (preferred_time, timezone, now, user_id))
        else:
            c.execute('''
                UPDATE subscriptions 
                SET preferred_time = ?, last_updated = ? 
                WHERE user_id = ?
            ''', (preferred_time, now, user_id))
        
        if c.rowcount == 0:
            logger.warning(f"No subscription found for user {user_id}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        logger.info(f"Updated delivery time to {preferred_time} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating delivery time: {e}")
        return False

def get_subscription(user_id):
    """
    Get a user's subscription details.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        dict: User subscription details or None if not found
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        else:
            logger.warning(f"No subscription found for user {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        return None

def get_active_subscriptions_by_time(hour, minute):
    """
    Get all active subscriptions for a specific delivery time.
    
    Args:
        hour (int): Hour (0-23)
        minute (int): Minute (0-59)
        
    Returns:
        list: List of subscription dictionaries
    """
    target_time = f"{hour:02d}:{minute:02d}"
    
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM subscriptions 
            WHERE preferred_time = ? AND is_active = 1
        ''', (target_time,))
        
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting subscriptions for time {target_time}: {e}")
        return []

def get_active_subscriptions_by_timezone(timezone_str):
    """
    Get all active subscriptions for a specific timezone.
    
    Args:
        timezone_str (str): IANA timezone string (e.g., "America/New_York")
        
    Returns:
        list: List of subscription dictionaries
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM subscriptions 
            WHERE timezone = ? AND is_active = 1
        ''', (timezone_str,))
        
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting subscriptions for timezone {timezone_str}: {e}")
        return []

def delete_subscription(user_id):
    """
    Delete a user's subscription.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        c = conn.cursor()
        
        c.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
        
        if c.rowcount == 0:
            logger.warning(f"No subscription found for user {user_id}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        logger.info(f"Deleted subscription for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        return False

def get_all_subscriptions():
    """
    Get all subscriptions in the database.
    
    Returns:
        list: List of subscription dictionaries
    """
    try:
        conn = sqlite3.connect(SUBSCRIPTIONS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM subscriptions")
        rows = c.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all subscriptions: {e}")
        return []

# Initialize the database when the module is imported
init_db()
