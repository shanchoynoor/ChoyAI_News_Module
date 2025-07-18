#!/usr/bin/env python3
"""
Main entry point for the Choy News Bot application.

This script can run either the interactive bot, the auto news service, or both.
"""
import os
import sys
import time
import logging
import threading
import argparse
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import Config
from utils.logging import setup_logging, get_logger
from core.bot import ChoyNewsBot
from core.digest_builder import build_news_digest
from api.telegram import send_telegram
from data_modules.models import (
    get_users_for_scheduled_times,
    update_last_sent,
    get_all_subscribed_users,
    init_user_subscriptions_db,
    init_user_logs_db
)
from utils.time_utils import get_bd_now, should_send_news

def run_bot():
    """Run the interactive Telegram bot."""
    logger = get_logger("bot")
    logger.info("Starting Choy News Bot interactive service...")
    
    try:
        bot = ChoyNewsBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        raise

def run_auto_news():
    """Run the automated news delivery service."""
    logger = get_logger("auto_news")
    logger.info("Starting Choy News auto news service...")
    
    # Initialize database
    init_user_subscriptions_db()
    
    try:
        while True:
            try:
                now = get_bd_now()
                current_time = now.strftime("%H:%M")
                logger.debug(f"Checking scheduled news at {current_time}")
                
                # Get all users who should receive news at this time
                hour, minute = now.hour, now.minute
                users = get_users_for_scheduled_times(hour, minute)
                
                if users:
                    logger.info(f"Found {len(users)} users for scheduled time {current_time}")
                    for user in users:
                        try:
                            # Build personalized digest
                            digest = build_news_digest(user)
                            
                            # Send digest to user
                            chat_id = user.get("chat_id")
                            send_telegram(digest, chat_id)
                            
                            # Update last sent time
                            update_last_sent(user.get("user_id"))
                            
                            logger.info(f"Sent news digest to user {user.get('user_id')}")
                        except Exception as e:
                            logger.error(f"Error sending to user {user.get('user_id')}: {e}")
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in auto news loop: {e}", exc_info=True)
                time.sleep(60)  # Continue after error
                
    except KeyboardInterrupt:
        logger.info("Auto news service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in auto news service: {e}", exc_info=True)
        raise

def main():
    """Main entry point that parses command line arguments and starts the requested service."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging("main")
    logger = get_logger("main")
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Choy News Bot")
    parser.add_argument("--service", choices=["bot", "auto", "both"], default="both",
                        help="Which service to run: 'bot', 'auto', or 'both' (default)")
    args = parser.parse_args()
    
    logger.info(f"Starting Choy News with service: {args.service}")
    
    try:
        # Start requested services
        if args.service in ["bot", "both"]:
            # Run in a separate thread
            bot_thread = threading.Thread(target=run_bot)
            bot_thread.daemon = True
            bot_thread.start()
            logger.info("Bot service started in background thread")
            
        if args.service in ["auto", "both"]:
            logger.info("Starting auto news service")
            run_auto_news()  # This will block the main thread
            
        # If only bot was started, we need to keep the main thread alive
        if args.service == "bot":
            while True:
                time.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("Received shutdown signal. Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ChoyNewsBot Main Entry Point

This script starts the Telegram bot with proper argument parsing.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.bot import ChoyNewsBot
from utils.logging import get_logger
from utils.config import Config

logger = get_logger(__name__)

def main():
    """Main entry point for the ChoyNewsBot."""
    parser = argparse.ArgumentParser(description='ChoyNewsBot - AI-Powered Breaking News & Crypto Intelligence')
    parser.add_argument('--service', choices=['bot', 'auto', 'both'], default='both',
                      help='Service to run: bot (interactive), auto (scheduled), or both')
    
    args = parser.parse_args()
    
    try:
        # Initialize configuration
        if not Config.TELEGRAM_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            sys.exit(1)
        
        if args.service in ['bot', 'both']:
            logger.info("Starting ChoyNewsBot...")
            bot = ChoyNewsBot()
            bot.run()
        
        if args.service in ['auto', 'both']:
            logger.info("Auto news service not implemented yet")
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
