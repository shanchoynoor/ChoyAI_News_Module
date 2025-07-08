#!/bin/bash
# Script to check environment variables

echo "===== CHECKING ENVIRONMENT VARIABLES ====="

# Check if .env file exists
if [ -f .env ]; then
  echo ".env file exists"
  echo "Content preview (without showing actual values):"
  grep -v "^#" .env | grep -v "^$" | sed 's/=.*/=***/'
else
  echo "ERROR: .env file does not exist!"
  echo "Creating template .env file..."
  cat > .env << 'EOL'
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_actual_telegram_token_here
AUTO_NEWS_CHAT_ID=your_chat_id_here

# API Keys
DEEPSEEK_API=your_deepseek_api_key_here
CALENDARIFIC_API_KEY=your_calendarific_api_key_here
EOL
  echo "Please edit the .env file and replace placeholder values with your actual keys"
  exit 1
fi

# Test environment variable loading
echo ""
echo "Testing environment variable loading with Python:"
python3 -c "
import os
from dotenv import load_dotenv
print('Loading .env file...')
load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
if token:
    masked_token = token[:4] + '****' + token[-4:] if len(token) > 8 else '****'
    print(f'TELEGRAM_TOKEN is set: {masked_token}')
else:
    print('ERROR: TELEGRAM_TOKEN is not set or is empty!')
"

echo ""
echo "If you see 'TELEGRAM_TOKEN is not set or is empty!', you need to edit your .env file"
echo "and set a valid TELEGRAM_TOKEN value."
echo ""
echo "After editing the .env file, restart your services with:"
echo "  pm2 restart news-digest-auto news-digest-bot"
