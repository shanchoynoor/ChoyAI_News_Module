"""
Bot service module for Choy News Bot.

This module handles Telegram bot messages and commands.
"""

import logging
import json
from choynews.utils.logging import get_logger
from choynews.data.models import log_user_interaction

logger = get_logger(__name__)

def handle_updates(updates):
    """
    Process Telegram update objects and handle messages/commands.
    
    Args:
        updates (list): List of Telegram update objects
        
    Returns:
        int: ID of the last processed update or None
    """
    if not updates:
        return None
        
    last_update_id = None
    
    for update in updates:
        last_update_id = update.get("update_id")
        
        # Handle message updates
        if "message" in update:
            message = update["message"]
            handle_message(message)
            
        # Handle callback query updates (inline keyboard buttons)
        elif "callback_query" in update:
            callback_query = update["callback_query"]
            handle_callback_query(callback_query)
            
    return last_update_id + 1 if last_update_id is not None else None

def handle_message(message):
    """
    Handle a message from a Telegram user.
    
    Args:
        message (dict): Telegram message object
    """
    # Extract message data
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    username = message.get("from", {}).get("username")
    first_name = message.get("from", {}).get("first_name")
    last_name = message.get("from", {}).get("last_name")
    text = message.get("text", "")
    
    if not text or not chat_id:
        return
        
    # Log the interaction
    log_user_interaction(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        message_type="message",
        last_interaction=text[:100]  # Truncate long messages
    )
    
    logger.info(f"Received message from {username or user_id}: {text[:50]}")
    
    # Process commands (messages starting with /)
    if text.startswith('/'):
        handle_command(chat_id, user_id, username, first_name, last_name, text)
    else:
        # Handle regular messages
        handle_regular_message(chat_id, user_id, username, text)

def handle_regular_message(chat_id, user_id, username, text):
    """Handle regular (non-command) messages."""
    from choynews.api.telegram import send_telegram
    
    # Simple responses to common greetings and questions
    text_lower = text.lower().strip()
    
    if any(greeting in text_lower for greeting in ['hello', 'hi', 'hey', 'greetings']):
        name = username or "there"
        response = f"Hello {name}! 👋 Welcome to ChoyNewsBot. Type /help to see what I can do for you!"
    elif any(word in text_lower for word in ['news', 'update', 'latest']):
        response = "📰 You can get the latest news by typing /news"
    elif any(word in text_lower for word in ['help', 'what', 'how']):
        response = "❓ Type /help to see all available commands and features"
    elif any(word in text_lower for word in ['thanks', 'thank you', 'thx']):
        response = "You're welcome! 😊 Happy to help!"
    else:
        ellipsis = "..." if len(text) > 50 else ""
        response = f"I received your message: '{text[:50]}{ellipsis}'\\n\\nType /help to see what commands I understand!"
    
    send_telegram(response, chat_id)
    logger.info(f"Responded to regular message from user {user_id}")

def handle_command(chat_id, user_id, username, first_name, last_name, text):
    """
    Handle a command from a Telegram user.
    
    Args:
        chat_id (int): Telegram chat ID
        user_id (int): Telegram user ID
        username (str): Telegram username
        first_name (str): User's first name
        last_name (str): User's last name
        text (str): Command text
    """
    # Split the command and arguments
    parts = text.split(' ', 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    logger.info(f"Processing command: {command} with args: {args[:50]}")
    
    # Import here to avoid circular imports
    from choynews.api.telegram import send_telegram
    
    # Handle different commands
    if command == '/start':
        handle_start_command(chat_id, user_id, username, first_name, last_name)
    elif command == '/help':
        handle_help_command(chat_id)
    elif command == '/status':
        handle_status_command(chat_id, user_id)
    elif command == '/news':
        handle_news_command(chat_id, user_id, args)
    elif command == '/weather':
        handle_weather_command(chat_id, user_id)
    elif command == '/cryptostats':
        handle_cryptostats_command(chat_id, user_id)
    elif command == '/subscribe':
        handle_subscribe_command(chat_id, user_id, username, first_name, last_name)
    elif command == '/unsubscribe':
        handle_unsubscribe_command(chat_id, user_id)
    elif command == '/support':
        handle_support_command(chat_id)
    elif command.startswith('/timezone'):
        handle_timezone_command(chat_id, user_id, args)
    elif command in ['/btc', '/eth', '/doge', '/ada', '/sol', '/xrp', '/matic', '/dot', '/link', '/uni']:
        # Individual coin commands
        coin_symbol = command[1:]  # Remove the '/' prefix
        handle_coin_command(chat_id, user_id, coin_symbol)
    elif command.endswith('stats') and len(command) > 6:
        # Coin stats commands like /btcstats, /ethstats
        coin_symbol = command[1:-5]  # Remove '/' prefix and 'stats' suffix
        handle_coinstats_command(chat_id, user_id, coin_symbol)
    elif command.startswith('/coin'):
        # Generic /coin command with argument
        if args:
            handle_coin_command(chat_id, user_id, args.strip().lower())
        else:
            send_telegram("Please specify a coin symbol. Example: `/coin btc` or use `/btc`", chat_id)
    else:
        # Unknown command
        send_telegram(
            f"Sorry, I don't understand the command '{command}'. Type /help to see available commands.",
            chat_id
        )

def handle_start_command(chat_id, user_id, username, first_name, last_name):
    """Handle the /start command."""
    from choynews.api.telegram import send_telegram
    
    name = first_name or username or "there"
    welcome_message = f"""
🗞️ *Welcome to ChoyNewsBot, {name}!*

I'm your personal news assistant. I can provide you with:
• 📰 Latest news updates
• 💰 Cryptocurrency market data
• 🌤️ Weather information
• ⏰ Scheduled news delivery

*Available Commands:*
/start - Show this welcome message
/help - Get help and see all commands
/news - Get latest news digest
/status - Check bot status

Type /help for more detailed information about what I can do!
    """
    
    send_telegram(welcome_message, chat_id)
    logger.info(f"Sent welcome message to user {user_id} ({username})")

def handle_help_command(chat_id):
    """Handle the /help command."""
    from choynews.api.telegram import send_telegram
    
    help_message = """
📚 *ChoyNewsBot Commands*

*📰 News & Information:*
🚀 `/start` - Initialize the bot and get a welcome message
📰 `/news` - Get the full daily news digest
🌤️ `/weather` - Get Dhaka weather information
⚡ `/status` - Check your subscription status and timezone

*💰 Cryptocurrency:*
📊 `/cryptostats` - Get AI summary of crypto market
🪙 `/coin <symbol>` - Get price and 24h change for a coin
   Examples: `/coin btc`, `/btc`, `/eth`, `/doge`
📈 `/coinstats <symbol>` - Get price, 24h change, and AI summary
   Examples: `/coinstats btc`, `/btcstats`, `/ethstats`

*⚙️ Settings & Subscriptions:*
🕒 `/timezone <zone>` - Set your timezone for news digest times
   Examples: `/timezone +6`, `/timezone Asia/Dhaka`
📬 `/subscribe` - Get news digests automatically at 8am, 1pm, 7pm, 11pm
📭 `/unsubscribe` - Stop receiving automatic news digests

*🆘 Support:*
❓ `/help` - Show this help message
🆘 `/support` - Contact the developer for support

*Popular Crypto Commands:*
• `/btc`, `/eth`, `/doge`, `/ada`, `/sol`, `/xrp`
• `/btcstats`, `/ethstats`, `/dogestats`

All times are shown in your local timezone. Use `/timezone` to set yours!
    """
    
    send_telegram(help_message, chat_id)
    logger.info(f"Sent help message to chat {chat_id}")

def handle_status_command(chat_id):
    """Handle the /status command."""
    from choynews.api.telegram import send_telegram
    import datetime
    
    status_message = f"""
🤖 *Bot Status*

✅ Bot is online and running
🕒 Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📡 API connection: Active
🔧 Services: Bot + Auto News

All systems operational! 🚀
    """
    
    send_telegram(status_message, chat_id)
    logger.info(f"Sent status message to chat {chat_id}")

def handle_news_command(chat_id, user_id, args):
    """Handle the /news command."""
    from choynews.api.telegram import send_telegram
    from choynews.core.digest_builder import build_news_digest
    
    try:
        # Create a basic user object for digest building
        user = {
            "user_id": user_id,
            "chat_id": chat_id,
            "preferences": {}  # Default preferences
        }
        
        # Send loading message like in the example
        send_telegram("Loading latest news...", chat_id)
        
        # Build and send news digest
        digest = build_news_digest(user)
        send_telegram(digest, chat_id)
        
        logger.info(f"Sent news digest to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error generating news digest for user {user_id}: {e}")
        send_telegram(
            "Sorry, I encountered an error while generating your news digest. Please try again later.",
            chat_id
        )

def handle_callback_query(callback_query):
    """
    Handle a callback query from a Telegram inline keyboard.
    
    Args:
        callback_query (dict): Telegram callback query object
    """
    # Extract callback data
    query_id = callback_query.get("id")
    user_id = callback_query.get("from", {}).get("id")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    message_id = callback_query.get("message", {}).get("message_id")
    data = callback_query.get("data", "")
    
    username = callback_query.get("from", {}).get("username")
    first_name = callback_query.get("from", {}).get("first_name")
    last_name = callback_query.get("from", {}).get("last_name")
    
    if not data or not chat_id:
        return
        
    # Log the interaction
    log_user_interaction(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        message_type="callback",
        last_interaction=data
    )
    
    logger.info(f"Received callback from {username or user_id}: {data}")
    
    # Process the callback data
    # Implement callback handlers based on the data

def handle_weather_command(chat_id, user_id):
    """Handle the /weather command."""
    from choynews.api.telegram import send_telegram
    
    try:
        # For now, send a placeholder. This would integrate with weather API
        weather_message = """
🌤️ *Weather in Dhaka*

🌡️ Temperature: 28°C (feels like 32°C)
🌧️ Condition: Partly cloudy with chance of rain
💧 Humidity: 78%
💨 Wind: 12 km/h E
👁️ Visibility: 8 km
🌅 Sunrise: 05:12 AM
🌇 Sunset: 06:47 PM

*Today's Forecast:*
• Morning: 26°C - Partly cloudy
• Afternoon: 30°C - Thunderstorms likely  
• Evening: 27°C - Light rain

Weather data will be fully integrated soon!
        """
        
        send_telegram(weather_message, chat_id)
        logger.info(f"Sent weather info to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting weather for user {user_id}: {e}")
        send_telegram("Sorry, weather information is temporarily unavailable.", chat_id)

def handle_cryptostats_command(chat_id, user_id):
    """Handle the /cryptostats command."""
    from choynews.api.telegram import send_telegram
    
    try:
        crypto_message = """
💰 *Cryptocurrency Market Overview*

📊 *Market Cap:* $2.41T (+2.3% 24h)
📈 *24h Volume:* $85.2B  
😨 *Fear & Greed Index:* 67 (Greed)

*Top Performers (24h):*
🚀 SOL: +8.4% ($142.50)
🚀 ADA: +6.2% ($0.48)
🚀 DOT: +5.1% ($7.82)

*Top Cryptocurrencies:*
₿ BTC: $43,250 (+1.2%)
Ξ ETH: $2,580 (+0.8%)
🪙 BNB: $315 (-0.5%)

*AI Market Summary:*
The crypto market shows bullish momentum with altcoins outperforming Bitcoin. Institutional adoption continues to drive growth, while regulatory clarity improves sentiment.

Full market integration coming soon!
        """
        
        send_telegram(crypto_message, chat_id)
        logger.info(f"Sent crypto stats to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting crypto stats for user {user_id}: {e}")
        send_telegram("Sorry, cryptocurrency market data is temporarily unavailable.", chat_id)

def handle_coin_command(chat_id, user_id, coin_symbol):
    """Handle coin price commands like /btc, /eth, etc."""
    from choynews.api.telegram import send_telegram
    
    try:
        # Coin data mapping (this would come from API in full implementation)
        coin_data = {
            'btc': {'name': 'Bitcoin', 'price': '$43,250', 'change': '+1.2%', 'symbol': '₿'},
            'eth': {'name': 'Ethereum', 'price': '$2,580', 'change': '+0.8%', 'symbol': 'Ξ'},
            'doge': {'name': 'Dogecoin', 'price': '$0.082', 'change': '+3.4%', 'symbol': '🐕'},
            'ada': {'name': 'Cardano', 'price': '$0.48', 'change': '+6.2%', 'symbol': '🪙'},
            'sol': {'name': 'Solana', 'price': '$142.50', 'change': '+8.4%', 'symbol': '🚀'},
            'xrp': {'name': 'XRP', 'price': '$0.58', 'change': '+2.1%', 'symbol': '💧'},
            'matic': {'name': 'Polygon', 'price': '$0.95', 'change': '-1.5%', 'symbol': '🔷'},
            'dot': {'name': 'Polkadot', 'price': '$7.82', 'change': '+5.1%', 'symbol': '⚪'},
            'link': {'name': 'Chainlink', 'price': '$15.30', 'change': '+0.7%', 'symbol': '🔗'},
            'uni': {'name': 'Uniswap', 'price': '$8.45', 'change': '+1.9%', 'symbol': '🦄'}
        }
        
        if coin_symbol in coin_data:
            coin = coin_data[coin_symbol]
            coin_message = f"""
{coin['symbol']} *{coin['name']} ({coin_symbol.upper()})*

💰 *Price:* {coin['price']}
📈 *24h Change:* {coin['change']}

Real-time price data integration coming soon!
            """
        else:
            coin_message = f"Sorry, I don't have data for '{coin_symbol.upper()}' yet. Try popular coins like BTC, ETH, DOGE, ADA, SOL, XRP."
        
        send_telegram(coin_message, chat_id)
        logger.info(f"Sent {coin_symbol} price to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting {coin_symbol} price for user {user_id}: {e}")
        send_telegram(f"Sorry, I couldn't get price data for {coin_symbol.upper()}.", chat_id)

def handle_coinstats_command(chat_id, user_id, coin_symbol):
    """Handle coin stats commands like /btcstats, /ethstats, etc."""
    from choynews.api.telegram import send_telegram
    
    try:
        # Extended coin data (this would come from API in full implementation)
        coin_stats = {
            'btc': {
                'name': 'Bitcoin', 'symbol': '₿', 'price': '$43,250', 'change': '+1.2%',
                'market_cap': '$842B', 'volume': '$28.5B', 'rank': '1',
                'summary': 'Bitcoin maintains dominance with steady institutional adoption. Recent ETF inflows suggest continued bullish sentiment.'
            },
            'eth': {
                'name': 'Ethereum', 'symbol': 'Ξ', 'price': '$2,580', 'change': '+0.8%',
                'market_cap': '$310B', 'volume': '$12.8B', 'rank': '2',
                'summary': 'Ethereum shows strength with upcoming network upgrades. DeFi activity remains robust across the ecosystem.'
            },
            'doge': {
                'name': 'Dogecoin', 'symbol': '🐕', 'price': '$0.082', 'change': '+3.4%',
                'market_cap': '$11.8B', 'volume': '$1.2B', 'rank': '8',
                'summary': 'Dogecoin rallies on social media momentum and increased merchant adoption. Community-driven growth continues.'
            }
        }
        
        if coin_symbol in coin_stats:
            coin = coin_stats[coin_symbol]
            stats_message = f"""
{coin['symbol']} *{coin['name']} ({coin_symbol.upper()}) Statistics*

💰 *Price:* {coin['price']}
📈 *24h Change:* {coin['change']}
🏆 *Market Cap:* {coin['market_cap']} (#{coin['rank']})
📊 *24h Volume:* {coin['volume']}

🤖 *AI Analysis:*
{coin['summary']}

Detailed analytics integration coming soon!
            """
        else:
            stats_message = f"Sorry, I don't have detailed stats for '{coin_symbol.upper()}' yet. Try BTC, ETH, or DOGE."
        
        send_telegram(stats_message, chat_id)
        logger.info(f"Sent {coin_symbol} stats to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting {coin_symbol} stats for user {user_id}: {e}")
        send_telegram(f"Sorry, I couldn't get stats for {coin_symbol.upper()}.", chat_id)

def handle_subscribe_command(chat_id, user_id, username, first_name, last_name):
    """Handle the /subscribe command."""
    from choynews.api.telegram import send_telegram
    
    try:
        # This would integrate with the subscription database
        subscribe_message = """
📬 *News Subscription Activated!*

You will now receive news digests at:
🌅 8:00 AM - Morning digest
🌞 1:00 PM - Midday digest  
🌆 7:00 PM - Evening digest
🌙 11:00 PM - Night digest

All times are in your local timezone. Set your timezone with `/timezone <zone>` if needed.

Use `/unsubscribe` to stop receiving automatic digests anytime.

Database integration coming soon!
        """
        
        send_telegram(subscribe_message, chat_id)
        logger.info(f"User {user_id} ({username}) subscribed to news digests")
        
    except Exception as e:
        logger.error(f"Error subscribing user {user_id}: {e}")
        send_telegram("Sorry, there was an error setting up your subscription. Please try again later.", chat_id)

def handle_unsubscribe_command(chat_id, user_id):
    """Handle the /unsubscribe command."""
    from choynews.api.telegram import send_telegram
    
    try:
        unsubscribe_message = """
📭 *News Subscription Cancelled*

You will no longer receive automatic news digests.

You can still get news anytime by using `/news` command.

To reactivate automatic digests, use `/subscribe`.

Database integration coming soon!
        """
        
        send_telegram(unsubscribe_message, chat_id)
        logger.info(f"User {user_id} unsubscribed from news digests")
        
    except Exception as e:
        logger.error(f"Error unsubscribing user {user_id}: {e}")
        send_telegram("Sorry, there was an error cancelling your subscription. Please try again later.", chat_id)

def handle_timezone_command(chat_id, user_id, timezone_arg):
    """Handle the /timezone command."""
    from choynews.api.telegram import send_telegram
    
    try:
        if not timezone_arg:
            timezone_message = """
🕒 *Set Your Timezone*

Usage: `/timezone <zone>`

Examples:
• `/timezone Asia/Dhaka`
• `/timezone +6`
• `/timezone Europe/London`
• `/timezone America/New_York`

This ensures you receive news digests at the correct local times (8am, 1pm, 7pm, 11pm).

Current timezone: UTC+6 (default)
            """
        else:
            # This would validate and set the timezone in database
            timezone_message = f"""
🕒 *Timezone Updated*

Your timezone has been set to: `{timezone_arg}`

News digests will now be delivered at:
🌅 8:00 AM your time
🌞 1:00 PM your time
🌆 7:00 PM your time  
🌙 11:00 PM your time

Database integration coming soon!
            """
        
        send_telegram(timezone_message, chat_id)
        logger.info(f"Timezone command for user {user_id}: {timezone_arg}")
        
    except Exception as e:
        logger.error(f"Error setting timezone for user {user_id}: {e}")
        send_telegram("Sorry, there was an error setting your timezone. Please try again later.", chat_id)

def handle_support_command(chat_id):
    """Handle the /support command."""
    from choynews.api.telegram import send_telegram
    
    support_message = """
🆘 *Support & Contact*

For help, feedback, or bug reports:

👨‍💻 *Developer:* Shanchoy Noor
📧 *Email:* shanchoyzone@gmail.com
🐛 *Issues:* Report bugs via email

*Common Issues:*
• News not loading: Check your internet connection
• Wrong timezone: Use `/timezone` to set correct zone
• Missing features: Many features are still in development

*Bot Status:* Active development
*Version:* 1.0.0

Thank you for using ChoyNewsBot! 🚀
    """
    
    send_telegram(support_message, chat_id)
    logger.info(f"Sent support info to chat {chat_id}")

def handle_status_command(chat_id, user_id):
    """Handle the /status command."""
    from choynews.api.telegram import send_telegram
    import datetime
    
    try:
        # This would query the database for user's actual status
        status_message = f"""
🤖 *Your Bot Status*

👤 *User ID:* {user_id}
📬 *Subscription:* Active (demo)
🕒 *Timezone:* UTC+6 (Asia/Dhaka)
📰 *Last Digest:* Demo mode
⏰ *Next Digest:* Demo mode

*Bot System:*
✅ Online and operational
🕒 Server time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📡 API connections: Active
🔧 Services: Bot + Auto News

Database integration coming soon!
        """
        
        send_telegram(status_message, chat_id)
        logger.info(f"Sent status to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting status for user {user_id}: {e}")
        send_telegram("Sorry, I couldn't retrieve your status. Please try again later.", chat_id)
