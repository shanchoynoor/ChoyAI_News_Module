# Installation Guide

This guide provides step-by-step instructions for installing the Choy News Telegram Bot.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git
- A Telegram Bot Token (create one via [@BotFather](https://t.me/botfather))

## Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/username/choynews.git
   cd choynews
   ```

2. **Create and activate a virtual environment**

   ```bash
   # Create virtual environment
   python -m venv .venv

   # Activate on Linux/Mac
   source .venv/bin/activate

   # Activate on Windows
   .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r config/requirements.txt
   ```

4. **Install the package in development mode**

   ```bash
   pip install -e .
   ```

5. **Configure environment variables**

   ```bash
   # Copy example environment file
   cp config/.env.example config/.env

   # Edit the .env file with your settings
   nano config/.env
   ```

   Required environment variables:
   
   - `TELEGRAM_TOKEN`: Your Telegram bot token
   - `AUTO_NEWS_CHAT_ID`: Chat ID for auto news (if using that feature)
   - Additional API keys as needed

## Running the Bot

After installation, you can run the bot using the following command:

```bash
# Run both the bot and auto news services
choynews --service both

# Run only the bot
choynews --service bot

# Run only the auto news service
choynews --service auto
```

## Troubleshooting

If you encounter any issues during installation:

1. Ensure Python 3.8+ is correctly installed: `python --version`
2. Check that all dependencies were installed: `pip list`
3. Verify that your environment variables are set correctly
4. Check the logs in the `logs/` directory for error messages
