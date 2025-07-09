"""
Bot service module for Choy News Bot.

This module handles Telegram bot messages and commands.
"""

import logging
import json
from choynews.utils.logging import get_logger
from choynews.data.models import log_user_interaction

logger = get_logger(__name__)

def handle_updates(updates):
    """
    Process Telegram update objects and handle messages/commands.
    
    Args:
        updates (list): List of Telegram update objects
        
    Returns:
        int: ID of the last processed update or None
    """
    if not updates:
        return None
        
    last_update_id = None
    
    for update in updates:
        last_update_id = update.get("update_id")
        
        # Handle message updates
        if "message" in update:
            message = update["message"]
            handle_message(message)
            
        # Handle callback query updates (inline keyboard buttons)
        elif "callback_query" in update:
            callback_query = update["callback_query"]
            handle_callback_query(callback_query)
            
    return last_update_id + 1 if last_update_id is not None else None

def handle_message(message):
    """
    Handle a message from a Telegram user.
    
    Args:
        message (dict): Telegram message object
    """
    # Extract message data
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    username = message.get("from", {}).get("username")
    first_name = message.get("from", {}).get("first_name")
    last_name = message.get("from", {}).get("last_name")
    text = message.get("text", "")
    
    if not text or not chat_id:
        return
        
    # Log the interaction
    log_user_interaction(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        message_type="message",
        last_interaction=text[:100]  # Truncate long messages
    )
    
    logger.info(f"Received message from {username or user_id}: {text[:50]}")
    
    # Process commands (messages starting with /)
    if text.startswith('/'):
        handle_command(chat_id, user_id, username, first_name, last_name, text)
    else:
        # Handle regular messages
        pass

def handle_command(chat_id, user_id, username, first_name, last_name, text):
    """
    Handle a command from a Telegram user.
    
    Args:
        chat_id (int): Telegram chat ID
        user_id (int): Telegram user ID
        username (str): Telegram username
        first_name (str): User's first name
        last_name (str): User's last name
        text (str): Command text
    """
    # Split the command and arguments
    parts = text.split(' ', 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    logger.info(f"Processing command: {command} with args: {args[:50]}")
    
    # Implement command handlers here
    # For example:
    # if command == '/start':
    #     handle_start_command(chat_id, user_id, username, first_name, last_name)
    # elif command == '/help':
    #     handle_help_command(chat_id)
    # etc.

def handle_callback_query(callback_query):
    """
    Handle a callback query from a Telegram inline keyboard.
    
    Args:
        callback_query (dict): Telegram callback query object
    """
    # Extract callback data
    query_id = callback_query.get("id")
    user_id = callback_query.get("from", {}).get("id")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    message_id = callback_query.get("message", {}).get("message_id")
    data = callback_query.get("data", "")
    
    username = callback_query.get("from", {}).get("username")
    first_name = callback_query.get("from", {}).get("first_name")
    last_name = callback_query.get("from", {}).get("last_name")
    
    if not data or not chat_id:
        return
        
    # Log the interaction
    log_user_interaction(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        message_type="callback",
        last_interaction=data
    )
    
    logger.info(f"Received callback from {username or user_id}: {data}")
    
    # Process the callback data
    # Implement callback handlers based on the data
