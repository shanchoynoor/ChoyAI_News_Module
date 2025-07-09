"""
User Logging Module for Choy News Bot.

This module handles tracking and logging user interactions with the bot.
"""

import os
import sqlite3
from datetime import datetime

from choynews.utils.logging import get_logger
from choynews.utils.config import Config

# Get logger
logger = get_logger(__name__)

# Database file path
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "user_logs.db")

def init_db():
    """Initialize the user logs database."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
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
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        interaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute('''
            INSERT INTO user_logs 
            (user_id, username, first_name, last_name, interaction_time, message_type, location, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, interaction_time, message_type, location, last_interaction))
        
        conn.commit()
        conn.close()
        logger.debug(f"Logged interaction for user {user_id}: {message_type}")
        return True
    except Exception as e:
        logger.error(f"Error logging user interaction: {e}")
        return False

def get_user_logs(user_id, limit=10):
    """
    Get recent logs for a specific user.
    
    Args:
        user_id (int): Telegram user ID
        limit (int, optional): Maximum number of logs to retrieve
        
    Returns:
        list: List of log dictionaries
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM user_logs 
            WHERE user_id = ? 
            ORDER BY interaction_time DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting user logs: {e}")
        return []

def get_active_users(days=7):
    """
    Get a list of active users within the specified number of days.
    
    Args:
        days (int, optional): Number of days to look back
        
    Returns:
        list: List of unique user IDs active in the specified period
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            SELECT DISTINCT user_id FROM user_logs 
            WHERE interaction_time >= datetime('now', ?) 
        ''', (f'-{days} days',))
        
        rows = c.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        return []

# Initialize the database when the module is imported
init_db()
