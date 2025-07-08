#!/bin/bash
# Script to fix and restart the auto_news service
# Run this script if your news-digest-auto service is in an error state

echo "===== FIXING AUTO NEWS SERVICE ====="
echo "Current directory: $(pwd)"

# Create logs directory if it doesn't exist
mkdir -p logs

# Install required packages (focusing on those needed by auto_news.py)
echo "Installing required packages..."
pip install python-dotenv requests pytz

# Verify .env file
if [ ! -f .env ]; then
  echo "ERROR: .env file is missing! Creating template..."
  cat > .env << 'EOL'
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_token_here
AUTO_NEWS_CHAT_ID=your_chat_id_here

# API Keys
DEEPSEEK_API=your_deepseek_api_key_here
CALENDARIFIC_API_KEY=your_calendarific_api_key_here
EOL
  echo "IMPORTANT: Edit the .env file with your actual values before continuing!"
  exit 1
fi

# Check for TELEGRAM_TOKEN in .env
if ! grep -q "TELEGRAM_TOKEN" .env || grep -q "TELEGRAM_TOKEN=your_telegram_token_here" .env; then
  echo "ERROR: TELEGRAM_TOKEN is not properly set in .env file"
  echo "Please edit the .env file and set a valid TELEGRAM_TOKEN"
  exit 1
fi

# Test auto_news.py imports
echo "Testing auto_news.py imports..."
python3 -c "
try:
    import os, sys, time, logging
    from datetime import datetime, timedelta, timezone
    from dotenv import load_dotenv
    print('Basic imports successful')
    
    # Try importing from news.py
    sys.path.insert(0, '$(pwd)')
    from news import build_news_digest, send_telegram, get_local_time_str
    print('Successfully imported from news.py')
    
    # Try importing from user_subscriptions.py
    from user_subscriptions import get_users_for_scheduled_times, update_last_sent, get_all_subscribed_users, init_db
    print('Successfully imported from user_subscriptions.py')
    
    print('All imports successful - auto_news.py should work correctly')
except Exception as e:
    print(f'ERROR: {str(e)}')
    sys.exit(1)
"

# If we get here, the imports succeeded
echo "Stopping and removing news-digest-auto service..."
pm2 stop news-digest-auto 2>/dev/null || true
pm2 delete news-digest-auto 2>/dev/null || true

echo "Updating auto_news.py file permissions..."
chmod 644 auto_news.py

echo "Starting news-digest-auto service..."
pm2 start --name news-digest-auto auto_news.py --interpreter=python3

echo "Saving PM2 configuration..."
pm2 save

echo "===== STATUS ====="
pm2 status

echo ""
echo "If news-digest-auto is still showing as 'errored', check the logs with:"
echo "  pm2 logs news-digest-auto"
echo ""
echo "You can also try running auto_news.py directly to see any errors:"
echo "  python3 auto_news.py"
