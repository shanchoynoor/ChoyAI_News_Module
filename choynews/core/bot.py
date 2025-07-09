"""
Telegram Bot Core Module for Choy News.

This module provides the ChoyNewsBot class that handles the bot's main operations.
"""

import time
import logging
import threading
from choynews.utils.logging import get_logger
from choynews.utils.config import Config
from choynews.api.telegram import get_updates, send_telegram
from choynews.services.bot_service import handle_updates

logger = get_logger(__name__)

class ChoyNewsBot:
    """Main Telegram bot class for Choy News."""
    
    def __init__(self):
        """Initialize the ChoyNewsBot."""
        self.running = False
        self.last_update_id = None
    
    def run(self):
        """Run the bot polling loop."""
        self.running = True
        logger.info("Bot started, waiting for messages...")
        
        try:
            while self.running:
                updates = get_updates(self.last_update_id)
                
                if updates:
                    self.last_update_id = handle_updates(updates)
                    logger.debug(f"Processed {len(updates)} updates")
                
                time.sleep(1)  # Avoid excessive polling
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Error in bot polling loop: {e}", exc_info=True)
            self.running = False
    
    def stop(self):
        """Stop the bot polling loop."""
        self.running = False
        logger.info("Bot stopping...")
    
    def send_message(self, chat_id, message, parse_mode="Markdown"):
        """
        Send a message to a Telegram chat.
        
        Args:
            chat_id (int/str): The Telegram chat ID
            message (str): The message to send
            parse_mode (str, optional): Message parse mode
            
        Returns:
            dict: API response or None on error
        """
        return send_telegram(message, chat_id, parse_mode)
