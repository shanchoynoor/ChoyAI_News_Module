# News Digest Telegram Bot

A Telegram bot that delivers curated, 6-hourly news digests at 8 AM, 1 PM, 7 PM, and 11 PM (local time). It fetches the latest news across categories—Local (Bangladesh), Global, Tech, Sports, and Crypto—along with crypto market data, ensuring fresh updates without repetition.

## Features
- **Scheduled Updates**: Sends news digests at 8 AM, 1 PM, 7 PM, and 11 PM.
- **User Subscriptions**: Users can subscribe to receive news at scheduled times in their local timezone.
- **Category-Based News**: Covers Local (Bangladesh), Global, Tech, Sports, and Crypto news from reliable RSS feeds.
- **Crypto Market Insights**: Includes market cap, volume, Fear/Greed Index, big-cap prices, and top movers.
- **Smart Caching**: Caches crypto market data to reduce API calls and provide fallback data during API outages.
- **No Duplicates**: Tracks last fetch time to ensure only new news is sent.
- **Efficient Fetching**: Uses asynchronous HTTP requests (`aiohttp`) for fast RSS feed processing.
- **Telegram-Friendly**: Splits long messages to comply with Telegram's 4096-character limit.
- **User-Friendly Responses**: Responds to non-command messages with a helpful guide to available commands.

## Requirements
- Python 3.8+
- Packages: `aiohttp`, `requests`, `feedparser`, `python-dotenv`
- Telegram Bot Token and Chat ID
- Finnhub API Key (optional, for crypto data)
- CoinGecko API (used for crypto market data, no key required)

## Installation
1. Clone the repository:
```bash
   git clone https://github.com/yourusername/news-digest-bot.git
   cd news-digest-bot
```

2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install aiohttp requests feedparser python-dotenv
```

4. Create a .env file with the following:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
FINNHUB_API_KEY=your_finnhub_api_key
```

5. Run the bot:
```bash
python news.py
```

## Deployment with PM2

This bot can be deployed using PM2, a process manager for Node.js applications that can also manage Python processes.

1. Install PM2 if you haven't already:
```bash
npm install -g pm2
```

2. Start the bot using the provided ecosystem file:
```bash
pm2 start ecosystem.config.json
```

3. Check status:
```bash
pm2 status
```

4. View logs:
```bash
pm2 logs news-digest-bot  # For the main bot
pm2 logs news-digest-auto  # For the automatic scheduler
```

5. Set PM2 to start on system boot:
```bash
pm2 startup
pm2 save
```

## Usage
The bot processes these commands:

- `/start` - Initialize the bot and get a welcome message
- `/news` - Get the full daily news digest
- `/weather` - Get Dhaka weather
- `/cryptostats` - Get AI summary of crypto market
- `/coin` - Get price and 24h change for a coin (e.g. /btc, /eth, /doge)
- `/coinstats` - Get price, 24h change, and AI summary (e.g. /btcstats)
- `/timezone <zone>` - Set your timezone for news digest times
- `/subscribe` - Get news digests automatically at 8am, 1pm, 7pm, and 11pm in your local timezone
- `/unsubscribe` - Stop receiving automatic news digests
- `/status` - Check your subscription status and timezone
- `/support` - Contact the developer for support
- `/help` - Show this help message

### Testing
To test the crypto data fetching functionality:

```bash
python test_crypto_data.py
```

This script will test all crypto data fetching functions and verify that the caching mechanism is working properly.

### Each digest includes:
- Local News: Top stories from Bangladesh (e.g., Prothom Alo, The Daily Star).
- Global News: International headlines (e.g., BBC, Reuters).
- Tech News: Technology updates (e.g., TechCrunch, The Verge).
- Sports News: Sports highlights (e.g., ESPN, Sky Sports).
- Crypto News: Cryptocurrency updates (e.g., Cointelegraph, Coindesk).
- Crypto Market: Market cap, volume, Fear/Greed Index, top gainers/losers, and big-cap prices.
- Messages are formatted in Markdown, with clickable links and publication times.

### Scheduling
To automate the bot, set up a cron job (Linux/Mac) or Task Scheduler (Windows). Example cron job for 8 AM, 1 PM, 7 PM, 12 AM (local time):

```bash
0 8,13,19,0 * * * /path/to/venv/bin/python /path/to/news-digest-bot/news.py
```
<br></br>
## Acknowledgments
- RSS feeds from various news sources.
- CoinGecko API for crypto market data.
- Telegram Bot API for messaging.