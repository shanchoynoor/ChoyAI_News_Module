import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import traceback

# Configure logging with rotation to avoid large log files
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("auto_news.log", mode='a', maxBytes=10485760, backupCount=3)
    ]
)
logger = logging.getLogger("auto_news")

# Load environment variables
load_dotenv()
TELEGRAM_CHAT_ID = os.getenv("AUTO_NEWS_CHAT_ID")  # Legacy global chat ID (optional)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Check for required environment variables at startup
if not TELEGRAM_TOKEN:
    logger.critical("TELEGRAM_TOKEN environment variable is not set. Cannot continue.")
    sys.exit(1)

# Verify imports at startup to avoid runtime errors
try:
    from news import build_news_digest, send_telegram, get_local_time_str
    from user_subscriptions import get_users_for_scheduled_times, update_last_sent, get_all_subscribed_users, init_db
    logger.info("Successfully imported all required modules")
except ImportError as e:
    logger.critical(f"Failed to import required modules: {e}")
    logger.critical(traceback.format_exc())
    sys.exit(1)

# Bangladesh is UTC+6
def get_bd_now():
    return datetime.now(timezone.utc) + timedelta(hours=6)

def should_send_news(now=None):
    """
    Check if the current time (BDT) matches one of the scheduled send times:
    8:00am, 1:00pm, 7:00pm, or 11:00pm.
    
    Returns True only during the first minute of each scheduled hour.
    """
    if now is None:
        now = get_bd_now()
    
    # List of (hour, minute) tuples for sending news
    send_times = [(8, 0), (13, 0), (19, 0), (23, 0)]
    
    # Only trigger on the exact minute
    current_time = (now.hour, now.minute)
    should_send = current_time in send_times
    
    if should_send:
        logger.info(f"Scheduled time matched: {now.hour}:{now.minute}")
    
    return should_send

def main():
    """
    Main function that runs continuously, checking for scheduled times
    to send news digests to subscribed users.
    """
    logger.info("Auto News service started")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Initialize user database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        logger.error(traceback.format_exc())
    
    # Legacy global chat ID support
    if TELEGRAM_CHAT_ID:
        logger.info(f"Legacy global chat ID configured: {TELEGRAM_CHAT_ID}")
    else:
        logger.info("No legacy global chat ID configured, using subscription system only")
    
    last_check_minute = -1
    
    # Main loop
    while True:
        try:
            now = datetime.now(timezone.utc)
            now_bd = get_bd_now()
            
            # Log less frequently - only once per minute
            if now_bd.minute != last_check_minute:
                logger.debug(f"Checking at {now_bd.strftime('%Y-%m-%d %H:%M:%S')} (BD time)")
                last_check_minute = now_bd.minute
            
            # Check if it's time to send news
            if should_send_news(now_bd):
                logger.info(f"Scheduled news time: {now_bd.strftime('%Y-%m-%d %H:%M')} (BD time)")
                
                # Send to legacy global chat ID if configured
                if TELEGRAM_CHAT_ID:
                    try:
                        logger.info(f"Sending to legacy global chat ID: {TELEGRAM_CHAT_ID}")
                        build_news_digest(return_msg=False, chat_id=TELEGRAM_CHAT_ID)
                        logger.info("Successfully sent to legacy global chat ID")
                    except Exception as e:
                        logger.error(f"Error sending to legacy global chat ID: {e}")
                        logger.error(traceback.format_exc())
                
                # Get users who should receive news at this hour in their local timezone
                try:
                    target_users = get_users_for_scheduled_times()
                    logger.info(f"Found {len(target_users)} subscribed users for current time")
                    
                    # Send to each user and update their last sent timestamp
                    for user_id in target_users:
                        try:
                            logger.info(f"Sending to user: {user_id}")
                            
                            # Get user's local time for the header
                            user_time_str = get_local_time_str(user_id=user_id)
                            
                            # Build and send the digest
                            build_news_digest(return_msg=False, chat_id=user_id)
                            
                            # Update the last sent timestamp
                            update_last_sent(user_id)
                            
                            logger.info(f"Successfully sent to user {user_id}")
                            
                            # Small delay between sends to avoid rate limits
                            time.sleep(1)
                        except Exception as e:
                            logger.error(f"Error sending to user {user_id}: {e}")
                            logger.error(traceback.format_exc())
                except Exception as e:
                    logger.error(f"Error getting users for scheduled times: {e}")
                    logger.error(traceback.format_exc())
                
                # Wait 60 seconds after sending to avoid duplicate sends
                logger.info("Waiting 60 seconds to avoid duplicate sends")
                time.sleep(60)
            
            # Sleep briefly before checking again
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.error(traceback.format_exc())
            time.sleep(30)  # Wait longer after an error

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error in auto_news.py: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
