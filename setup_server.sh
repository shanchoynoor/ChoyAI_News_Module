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

# Make sure .env file exists
echo "Checking for .env file..."
if [ ! -f .env ]; then
  echo "Creating template .env file..."
  cat > .env << 'EOL'
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_token_here
AUTO_NEWS_CHAT_ID=your_chat_id_here

# API Keys
DEEPSEEK_API=your_deepseek_api_key_here
CALENDARIFIC_API_KEY=your_calendarific_api_key_here

# Other Settings
# Add any other environment variables your bot needs
EOL
  echo "WARNING: Please edit the .env file with your actual API keys and settings!"
else
  echo ".env file already exists."
fi

# Stop existing PM2 processes
echo "Stopping existing PM2 processes..."
pm2 stop news-digest-bot news-digest-auto choynews_auto choynewsbot 2>/dev/null || true
pm2 delete news-digest-bot news-digest-auto choynews_auto choynewsbot 2>/dev/null || true

# Start services with the new configuration
echo "Starting services with PM2..."
pm2 start server_config.json

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
