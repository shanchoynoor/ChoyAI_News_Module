#!/bin/bash
# Script to check and diagnose auto_news.py issues

echo "===== DIAGNOSING AUTO_NEWS.PY ISSUES ====="

# Check for logs directory
if [ ! -d "logs" ]; then
  echo "Creating logs directory..."
  mkdir -p logs
fi

# Save current PM2 logs
echo "Capturing current PM2 logs..."
pm2 logs news-digest-auto --lines 50 --nostream > logs/auto_news_pm2.log 2>&1
echo "PM2 logs saved to logs/auto_news_pm2.log"

# Check Python version
echo "Python version:"
python3 --version

# Check for required packages
echo "Checking for required packages..."
pip list | grep -E 'dotenv|pytz|requests|feedparser|telegram'

# Check environment variables
echo "Checking environment variables..."
if [ -f .env ]; then
  echo ".env file exists"
  # Count non-comment, non-empty lines
  ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | wc -l)
  echo "Number of environment variables: $ENV_VARS"
  
  # Check for critical variables without showing values
  if grep -q "TELEGRAM_TOKEN=" .env; then
    echo "TELEGRAM_TOKEN is set"
  else
    echo "ERROR: TELEGRAM_TOKEN is missing!"
  fi
  
  if grep -q "AUTO_NEWS_CHAT_ID=" .env; then
    echo "AUTO_NEWS_CHAT_ID is set"
  else
    echo "WARNING: AUTO_NEWS_CHAT_ID is not set (optional)"
  fi
else
  echo "ERROR: .env file is missing!"
fi

# Test auto_news.py directly with output capture
echo "Testing auto_news.py directly (will terminate after 5 seconds)..."
echo "This will show any import or initialization errors..."

# Run in background with timeout
timeout 5 python3 auto_news.py > logs/auto_news_test.log 2>&1 &
TEST_PID=$!

# Wait for timeout
sleep 5
kill $TEST_PID 2>/dev/null || true

echo "Test output saved to logs/auto_news_test.log"
echo "First 20 lines of test output:"
head -n 20 logs/auto_news_test.log

echo ""
echo "===== DIAGNOSIS COMPLETE ====="
echo "Next steps:"
echo "1. Check the log files in logs/ directory"
echo "2. Ensure all required Python packages are installed"
echo "3. Verify the .env file has the correct environment variables"
echo "4. Run './fix_auto_news.sh' to attempt an automatic fix"
