#!/bin/bash
# Migration script to help transition from newsdigest to choynews

set -e  # Exit on error

echo "Starting migration from newsdigest to choynews..."

# Create data directory if it doesn't exist
mkdir -p /workspaces/news_digest/data

# Move database files if they exist
if [ -f "/workspaces/news_digest/user_timezones.db" ]; then
  echo "Moving user_timezones.db to data directory..."
  mv /workspaces/news_digest/user_timezones.db /workspaces/news_digest/data/
fi

if [ -f "/workspaces/news_digest/user_subscriptions.db" ]; then
  echo "Moving user_subscriptions.db to data directory..."
  mv /workspaces/news_digest/user_subscriptions.db /workspaces/news_digest/data/
fi

if [ -f "/workspaces/news_digest/user_logs.db" ]; then
  echo "Moving user_logs.db to data directory..."
  mv /workspaces/news_digest/user_logs.db /workspaces/news_digest/data/
fi

# Move coinlist.json if it exists
if [ -f "/workspaces/news_digest/coinlist.json" ]; then
  echo "Moving coinlist.json to data directory..."
  mv /workspaces/news_digest/coinlist.json /workspaces/news_digest/data/
fi

# Move cache files if they exist
if [ -f "/workspaces/news_digest/crypto_market_cache.json" ]; then
  echo "Moving crypto_market_cache.json to data directory..."
  mv /workspaces/news_digest/crypto_market_cache.json /workspaces/news_digest/data/
fi

if [ -f "/workspaces/news_digest/crypto_movers_cache.json" ]; then
  echo "Moving crypto_movers_cache.json to data directory..."
  mv /workspaces/news_digest/crypto_movers_cache.json /workspaces/news_digest/data/
fi

if [ -f "/workspaces/news_digest/crypto_bigcap_cache.json" ]; then
  echo "Moving crypto_bigcap_cache.json to data directory..."
  mv /workspaces/news_digest/crypto_bigcap_cache.json /workspaces/news_digest/data/
fi

# Create logs directory if it doesn't exist
mkdir -p /workspaces/news_digest/logs

# Move log files if they exist
if [ -f "/workspaces/news_digest/auto_news.log" ]; then
  echo "Moving auto_news.log to logs directory..."
  mv /workspaces/news_digest/auto_news.log /workspaces/news_digest/logs/
fi

echo "Migration completed successfully!"
echo "Now install the package with: pip install -e ."
echo "And then update your scripts to use the new choynews package."
