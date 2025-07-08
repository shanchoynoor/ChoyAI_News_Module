# News Digest Bot

A comprehensive news aggregation and cryptocurrency information Telegram bot.

## Features

- Daily news digest from various sources and categories
- Cryptocurrency market data and price information
- Weather updates for Dhaka
- AI-powered crypto market analysis
- User timezone preferences
- Automatic scheduled digests
- Customizable user subscriptions

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- PM2 process manager
- Node.js (for PM2)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd news_digest
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys and settings:
   ```
   cp .env.example .env
   nano .env  # Edit with your actual API keys
   ```

4. Set up the environment and start the services:
   ```
   ./setup_server.sh
   ```

### Environment Variables

Create a `.env` file with the following variables:

```
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_token_here
AUTO_NEWS_CHAT_ID=your_chat_id_here

# API Keys
DEEPSEEK_API=your_deepseek_api_key_here
CALENDARIFIC_API_KEY=your_calendarific_api_key_here
```

## Running the Bot

### Using PM2 (Recommended)

The bot is configured to run with PM2, which provides process management and automatic restarts.

```bash
# Start both the bot and auto-news services
pm2 start ecosystem.config.json

# Check status
pm2 status

# View logs
pm2 logs news-digest-bot
pm2 logs news-digest-auto

# Restart services
pm2 restart news-digest-bot news-digest-auto

# Set up PM2 to start on system boot
pm2 startup
pm2 save
```

### Manual Run

For testing or development:

```bash
# Run the bot
python news.py

# Run the automatic digest sender
python auto_news.py
```

## Troubleshooting

If you encounter issues:

1. Check the logs:
   ```
   cat logs/news-bot-error.log
   cat logs/news-auto-error.log
   ```

2. Run the diagnostic script:
   ```
   ./diagnose.sh
   ```

3. Common issues:
   - Missing environment variables: Make sure your `.env` file has all required keys
   - Python dependency issues: Verify all requirements are installed with `pip install -r requirements.txt`
   - Permission issues: Ensure script files are executable (`chmod +x *.sh`)
   - Database problems: Check the permissions on `.db` files

4. To reset and restart:
   ```
   ./restart.sh
   ```

## Maintenance

### Updating the Coin List

The bot uses a local coin list for cryptocurrency information. Update it with:

```bash
python update_coinlist.py
```

### Backup

Backup important files regularly:

```bash
# Backup databases and configuration
tar -czvf news_digest_backup_$(date +%Y%m%d).tar.gz *.db .env ecosystem.config.json
```

## Commands

The bot supports the following commands:

- `/start` - Initialize the bot and get a welcome message
- `/news` - Get the full daily news digest
- `/weather` - Get Dhaka weather
- `/cryptostats` - Get AI summary of crypto market
- `/coin` - Get price and 24h change for a coin (e.g. /btc, /eth, /doge)
- `/coinstats` - Get price, 24h change, and AI summary (e.g. /btcstats)
- `/timezone` - Set your timezone for news digest times
- `/subscribe` - Get news digests automatically
- `/unsubscribe` - Stop receiving automatic news digests
- `/status` - Check your subscription status and timezone
- `/support` - Contact the developer for support
- `/help` - Show the help message

## License

[Your license information here]

## Author

Shanchoy
