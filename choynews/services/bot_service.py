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
        handle_regular_message(chat_id, user_id, username, text)

def handle_regular_message(chat_id, user_id, username, text):
    """Handle regular (non-command) messages."""
    from choynews.api.telegram import send_telegram
    
    # Simple responses to common greetings and questions
    text_lower = text.lower().strip()
    
    if any(greeting in text_lower for greeting in ['hello', 'hi', 'hey', 'greetings']):
        name = username or "there"
        response = f"Hello {name}! 👋 Welcome to ChoyNewsBot. Type /help to see what I can do for you!"
    elif any(word in text_lower for word in ['news', 'update', 'latest']):
        response = "📰 You can get the latest news by typing /news"
    elif any(word in text_lower for word in ['help', 'what', 'how']):
        response = "❓ Type /help to see all available commands and features"
    elif any(word in text_lower for word in ['thanks', 'thank you', 'thx']):
        response = "You're welcome! 😊 Happy to help!"
    else:
        ellipsis = "..." if len(text) > 50 else ""
        response = f"I received your message: '{text[:50]}{ellipsis}'\\n\\nType /help to see what commands I understand!"
    
    send_telegram(response, chat_id)
    logger.info(f"Responded to regular message from user {user_id}")

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
    
    # Import here to avoid circular imports
    from choynews.api.telegram import send_telegram
    
    # Handle different commands
    if command == '/start':
        handle_start_command(chat_id, user_id, username, first_name, last_name)
    elif command == '/help':
        handle_help_command(chat_id)
    elif command == '/status':
        handle_status_command(chat_id)
    elif command == '/news':
        handle_news_command(chat_id, user_id, args)
    else:
        # Unknown command
        send_telegram(
            f"Sorry, I don't understand the command '{command}'. Type /help to see available commands.",
            chat_id
        )

def handle_start_command(chat_id, user_id, username, first_name, last_name):
    """Handle the /start command."""
    from choynews.api.telegram import send_telegram
    
    name = first_name or username or "there"
    welcome_message = f"""
🗞️ *Welcome to ChoyNewsBot, {name}!*

I'm your personal news assistant. I can provide you with:
• 📰 Latest news updates
• 💰 Cryptocurrency market data
• 🌤️ Weather information
• ⏰ Scheduled news delivery

*Available Commands:*
/start - Show this welcome message
/help - Get help and see all commands
/news - Get latest news digest
/status - Check bot status

Type /help for more detailed information about what I can do!
    """
    
    send_telegram(welcome_message, chat_id)
    logger.info(f"Sent welcome message to user {user_id} ({username})")

def handle_help_command(chat_id):
    """Handle the /help command."""
    from choynews.api.telegram import send_telegram
    
    help_message = """
📚 *ChoyNewsBot Help*

*Available Commands:*

🚀 `/start` - Show welcome message
❓ `/help` - Show this help message
📰 `/news` - Get latest news digest
⚡ `/status` - Check bot status

*Features:*
• Daily news digests
• Cryptocurrency market updates
• Weather information
• Personalized content delivery
• Scheduled news at specific times

*Coming Soon:*
• Custom news preferences
• Location-based weather
• Crypto portfolio tracking
• More interactive features

For support or questions, contact the administrator.
    """
    
    send_telegram(help_message, chat_id)
    logger.info(f"Sent help message to chat {chat_id}")

def handle_status_command(chat_id):
    """Handle the /status command."""
    from choynews.api.telegram import send_telegram
    import datetime
    
    status_message = f"""
🤖 *Bot Status*

✅ Bot is online and running
🕒 Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📡 API connection: Active
🔧 Services: Bot + Auto News

All systems operational! 🚀
    """
    
    send_telegram(status_message, chat_id)
    logger.info(f"Sent status message to chat {chat_id}")

def handle_news_command(chat_id, user_id, args):
    """Handle the /news command."""
    from choynews.api.telegram import send_telegram
    from choynews.core.digest_builder import build_news_digest
    
    try:
        # Create a basic user object for digest building
        user = {
            "user_id": user_id,
            "chat_id": chat_id,
            "preferences": {}  # Default preferences
        }
        
        # Build and send news digest
        send_telegram("📰 Generating your news digest... Please wait.", chat_id)
        digest = build_news_digest(user)
        send_telegram(digest, chat_id)
        
        logger.info(f"Sent news digest to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error generating news digest for user {user_id}: {e}")
        send_telegram(
            "Sorry, I encountered an error while generating your news digest. Please try again later.",
            chat_id
        )

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
