import os
import sys
import time
from datetime import datetime, timedelta
from news import handle_updates, get_updates, send_telegram, get_help_text
from news import main as news_main
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_CHAT_ID = os.getenv("AUTO_NEWS_CHAT_ID")  # Set this in your .env or pass as env var

# Bangladesh is UTC+6
def get_bd_now():
    return datetime.utcnow() + timedelta(hours=6)

def should_send_news(now=None):
    if now is None:
        now = get_bd_now()
    # Send at 8:00, 13:00, 19:00, 23:00 (BD time)
    send_hours = [8, 13, 19, 23]
    return now.hour in send_hours and now.minute == 0

def main():
    chat_id = TELEGRAM_CHAT_ID
    if not chat_id:
        print("AUTO_NEWS_CHAT_ID not set in environment.")
        sys.exit(1)
    sent_today = set()
    last_date = None
    while True:
        now = get_bd_now()
        key = (now.date(), now.hour)
        if should_send_news(now) and key not in sent_today:
            print(f"[auto_news] Sending news for {now.strftime('%Y-%m-%d %H:%M')} (BD time)")
            try:
                # Use the same logic as /news handler in news.py
                news_main(return_msg=False, chat_id=chat_id)
                sent_today.add(key)
            except Exception as e:
                print(f"[auto_news] Error sending news: {e}")
        # Reset sent_today at midnight BD time
        if last_date != now.date():
            sent_today = set()
            last_date = now.date()
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    main()
