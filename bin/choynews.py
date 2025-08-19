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
from pathlib import Path

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

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
    init_user_logs_db()
    
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
                            # Check if we should send news to this user
                            if not should_send_news(user):
                                continue
                                
                            # Build personalized digest
                            digest = build_news_digest(user)
                            if not digest:
                                logger.warning(f"No digest generated for user {user.get('user_id')}")
                                continue
                            
                            # Send digest to user
                            chat_id = user.get("chat_id")
                            if chat_id and send_telegram(digest, chat_id):
                                # Update last sent time only on success
                                update_last_sent(user.get("user_id"))
                                logger.info(f"Sent news digest to user {user.get('user_id')}")
                            else:
                                logger.error(f"Failed to send digest to user {user.get('user_id')}")
                                
                        except Exception as e:
                            logger.error(f"Error processing user {user.get('user_id')}: {e}")
                
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
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="ChoyNewsBot - AI-Powered Breaking News & Crypto Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bin/choynews.py --service bot     # Interactive bot only
  python bin/choynews.py --service auto    # Auto news delivery only  
  python bin/choynews.py --service both    # Both services (default)
        """
    )
    parser.add_argument("--service", choices=["bot", "auto", "both"], default="both",
                        help="Which service to run: 'bot' (interactive), 'auto' (scheduled), or 'both' (default)")
    parser.add_argument("--debug", action="store_true", 
                        help="Enable debug logging")
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate configuration
    try:
        Config.validate()
        if not Config.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    except (ValueError, AttributeError) as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Make sure your .env file contains TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    
    logger.info(f"Starting Choy News with service: {args.service}")
    
    try:
        threads = []
        
        # Start bot service in background if requested
        if args.service in ["bot", "both"]:
            bot_thread = threading.Thread(target=run_bot, name="BotThread")
            bot_thread.daemon = True
            bot_thread.start()
            threads.append(bot_thread)
            logger.info("Bot service started in background thread")
            
        # Start auto news service
        if args.service in ["auto", "both"]:
            if args.service == "both":
                # Run auto news in background thread
                auto_thread = threading.Thread(target=run_auto_news, name="AutoNewsThread")
                auto_thread.daemon = True
                auto_thread.start()
                threads.append(auto_thread)
                logger.info("Auto news service started in background thread")
            else:
                # Run auto news in main thread
                logger.info("Starting auto news service")
                run_auto_news()
                
        # If running both services, keep main thread alive
        if args.service == "both":
            try:
                while any(thread.is_alive() for thread in threads):
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                
        # If only bot was started, keep main thread alive
        elif args.service == "bot":
            try:
                while threads[0].is_alive():
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                
    except KeyboardInterrupt:
        logger.info("Shutting down services...")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()