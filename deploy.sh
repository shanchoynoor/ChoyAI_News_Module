#!/bin/bash
# Deploy News Digest Bot with PM2

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null
then
    echo "Installing PM2..."
    npm install -g pm2
else
    echo "PM2 is already installed"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

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
echo "View logs with: pm2 logs news-digest-bot"
echo "View auto scheduler logs with: pm2 logs news-digest-auto"
