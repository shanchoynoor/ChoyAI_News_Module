#!/bin/bash
# Setup script for the News Digest Bot
# This script will install all required dependencies and fix environment issues

echo "===== SETTING UP NEWS DIGEST BOT ====="
echo "Current directory: $(pwd)"

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Install required Python packages
echo "Installing Python packages..."
pip install python-dotenv feedparser pytz requests python-telegram-bot numpy timezonefinder sgmllib3k
echo "Installing additional packages directly in case of requirements.txt issues..."
pip install -r requirements.txt

# Make sure the permissions are correct
echo "Setting correct permissions..."
chmod 644 *.json *.py *.db
chmod 755 *.sh

# Create a pm2 configuration file specific to your server
echo "Creating PM2 configuration file..."
cat > server_config.json << 'EOL'
{
  "apps": [
    {
      "name": "news-digest-bot",
      "script": "news.py",
      "interpreter": "python3",
      "instances": 1,
      "autorestart": true,
      "watch": false,
      "max_memory_restart": "200M",
      "env": {
        "PYTHONUNBUFFERED": "1"
      },
      "log_date_format": "YYYY-MM-DD HH:mm:ss",
      "error_file": "logs/news-bot-error.log",
      "out_file": "logs/news-bot-out.log",
      "merge_logs": true
    },
    {
      "name": "news-digest-auto",
      "script": "auto_news.py",
      "interpreter": "python3",
      "instances": 1,
      "autorestart": true,
      "watch": false,
      "max_memory_restart": "150M",
      "env": {
        "PYTHONUNBUFFERED": "1"
      },
      "log_date_format": "YYYY-MM-DD HH:mm:ss",
      "error_file": "logs/news-auto-error.log",
      "out_file": "logs/news-auto-out.log",
      "merge_logs": true
    }
  ]
}
EOL

# Make sure .env file exists and has required values
echo "Checking for .env file and required values..."
if [ ! -f .env ]; then
  echo "Creating template .env file..."
  cat > .env << 'EOL'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_token_here
TELEGRAM_TOKEN=your_telegram_token_here
AUTO_NEWS_CHAT_ID=your_chat_id_here

# API Keys
DEEPSEEK_API=your_deepseek_api_key_here
CALENDARIFIC_API_KEY=your_calendarific_api_key_here

# Other Settings
# Add any other environment variables your bot needs
EOL
  echo "WARNING: Please edit the .env file with your actual API keys and settings!"
  echo "The script will continue but services may not start correctly until you set these values."
else
  echo ".env file already exists. Checking for required values..."

  # Check if at least one of the token variables is set
  telegram_bot_token=$(grep -o 'TELEGRAM_BOT_TOKEN=.*' .env 2>/dev/null | cut -d'=' -f2)
  telegram_token=$(grep -o 'TELEGRAM_TOKEN=.*' .env 2>/dev/null | cut -d'=' -f2)
  
  # Check if both are missing or using placeholder values
  if { [ -z "$telegram_bot_token" ] || [ "$telegram_bot_token" = "your_telegram_token_here" ]; } && \
     { [ -z "$telegram_token" ] || [ "$telegram_token" = "your_telegram_token_here" ]; }; then
    echo "WARNING: No valid Telegram token found in .env file!"
    echo "Please edit the .env file and set either TELEGRAM_BOT_TOKEN or TELEGRAM_TOKEN."
    echo "The script will continue but services may not start correctly until you set this value."
  else
    # If one token is set but the other is missing, create the missing one
    if [ -n "$telegram_bot_token" ] && [ "$telegram_bot_token" != "your_telegram_token_here" ] && \
       { [ -z "$telegram_token" ] || [ "$telegram_token" = "your_telegram_token_here" ]; }; then
      echo "Found TELEGRAM_BOT_TOKEN but TELEGRAM_TOKEN is missing. Adding TELEGRAM_TOKEN..."
      if ! grep -q "TELEGRAM_TOKEN=" .env; then
        echo "" >> .env
        echo "# Added by setup script for compatibility" >> .env
        echo "TELEGRAM_TOKEN=$telegram_bot_token" >> .env
      else
        # If TELEGRAM_TOKEN exists but with placeholder, update it
        sed -i "s/TELEGRAM_TOKEN=.*/TELEGRAM_TOKEN=$telegram_bot_token/" .env
      fi
      echo "TELEGRAM_TOKEN has been added/updated in the .env file."
    elif [ -n "$telegram_token" ] && [ "$telegram_token" != "your_telegram_token_here" ] && \
         { [ -z "$telegram_bot_token" ] || [ "$telegram_bot_token" = "your_telegram_token_here" ]; }; then
      echo "Found TELEGRAM_TOKEN but TELEGRAM_BOT_TOKEN is missing. Adding TELEGRAM_BOT_TOKEN..."
      if ! grep -q "TELEGRAM_BOT_TOKEN=" .env; then
        echo "" >> .env
        echo "# Added by setup script for compatibility" >> .env
        echo "TELEGRAM_BOT_TOKEN=$telegram_token" >> .env
      else
        # If TELEGRAM_BOT_TOKEN exists but with placeholder, update it
        sed -i "s/TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$telegram_token/" .env
      fi
      echo "TELEGRAM_BOT_TOKEN has been added/updated in the .env file."
    else
      echo "Both TELEGRAM_BOT_TOKEN and TELEGRAM_TOKEN appear to be set."
      
      # If they're different, make them the same using TELEGRAM_BOT_TOKEN as source of truth
      if [ "$telegram_bot_token" != "$telegram_token" ] && \
         [ -n "$telegram_bot_token" ] && [ "$telegram_bot_token" != "your_telegram_token_here" ]; then
        echo "WARNING: Token values are different! Synchronizing to use TELEGRAM_BOT_TOKEN value..."
        sed -i "s/TELEGRAM_TOKEN=.*/TELEGRAM_TOKEN=$telegram_bot_token/" .env
        echo "TELEGRAM_TOKEN has been updated to match TELEGRAM_BOT_TOKEN."
      fi
    fi
    
    echo "Telegram token configuration appears to be correct."
  fi
fi

# Fix inconsistencies in auto_news.py to use the same token name as news.py
echo "Checking for token variable inconsistencies in Python files..."
if grep -q "TELEGRAM_TOKEN = os.getenv(\"TELEGRAM_TOKEN\")" auto_news.py; then
  echo "Updating auto_news.py to use both token variables..."
  sed -i 's/TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")/# Try both token variable names for compatibility\nTELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")/' auto_news.py
  echo "Fixed token variable inconsistency in auto_news.py"
fi

# Check and fix common auto_news.py issues
echo "Checking auto_news.py for common issues..."

# Check for FileHandler with maxBytes issue
if grep -q "logging.FileHandler.*maxBytes" auto_news.py; then
  echo "Fixing FileHandler issue in auto_news.py..."
  sed -i '5i from logging.handlers import RotatingFileHandler' auto_news.py
  sed -i 's/logging.FileHandler/RotatingFileHandler/g' auto_news.py
  echo "Fixed logging configuration in auto_news.py"
fi

# Stop existing PM2 processes
echo "Stopping existing PM2 processes..."
pm2 stop news-digest-bot news-digest-auto choynews_auto choynewsbot 2>/dev/null || true
pm2 delete news-digest-bot news-digest-auto choynews_auto choynewsbot 2>/dev/null || true

# Start services with the new configuration
echo "Starting services with PM2..."
pm2 start server_config.json

# Check for immediate errors
echo "Checking for immediate errors..."
sleep 5  # Wait for services to initialize

if pm2 status | grep -q "errored"; then
  echo "ERROR: One or more services failed to start. Checking logs..."
  mkdir -p error_logs
  
  # Capture error logs
  echo "=== NEWS-DIGEST-BOT ERRORS ===" > error_logs/startup_errors.log
  pm2 logs news-digest-bot --lines 20 --nostream >> error_logs/startup_errors.log 2>&1
  
  echo "=== NEWS-DIGEST-AUTO ERRORS ===" >> error_logs/startup_errors.log
  pm2 logs news-digest-auto --lines 20 --nostream >> error_logs/startup_errors.log 2>&1
  
  echo "Error logs saved to error_logs/startup_errors.log"
  echo "Displaying last 10 lines of error logs:"
  tail -n 10 error_logs/startup_errors.log
fi

# Save PM2 configuration
echo "Saving PM2 configuration..."
pm2 save

echo "===== SETUP COMPLETE ====="
echo "PM2 Status:"
pm2 status

echo ""
echo "IMPORTANT: If you see any errors, check the following:"
echo "1. Make sure you've edited the .env file with your actual API keys"
echo "2. Check the log files in the logs/ directory"
echo "3. Run 'pm2 logs' to see real-time logs"
