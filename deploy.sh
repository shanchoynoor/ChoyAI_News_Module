#!/bin/bash

# ChoyNewsBot Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting ChoyNewsBot deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating template..."
    cat > .env << EOF
# Required Environment Variables
TELEGRAM_TOKEN=your_telegram_bot_token_here
DEEPSEEK_API=your_deepseek_api_key_here

# Optional Environment Variables
WEATHERAPI_KEY=your_weather_api_key
CALENDARIFIC_API_KEY=your_calendar_api_key
TWELVE_DATA_API_KEY=your_twelve_data_api_key

# Application Settings
LOG_LEVEL=INFO
REDIS_PASSWORD=choynews_redis_secure

# Auto News Settings (optional)
AUTO_NEWS_CHAT_ID=your_channel_id_for_auto_news
EOF
    echo "📝 Please edit .env file with your actual API keys before continuing."
    echo "   Then run: ./deploy.sh"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs data/cache data/static

# Initialize databases
echo "🗄️  Initializing databases..."
python3 init_db.py

# Stop existing containers (if any)
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Pull latest images and build
echo "🔄 Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Check health
echo "🔍 Checking service health..."
sleep 10

# Show status
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check logs with:"
echo "   docker-compose -f docker-compose.prod.yml logs -f choynews-bot"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🔄 To restart:"
echo "   docker-compose -f docker-compose.prod.yml restart choynews-bot"
