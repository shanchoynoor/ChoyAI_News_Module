#!/bin/bash
# Script to restart news digest services

echo "===== RESTARTING NEWS DIGEST SERVICES ====="

# First check if token configuration is correct
echo "Checking token configuration..."
./check_token.sh

echo ""
echo "Stopping and restarting services..."
pm2 restart news-digest-bot news-digest-auto

# Check for errors
echo "Checking service status..."
sleep 5  # Wait for services to initialize

if pm2 status | grep -q "errored"; then
  echo "ERROR: One or more services failed to start. Checking logs..."
  mkdir -p error_logs
  
  # Capture error logs
  echo "=== NEWS-DIGEST-BOT ERRORS ===" > error_logs/restart_errors.log
  pm2 logs news-digest-bot --lines 20 --nostream >> error_logs/restart_errors.log 2>&1
  
  echo "=== NEWS-DIGEST-AUTO ERRORS ===" >> error_logs/restart_errors.log
  pm2 logs news-digest-auto --lines 20 --nostream >> error_logs/restart_errors.log 2>&1
  
  echo "Error logs saved to error_logs/restart_errors.log"
  echo "Displaying last 10 lines of error logs:"
  tail -n 10 error_logs/restart_errors.log
  
  echo ""
  echo "If you're still experiencing issues, run:"
  echo "  pm2 logs"
  echo "to see detailed real-time logs."
else
  echo "✅ Services restarted successfully!"
  echo "Current PM2 Status:"
  pm2 status
fi
