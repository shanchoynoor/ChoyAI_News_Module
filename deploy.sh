#!/bin/bash
# Deploy News Digest Bot with PM2
set -e  # Exit on error

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null
then
    echo "Installing PM2..."
    npm install -g pm2
else
    echo "PM2 is already installed"
fi

# Make sure old processes are stopped first
echo "Stopping any existing news digest processes..."
pm2 stop news-digest-bot news-digest-auto 2>/dev/null || true
pm2 delete news-digest-bot news-digest-auto 2>/dev/null || true

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check for required environment variables
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "WARNING: TELEGRAM_TOKEN environment variable is not set!"
    echo "The application may not work correctly."
fi

# Start the bot with PM2
echo "Starting News Digest Bot with PM2..."
pm2 start ecosystem.config.json

# Check status
echo "PM2 Status:"
pm2 status

# Configure PM2 to start on system boot
echo "Configuring PM2 to start on system boot..."
pm2 startup
pm2 save

echo "Deployment complete! The bot is now running."
echo "Check logs in the logs/ directory if you encounter any issues."
echo "View logs with: pm2 logs news-digest-bot"
echo "View auto scheduler logs with: pm2 logs news-digest-auto"
