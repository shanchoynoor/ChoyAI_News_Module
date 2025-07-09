"""
Data models for the Choy News application.

This module provides functions for interacting with user data, subscriptions, and logs.
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta
import pytz
from choynews.utils.logging import get_logger
from choynews.utils.config import Config
from choynews.utils.time_utils import time_in_range

logger = get_logger(__name__)

# Initialize database paths
USER_SUBSCRIPTIONS_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "user_subscriptions.db")
USER_LOGS_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "user_logs.db")

def init_user_subscriptions_db():
    """Initialize the user subscriptions database."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(USER_SUBSCRIPTIONS_DB), exist_ok=True)
        
        conn = sqlite3.connect(USER_SUBSCRIPTIONS_DB)
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
                last_updated TEXT,
                last_sent TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("User subscriptions database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing user subscriptions database: {e}")
        raise

def init_user_logs_db():
    """Initialize the user logs database."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(USER_LOGS_DB), exist_ok=True)
        
        conn = sqlite3.connect(USER_LOGS_DB)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                interaction_time TEXT,
                message_type TEXT,
                location TEXT,
                last_interaction TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("User logs database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing user logs database: {e}")
        raise

def get_users_for_scheduled_times(hour, minute):
    """
    Get users who have subscribed to receive digests at the specified time.
    
    Args:
        hour (int): Hour of day (0-23)
        minute (int): Minute of hour (0-59)
        
    Returns:
        list: List of user dictionaries
    """
    target_time = f"{hour:02d}:{minute:02d}"
    users = []
    
    try:
        conn = sqlite3.connect(USER_SUBSCRIPTIONS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM subscriptions 
            WHERE preferred_time = ? AND is_active = 1
        ''', (target_time,))
        
        rows = c.fetchall()
        for row in rows:
            users.append(dict(row))
            
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error getting users for scheduled time {target_time}: {e}")
        return []

def get_all_subscribed_users():
    """
    Get all active subscribed users.
    
    Returns:
        list: List of user dictionaries
    """
    try:
        conn = sqlite3.connect(USER_SUBSCRIPTIONS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM subscriptions WHERE is_active = 1")
        rows = c.fetchall()
        
        users = [dict(row) for row in rows]
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error getting all subscribed users: {e}")
        return []

def update_last_sent(user_id, timestamp=None):
    """
    Update the last_sent timestamp for a user.
    
    Args:
        user_id (int): The user ID
        timestamp (str, optional): The timestamp string. If None, current time is used.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    try:
        conn = sqlite3.connect(USER_SUBSCRIPTIONS_DB)
        c = conn.cursor()
        
        c.execute('''
            UPDATE subscriptions 
            SET last_sent = ? 
            WHERE user_id = ?
        ''', (timestamp, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating last_sent for user {user_id}: {e}")
        return False

def log_user_interaction(user_id, username, first_name, last_name, message_type, location=None, last_interaction=None):
    """
    Log a user interaction with the bot.
    
    Args:
        user_id (int): Telegram user ID
        username (str): Telegram username
        first_name (str): User's first name
        last_name (str): User's last name
        message_type (str): Type of interaction (e.g., 'command', 'message', 'callback')
        location (str, optional): User's location if provided
        last_interaction (str, optional): Description of the interaction
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(USER_LOGS_DB)
        c = conn.cursor()
        interaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute('''
            INSERT INTO user_logs 
            (user_id, username, first_name, last_name, interaction_time, message_type, location, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, interaction_time, message_type, location, last_interaction))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error logging user interaction: {e}")
        return False

# Initialize databases when module is imported
init_user_subscriptions_db()
init_user_logs_db()
