import os
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
from news import build_news_digest, send_telegram, get_local_time_str
from dotenv import load_dotenv
from user_subscriptions import get_users_for_scheduled_times, update_last_sent, get_all_subscribed_users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("auto_news.log")
    ]
)
logger = logging.getLogger("auto_news")

# Load environment variables
load_dotenv()
TELEGRAM_CHAT_ID = os.getenv("AUTO_NEWS_CHAT_ID")  # Legacy global chat ID (optional)

# Bangladesh is UTC+6
def get_bd_now():
    return datetime.now(timezone.utc) + timedelta(hours=6)

def should_send_news(now=None):
    """
    Check if the current time (BDT) matches one of the scheduled send times:
    8:00am, 1:00pm, 7:00pm, or 11:00pm.
    """
    if now is None:
        now = get_bd_now()
    
    # List of (hour, minute) tuples for sending news
    send_times = [(8, 0), (13, 0), (19, 0), (23, 0)]
    
    # Only trigger on the exact minute
    return (now.hour, now.minute) in send_times

def main():
    """
    Main function that runs continuously, checking for scheduled times
    to send news digests to subscribed users.
    """
    logger.info("Auto News service started")
    
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
                
                # Get users who should receive news at this hour in their local timezone
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
                
                # Wait 60 seconds after sending to avoid duplicate sends
                time.sleep(60)
            
            # Sleep briefly before checking again
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(30)  # Wait longer after an error

if __name__ == "__main__":
    main()
