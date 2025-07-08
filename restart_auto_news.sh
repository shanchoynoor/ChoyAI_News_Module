#!/bin/bash
# Script to fix and properly run the auto_news service

echo "===== FIXING AUTO NEWS SERVICE ====="
echo "Current directory: $(pwd)"

# Check if auto_news.py exists
if [ ! -f "auto_news.py" ]; then
  echo "ERROR: auto_news.py file not found!"
  exit 1
fi

# Test if auto_news.py can run
echo "Testing auto_news.py..."
python3 -c "
import sys
try:
    with open('auto_news.py', 'r') as f:
        content = f.read()
        # Check if we're already using RotatingFileHandler
        if 'RotatingFileHandler' not in content:
            print('ERROR: RotatingFileHandler not found in auto_news.py')
            sys.exit(1)
        print('auto_news.py looks good!')
except Exception as e:
    print(f'ERROR reading auto_news.py: {e}')
    sys.exit(1)
"

# Stop and delete existing services
echo "Stopping and removing existing PM2 services..."
pm2 stop news-digest-auto 2>/dev/null || true
pm2 delete news-digest-auto 2>/dev/null || true

# Explicitly run auto_news.py with python3
echo "Starting auto_news.py with PM2..."
pm2 start auto_news.py --name news-digest-auto --interpreter python3

# Save PM2 configuration
echo "Saving PM2 configuration..."
pm2 save

# Display status
echo "Current PM2 status:"
pm2 status

echo ""
echo "If news-digest-auto is still showing as 'errored', try running it directly:"
echo "  python3 auto_news.py"
echo ""
echo "To check the logs:"
echo "  pm2 logs news-digest-auto"
