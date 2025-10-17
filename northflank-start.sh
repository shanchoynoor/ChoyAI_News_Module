#!/bin/bash
# Northflank startup script for ChoyNewsBot
# This script ensures proper environment setup and starts the bot

set -e  # Exit on any error

echo "=== ChoyNewsBot Northflank Startup ==="
echo "Working directory: $(pwd)"
echo "Python version: $(python3 --version)"
echo "Pip version: $(pip3 --version)"

# Install dependencies if requirements.txt exists
if [ -f "config/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip3 install --no-cache-dir -r config/requirements.txt
else
    echo "Warning: config/requirements.txt not found"
fi

# Create necessary directories with proper permissions
echo "Creating directories..."
mkdir -p logs data/cache data/static
chmod -R 755 logs data
chmod 644 data/cache/.gitkeep 2>/dev/null || true

# Set environment variables (fallback if not set by Northflank)
export PYTHONPATH="${PYTHONPATH}:/app"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Validate environment
echo "Validating environment..."
python3 -c "
import os
import sys
sys.path.insert(0, '.')

# Check critical environment variables
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
if not telegram_token:
    print('ERROR: TELEGRAM_BOT_TOKEN not set')
    sys.exit(1)

print(f'TELEGRAM_BOT_TOKEN: {\"Set\" if telegram_token else \"Not set\"} (length: {len(telegram_token)})')
print(f'Working directory: {os.getcwd()}')
print('Environment validation passed!')
"

# Test Telegram API connection
echo "Testing Telegram API connection..."
python3 -c "
import sys
import os
sys.path.insert(0, '.')

# Check environment variables
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
print(f'TELEGRAM_BOT_TOKEN present: {\"Yes\" if telegram_token else \"No\"} (length: {len(telegram_token)})')

from api.telegram import get_updates
try:
    updates = get_updates()
    print(f'Telegram API test successful! Received {len(updates) if updates else 0} updates')
except Exception as e:
    print(f'Telegram API test failed: {e}')
    # Don't exit on API test failure - might be network issue
    print('Continuing with startup despite API test failure...')
"

# Start the bot
echo "Starting ChoyNewsBot..."
exec python3 bin/choynews.py --service bot