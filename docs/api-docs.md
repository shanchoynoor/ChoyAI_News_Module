# API Documentation

This document describes the APIs used by the Choy News Telegram Bot, including both internal modules and external service integrations.

## Internal API Modules

### Telegram API Module

Located in `choynews/api/telegram.py`

#### Functions

##### `send_telegram(message, chat_id)`
Sends a formatted message to a Telegram chat.

- **Parameters**:
  - `message` (str): The message to send
  - `chat_id` (str): The Telegram chat ID to send the message to
- **Returns**: Boolean indicating success or failure

##### `send_telegram_photo(photo_url, caption, chat_id)`
Sends a photo with caption to a Telegram chat.

- **Parameters**:
  - `photo_url` (str): URL of the photo to send
  - `caption` (str): Caption text for the photo
  - `chat_id` (str): The Telegram chat ID to send the photo to
- **Returns**: Boolean indicating success or failure

### Digest Builder Module

Located in `choynews/core/digest_builder.py`

#### Functions

##### `build_news_digest(user)`

Builds a personalized news digest for a user.

- **Parameters**:
  - `user` (dict): User information including preferences
- **Returns**: Formatted digest string ready to send

##### `fetch_category_news(category, sources, limit=5)`

Fetches news for a specific category from multiple sources.

- **Parameters**:
  - `category` (str): News category to fetch
  - `sources` (list): List of source URLs to fetch from
  - `limit` (int, optional): Maximum number of items to fetch per source
- **Returns**: List of news items

### Advanced News Fetcher Module

Located in `choynews/core/advanced_news_fetcher.py`

#### Functions

##### `get_full_news_digest()`

Generates a comprehensive news digest with breaking news prioritization and AI analysis.

- **Returns**: Complete formatted news digest with crypto market analysis
- **Features**: 
  - Breaking news detection (≤20 minutes)
  - Duplicate news filtering
  - AI-powered crypto market analysis
  - Weather integration

##### `get_individual_crypto_stats(symbol)`

Fetches detailed cryptocurrency statistics for any coin.

- **Parameters**:
  - `symbol` (str): Cryptocurrency symbol (e.g., 'btc', 'eth', 'pepe')
- **Returns**: Formatted statistics including price, volume, market cap, and 52-week range

##### `get_individual_crypto_stats_with_ai(symbol)`

Fetches detailed cryptocurrency statistics with AI analysis and trading signals.

- **Parameters**:
  - `symbol` (str): Cryptocurrency symbol
- **Returns**: Comprehensive analysis with technicals, forecast, and buy/sell/hold signals

### News Fetcher Module

Located in `choynews/core/news_fetcher.py`

#### Functions

##### `get_compact_news_digest()`

Generates a compact news digest optimized for mobile viewing.

- **Returns**: Formatted compact news digest with [SEE MORE] buttons
- **Features**:
  - Compact weather display
  - Limited news items per category
  - Breaking news alerts
  - Clean formatting without emojis

##### `get_category_news(category, limit=10)`

Fetches detailed news for a specific category with flexible age filtering.

- **Parameters**:
  - `category` (str): Category type ('local', 'global', 'tech', 'sports', 'finance')
  - `limit` (int, optional): Number of news items to return
- **Returns**: Formatted news list for the category

### User Subscription Module

Located in `choynews/data/subscriptions.py`

#### Functions

##### `subscribe_user(user_id, chat_id, timezone='UTC')`
Subscribe a user to automatic news digests.

- **Parameters**:
  - `user_id` (int): Telegram user ID
  - `chat_id` (int): Telegram chat ID
  - `timezone` (str, optional): User's timezone
- **Returns**: Boolean indicating success or failure

##### `unsubscribe_user(user_id)`
Unsubscribe a user from automatic news digests.

- **Parameters**:
  - `user_id` (int): Telegram user ID
- **Returns**: Boolean indicating success or failure

## External API Integrations

### Telegram Bot API

The bot uses the [python-telegram-bot](https://python-telegram-bot.readthedocs.io/) library to interact with the Telegram Bot API.

- **API Documentation**: [Telegram Bot API](https://core.telegram.org/bots/api)
- **Authentication**: Bot token configured in environment variables

### News API Endpoints

The bot fetches news from various RSS feeds:

**Local Bangladesh Sources:**
- The Daily Star: https://www.thedailystar.net/rss.xml
- Prothom Alo: https://www.prothomalo.com/feed
- BDNews24: https://bangla.bdnews24.com/rss.xml
- Dhaka Tribune: https://www.dhakatribune.com/feed
- Financial Express: https://thefinancialexpress.com.bd/feed

**Global Sources:**
- BBC News: https://feeds.bbci.co.uk/news/rss.xml
- CNN: http://rss.cnn.com/rss/edition.rss
- Al Jazeera: https://www.aljazeera.com/xml/rss/all.xml
- Reuters: https://news.yahoo.com/rss/
- The Guardian: https://www.theguardian.com/world/rss

**Technology Sources:**
- TechCrunch: https://techcrunch.com/feed/
- The Verge: https://www.theverge.com/rss/index.xml
- Ars Technica: http://feeds.arstechnica.com/arstechnica/index/
- Wired: https://www.wired.com/feed/rss

**Sports Sources:**
- ESPN: https://www.espn.com/espn/rss/news
- BBC Sport: http://feeds.bbci.co.uk/sport/rss.xml
- Sky Sports: http://www.skysports.com/rss/12040

**Cryptocurrency Sources:**
- CoinDesk: https://www.coindesk.com/arc/outboundfeeds/rss/
- Cointelegraph: https://cointelegraph.com/rss
- The Block: https://www.theblock.co/rss.xml
- Decrypt: https://decrypt.co/feed

### Cryptocurrency APIs

- **CoinGecko API**: Used for cryptocurrency prices and market data
  - Base URL: https://api.coingecko.com/api/v3/
  - No authentication required (free tier)
  - Endpoints used:
    - `/coins/markets`: Get cryptocurrency prices
    - `/global`: Get global market data

- **Alternative.me API**: Used for Fear & Greed Index
  - Endpoint: https://api.alternative.me/fng/
  - No authentication required

### Weather API

- **WeatherAPI**: Used for weather information
  - Base URL: https://api.weatherapi.com/v1/
  - Authentication: API key in environment variables
  - Endpoints used:
    - `/current.json`: Get current weather with air quality index

### AI Analysis APIs

- **DeepSeek API**: Used for cryptocurrency market analysis and trading signals
  - Base URL: https://api.deepseek.com/
  - Authentication: API key in environment variables
  - Model: deepseek-chat
  - Features:
    - Market sentiment analysis
    - Technical analysis with RSI, support/resistance levels
    - 24-hour price predictions
    - Buy/sell/hold recommendations

### Calendar APIs

- **Calendarific API**: Used for Bangladesh holiday information
  - Base URL: https://calendarific.com/api/v2/
  - Authentication: API key in environment variables
  - Endpoints used:
    - `/holidays`: Get Bangladesh holidays for specific dates

## Configuration

### Environment Variables

The following environment variables must be configured:

- `TELEGRAM_TOKEN` or `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `AUTO_NEWS_CHAT_ID`: Chat ID for automatic news delivery
- `DEEPSEEK_API`: DeepSeek API key for AI analysis
- `WEATHERAPI_KEY`: WeatherAPI key for weather data
- `CALENDARIFIC_API_KEY`: Calendarific API key for holidays
- `TWELVE_DATA_API_KEY`: Twelve Data API key for market indices

### Optional Configuration

- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Log file path (default: logs/choynews.log)
- `LOG_MAX_BYTES`: Maximum log file size (default: 10MB)

## Error Handling

All API calls implement error handling with exponential backoff retry logic for transient failures. Failed API calls are logged and fallback to cached data when available.
