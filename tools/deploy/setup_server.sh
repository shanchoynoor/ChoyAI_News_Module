#!/bin/bash

# ChoyNewsBot Production Server Setup Script
# Run this script on your production server to set up the bot

set -e  # Exit on any error

echo "🚀 ChoyNewsBot Production Setup"
echo "================================"
echo

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -d "choynews" ]; then
    echo "❌ Error: This script must be run from the ChoyAI_News_Module directory"
    echo "Please cd to the project root directory and try again"
    exit 1
fi

echo "✅ Running from correct directory: $(pwd)"
echo

# Step 1: Install system dependencies
echo "📦 Step 1: Installing system dependencies..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3 python3-pip python3-devel gcc
else
    echo "⚠️  Please manually install: python3, python3-pip, python3-venv"
fi

# Step 2: Create virtual environment
echo
echo "🐍 Step 2: Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

echo "✅ Virtual environment created and activated"

# Step 3: Upgrade pip and install dependencies
echo
echo "📋 Step 3: Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Install the package in development mode
pip install -e .

echo "✅ Dependencies installed successfully"

# Step 4: Create environment file template
echo
echo "⚙️  Step 4: Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# ChoyNewsBot Configuration
# Replace the placeholder values with your actual API keys

TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
WEATHER_API_KEY=your_weatherapi_key_here
NEWS_API_KEY=your_news_api_key_here
CALENDARIFIC_API_KEY=your_calendarific_key_here

# Database Configuration (Optional)
DATABASE_URL=sqlite:///data/choynews.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/choynews.log
EOF
    echo "📝 Created .env template file"
    echo "⚠️  IMPORTANT: Edit .env file with your actual API keys!"
else
    echo "✅ .env file already exists"
fi

# Step 5: Create necessary directories
echo
echo "📁 Step 5: Creating necessary directories..."
mkdir -p logs data/cache data/static

# Step 6: Test the installation
echo
echo "🧪 Step 6: Testing installation..."
echo "Testing Python module import..."
if python3 -c "import choynews; print('✅ ChoyNews module imports successfully')"; then
    echo "✅ Module import test passed"
else
    echo "❌ Module import test failed"
    exit 1
fi

# Step 7: Create startup script
echo
echo "🚀 Step 7: Creating startup script..."
cat > start_bot.sh << 'EOF'
#!/bin/bash
# ChoyNewsBot Startup Script

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment
source venv/bin/activate

# Start the bot
echo "🤖 Starting ChoyNewsBot..."
python3 -m choynews.core.bot
EOF

chmod +x start_bot.sh
echo "✅ Created start_bot.sh script"

# Step 8: Create systemd service file
echo
echo "🔧 Step 8: Creating systemd service file..."
mkdir -p tools/deploy
cat > tools/deploy/choynews.service << EOF
[Unit]
Description=ChoyNewsBot Telegram Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/start_bot.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created systemd service file"

# Final instructions
echo
echo "🎉 Setup Complete!"
echo "=================="
echo
echo "Next steps:"
echo "1. Edit the .env file with your API keys:"
echo "   nano .env"
echo
echo "2. Test the bot manually:"
echo "   ./start_bot.sh"
echo
echo "3. To install as a system service:"
echo "   sudo cp tools/deploy/choynews.service /etc/systemd/system/"
echo "   sudo systemctl enable choynews"
echo "   sudo systemctl start choynews"
echo
echo "4. To check service status:"
echo "   sudo systemctl status choynews"
echo
echo "5. To view logs:"
echo "   sudo journalctl -u choynews -f"
echo
echo "🔑 Required API Keys:"
echo "- Telegram Bot Token: https://t.me/BotFather"
echo "- Weather API Key: https://www.weatherapi.com/"
echo "- News API Key: https://newsapi.org/"
echo
echo "📖 Documentation: docs/deployment.md"
echo "🆘 Support: @shanchoynoor on Telegram"
echo