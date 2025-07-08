#!/bin/bash
# Script to check and fix Telegram token configuration

echo "===== TELEGRAM TOKEN CONFIGURATION CHECK ====="

# Check if .env file exists
if [ ! -f .env ]; then
  echo "ERROR: .env file does not exist!"
  echo "Please run ./setup_server.sh to create a template .env file."
  exit 1
fi

# Extract token values
telegram_bot_token=$(grep -o 'TELEGRAM_BOT_TOKEN=.*' .env 2>/dev/null | cut -d'=' -f2)
telegram_token=$(grep -o 'TELEGRAM_TOKEN=.*' .env 2>/dev/null | cut -d'=' -f2)

echo "Current token configuration:"
if [ -n "$telegram_bot_token" ] && [ "$telegram_bot_token" != "your_telegram_token_here" ]; then
  echo "- TELEGRAM_BOT_TOKEN: ****$(echo "$telegram_bot_token" | tail -c 5)"
else
  echo "- TELEGRAM_BOT_TOKEN: Not set or using placeholder value"
fi

if [ -n "$telegram_token" ] && [ "$telegram_token" != "your_telegram_token_here" ]; then
  echo "- TELEGRAM_TOKEN: ****$(echo "$telegram_token" | tail -c 5)"
else
  echo "- TELEGRAM_TOKEN: Not set or using placeholder value"
fi

# Check configuration status
if { [ -z "$telegram_bot_token" ] || [ "$telegram_bot_token" = "your_telegram_token_here" ]; } && \
   { [ -z "$telegram_token" ] || [ "$telegram_token" = "your_telegram_token_here" ]; }; then
  echo "STATUS: ❌ NO VALID TOKEN FOUND"
  echo "ACTION REQUIRED: Edit your .env file and add a valid token to either TELEGRAM_BOT_TOKEN or TELEGRAM_TOKEN."
elif [ -n "$telegram_bot_token" ] && [ "$telegram_bot_token" != "your_telegram_token_here" ] && \
     [ -n "$telegram_token" ] && [ "$telegram_token" != "your_telegram_token_here" ]; then
  if [ "$telegram_bot_token" = "$telegram_token" ]; then
    echo "STATUS: ✅ BOTH TOKENS ARE SET AND MATCH"
    echo "ACTION: None required. Configuration is correct."
  else
    echo "STATUS: ⚠️ TOKENS ARE DIFFERENT"
    echo "ACTION REQUIRED: Run ./setup_server.sh to synchronize the tokens or manually edit .env to make them match."
  fi
else
  echo "STATUS: ⚠️ ONLY ONE TOKEN IS SET"
  echo "ACTION REQUIRED: Run ./setup_server.sh to automatically set both tokens or manually edit .env."
fi

echo ""
echo "Python code check:"
echo "-----------------"

# Check auto_news.py implementation
if grep -q "TELEGRAM_TOKEN = os.getenv(\"TELEGRAM_TOKEN\") or os.getenv(\"TELEGRAM_BOT_TOKEN\")" auto_news.py; then
  echo "✅ auto_news.py is using both token variables (correctly configured)"
else
  echo "❌ auto_news.py is NOT using both token variables"
  echo "ACTION REQUIRED: Run ./setup_server.sh to fix the code or manually edit auto_news.py."
fi

# Check news.py implementation
if grep -q "TELEGRAM_TOKEN = os.getenv(\"TELEGRAM_BOT_TOKEN\")" news.py; then
  echo "✅ news.py is using TELEGRAM_BOT_TOKEN (correctly configured)"
else
  echo "❓ news.py token variable could not be determined"
  echo "ACTION: Manually inspect news.py to check which token variable it uses."
fi

echo ""
echo "To fix all issues automatically, run:"
echo "  ./setup_server.sh"
echo ""
echo "After fixing issues, restart services with:"
echo "  pm2 restart news-digest-auto news-digest-bot"
