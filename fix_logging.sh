#!/bin/bash
# Quick fix for the FileHandler issue in auto_news.py

echo "Fixing auto_news.py logging configuration..."

# Backup original file
cp auto_news.py auto_news.py.bak

# Replace FileHandler with RotatingFileHandler
sed -i '5i from logging.handlers import RotatingFileHandler' auto_news.py
sed -i 's/logging.FileHandler/RotatingFileHandler/g' auto_news.py

echo "Fixed auto_news.py - replaced FileHandler with RotatingFileHandler"

echo "Restarting news-digest-auto service..."
pm2 stop news-digest-auto 2>/dev/null || true
pm2 delete news-digest-auto 2>/dev/null || true
pm2 start --name news-digest-auto auto_news.py --interpreter=python3

echo "Saving PM2 configuration..."
pm2 save

echo "Current PM2 status:"
pm2 status

echo ""
echo "Check if news-digest-auto is now running. If it's still in error state, run:"
echo "pm2 logs news-digest-auto"
