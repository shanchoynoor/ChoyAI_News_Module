#!/bin/bash

# ChoyNewsBot Server Setup and Fix Script
# This script will properly set up the Python environment and fix common issues

set -e  # Exit on any error

echo "=== ChoyNewsBot Server Setup Script ==="
echo "Starting server setup and fixes..."
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -d "choynews" ]; then
    echo "❌ Error: This script must be run from the ChoyAI_News_Module directory"
    echo "Please cd to the project root directory and try again"
    exit 1
fi

echo "✅ Running from correct directory: $(pwd)"

# Step 1: Check Python installation
echo
echo "=== Step 1: Checking Python Installation ==="
if ! command_exists python3; then
    echo "❌ python3 is not installed. Installing..."
    # For Ubuntu/Debian
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    # For CentOS/RHEL
    elif command_exists yum; then
        sudo yum install -y python3 python3-pip
    else
        echo "❌ Cannot automatically install python3. Please install it manually."
        exit 1
    fi
else
    echo "✅ python3 is installed: $(python3 --version)"
fi

# Step 2: Remove old virtual environment if corrupted
echo
echo "=== Step 2: Setting up Virtual Environment ==="
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

echo "Creating new virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

# Verify venv is working
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Step 3: Upgrade pip and install dependencies
echo
echo "=== Step 3: Installing Dependencies ==="
echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing package in development mode..."
pip install -e .

# Step 4: Fix the choynews executable
echo
echo "=== Step 4: Fixing choynews Executable ==="

# Make sure bin directory exists
mkdir -p bin

# Create a more robust choynews script
cat > bin/choynews << 'EOF'
#!/bin/bash
# ChoyNewsBot Launcher Script
# This script ensures the virtual environment is activated and runs the bot

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source "$PROJECT_DIR/venv/bin/activate"
    else
        echo "❌ Virtual environment not found at $PROJECT_DIR/venv"
        echo "Please run the setup script first."
        exit 1
    fi
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run the bot
echo "Starting ChoyNewsBot..."
python3 -m choynews.core.bot "$@"
EOF

# Make the script executable
chmod +x bin/choynews

echo "✅ Created robust choynews launcher script"

# Step 5: Create systemd service file (optional)
echo
echo "=== Step 5: Creating Systemd Service (Optional) ==="
cat > tools/deploy/choynews.service << EOF
[Unit]
Description=ChoyNewsBot Telegram Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/bin/choynews
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created systemd service file at tools/deploy/choynews.service"

# Step 6: Test the installation
echo
echo "=== Step 6: Testing Installation ==="
echo "Testing Python module import..."
python3 -c "import choynews; print('✅ ChoyNews module imports successfully')"

echo "Testing choynews executable..."
if [ -x "bin/choynews" ]; then
    echo "✅ choynews executable is ready"
else
    echo "❌ choynews executable is not executable"
    chmod +x bin/choynews
fi

echo
echo "=== Setup Complete! ==="
echo
echo "To start the bot:"
echo "1. Make sure your .env file is configured with bot tokens"
echo "2. Run: ./bin/choynews"
echo
echo "To install as a system service:"
echo "1. sudo cp tools/deploy/choynews.service /etc/systemd/system/"
echo "2. sudo systemctl enable choynews"
echo "3. sudo systemctl start choynews"
echo
echo "To check logs:"
echo "   sudo journalctl -u choynews -f"
echo
