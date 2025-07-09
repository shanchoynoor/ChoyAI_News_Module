#!/bin/bash
# Migration script to help transition from the old file structure to the new one
# This script preserves your data while reorganizing the code

echo "===== MIGRATING NEWS DIGEST PROJECT TO NEW STRUCTURE ====="
echo "This script will help reorganize your project while preserving all your data."
echo "It's recommended to backup your project before proceeding."
read -p "Continue? (y/n): " confirm
if [ "$confirm" != "y" ]; then
  echo "Migration aborted."
  exit 1
fi

# Create necessary directories if they don't exist
echo "Creating necessary directories..."
mkdir -p data/db logs

# Move data files to the data directory
echo "Moving data files..."
if [ -f coinlist.json ]; then
  mv coinlist.json data/
fi
if [ -f crypto_bigcap_cache.json ]; then
  mv crypto_bigcap_cache.json data/
fi
if [ -f crypto_market_cache.json ]; then
  mv crypto_market_cache.json data/
fi
if [ -f crypto_movers_cache.json ]; then
  mv crypto_movers_cache.json data/
fi
if [ -f sent_news.json ]; then
  mv sent_news.json data/
fi

# Move database files
echo "Moving database files..."
if [ -f user_timezones.db ]; then
  mv user_timezones.db data/db/
fi
if [ -f user_subscriptions.db ]; then
  mv user_subscriptions.db data/db/
fi
if [ -f user_logs.db ]; then
  mv user_logs.db data/db/
fi

# Copy log files
echo "Moving log files..."
if [ -f auto_news.log ]; then
  mv auto_news.log logs/
fi

# Ensure permissions are correct
echo "Setting permissions..."
chmod 644 data/*.json data/db/*.db
chmod 755 scripts/*.py deployment/*.sh

echo "===== MIGRATION COMPLETE ====="
echo ""
echo "Your project has been reorganized to follow a more modular structure."
echo "The main application logic is now in the 'newsdigest' package."
echo "Data files have been moved to the 'data' directory."
echo "Database files have been moved to 'data/db'."
echo "Log files have been moved to 'logs'."
echo ""
echo "To run the application with the new structure:"
echo "1. Install the package: pip install -e ."
echo "2. Run the setup script: ./deployment/setup_server.sh"
echo "3. Start the services: pm2 start deployment/pm2_config.json"
echo ""
echo "You may need to update your environment variables in the .env file."
