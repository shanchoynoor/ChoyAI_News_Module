#!/bin/bash
# cleanup.sh
# Script to cleanup the workspace and keep only choynews-related files

set -e  # Exit on error

echo "Starting cleanup to keep only choynews package..."

# Create data directory if it doesn't exist
mkdir -p /workspaces/news_digest/data
mkdir -p /workspaces/news_digest/logs

# Move all essential data files to data directory if they exist
# Coinlist
if [ -f "/workspaces/news_digest/coinlist.json" ]; then
  echo "Moving coinlist.json to data directory..."
  mv /workspaces/news_digest/coinlist.json /workspaces/news_digest/data/
fi

# Cache files
for cache_file in crypto_market_cache.json crypto_movers_cache.json crypto_bigcap_cache.json; do
  if [ -f "/workspaces/news_digest/$cache_file" ]; then
    echo "Moving $cache_file to data directory..."
    mv "/workspaces/news_digest/$cache_file" /workspaces/news_digest/data/
  fi
done

# Database files
for db_file in user_timezones.db user_subscriptions.db user_logs.db; do
  if [ -f "/workspaces/news_digest/$db_file" ]; then
    echo "Moving $db_file to data directory..."
    mv "/workspaces/news_digest/$db_file" /workspaces/news_digest/data/
  fi
done

# Log files
if [ -f "/workspaces/news_digest/auto_news.log" ]; then
  echo "Moving auto_news.log to logs directory..."
  mv /workspaces/news_digest/auto_news.log /workspaces/news_digest/logs/
fi

# Delete unnecessary Python files in the root directory
echo "Removing old Python files from root directory..."
rm -f /workspaces/news_digest/auto_news.py
rm -f /workspaces/news_digest/news.py
rm -f /workspaces/news_digest/news_digest.py
rm -f /workspaces/news_digest/crypto_cache.py
rm -f /workspaces/news_digest/user_logging.py
rm -f /workspaces/news_digest/user_subscriptions.py
rm -f /workspaces/news_digest/update_coinlist.py

# Remove newsdigest directory
echo "Removing newsdigest directory..."
rm -rf /workspaces/news_digest/newsdigest

# Remove unnecessary files and directories
echo "Removing unnecessary files and directories..."
rm -f /workspaces/news_digest/check_env.sh
rm -f /workspaces/news_digest/check_token.sh
rm -f /workspaces/news_digest/diagnose.sh
rm -f /workspaces/news_digest/diagnose_auto_news.sh
rm -f /workspaces/news_digest/fix_auto_news.sh
rm -f /workspaces/news_digest/fix_logging.sh
rm -f /workspaces/news_digest/restart.sh
rm -f /workspaces/news_digest/restart_auto_news.sh
rm -f /workspaces/news_digest/restart_services.sh
rm -f /workspaces/news_digest/ecosystem.config.json
rm -f /workspaces/news_digest/deploy.sh
rm -f /workspaces/news_digest/test_subscriptions.py
rm -f /workspaces/news_digest/AUTO_NEWS_FIXES.md
rm -f /workspaces/news_digest/SERVER_SETUP.md
rm -f /workspaces/news_digest/sent_news.json

# Remove the __pycache__ directories
echo "Removing __pycache__ directories..."
find /workspaces/news_digest -name "__pycache__" -type d -exec rm -rf {} +

echo "Cleanup completed successfully!"
echo "The workspace now contains only the choynews package and necessary files."
