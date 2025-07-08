#!/bin/bash
# Restart script for News Digest Bot services

echo "Stopping news digest services..."
pm2 stop news-digest-bot news-digest-auto 2>/dev/null || true

echo "Deleting previous instances..."
pm2 delete news-digest-bot news-digest-auto 2>/dev/null || true

echo "Creating logs directory..."
mkdir -p logs

echo "Starting services from ecosystem.config.json..."
pm2 start ecosystem.config.json

echo "PM2 Status:"
pm2 status

echo "Saving PM2 configuration..."
pm2 save

echo "Done! Services have been restarted."
echo "Check logs in the logs/ directory for any issues."
