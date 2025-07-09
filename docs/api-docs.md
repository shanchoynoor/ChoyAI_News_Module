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

- BBC News: https://feeds.bbci.co.uk/news/world/rss.xml
- Reuters: https://www.reutersagency.com/feed/
- TechCrunch: https://techcrunch.com/feed/
- ESPN: https://www.espn.com/espn/rss/news
- Cointelegraph: https://cointelegraph.com/rss

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
    - `/current.json`: Get current weather

## Error Handling

All API calls implement error handling with exponential backoff retry logic for transient failures. Failed API calls are logged and fallback to cached data when available.
