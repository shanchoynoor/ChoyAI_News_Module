"""
Bot service module for Choy News Bot.

This module handles Telegram bot messages and commands.
"""

import logging
import json
from utils.logging import get_logger
from data_modules.models import log_user_interaction

logger = get_logger(__name__)

# In-memory store for news items for [Details] callbacks
news_item_store = {}

def handle_updates(updates):
    """
    Process Telegram update objects and handle messages/commands.
    
    Args:
        updates (list): List of Telegram update objects
        
    Returns:
        int: ID of the last processed update or None if no updates
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
    from api.telegram import send_telegram
    
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
    from api.telegram import send_telegram
    
    # Handle different commands
    if command == '/start':
        handle_start_command(chat_id, user_id, username, first_name, last_name)
    elif command == '/help':
        handle_help_command(chat_id)
    elif command == '/status':
        handle_status_command(chat_id, user_id)
    elif command == '/server':
        handle_server_command(chat_id)
    elif command == '/news':
        handle_news_command(chat_id, user_id, args)
    elif command == '/weather':
        handle_weather_command(chat_id, user_id)
    elif command == '/cryptostats':
        handle_cryptostats_command(chat_id, user_id)
    elif command == '/local':
        handle_category_news_command(chat_id, user_id, 'local')
    elif command == '/global':
        handle_category_news_command(chat_id, user_id, 'global')
    elif command == '/tech':
        handle_category_news_command(chat_id, user_id, 'tech')
    elif command == '/sports':
        handle_category_news_command(chat_id, user_id, 'sports')
    elif command == '/finance':
        handle_category_news_command(chat_id, user_id, 'finance')
    elif command == '/subscribe':
        handle_subscribe_command(chat_id, user_id, username, first_name, last_name)
    elif command == '/unsubscribe':
        handle_unsubscribe_command(chat_id, user_id)
    elif command == '/support':
        handle_support_command(chat_id)
    elif command == '/about':
        handle_about_command(chat_id)
    elif command.startswith('/timezone'):
        handle_timezone_command(chat_id, user_id, args)
    elif command.endswith('stats') and len(command) > 6:
        # Coin stats commands like /btcstats, /ethstats, /pepestats
        coin_symbol = command[1:-5]  # Remove '/' prefix and 'stats' suffix
        handle_coinstats_command(chat_id, user_id, coin_symbol)
    elif command.startswith('/coin'):
        # Generic /coin command with argument
        if args:
            handle_coin_command(chat_id, user_id, args.strip().lower())
        else:
            send_telegram("Please specify a coin symbol. Example: `/coin btc` or use `/btc`", chat_id)
    elif command.startswith('/') and len(command) > 1:
        # Try to handle as coin symbol (e.g., /btc, /eth, /pepe, /shib, etc.)
        coin_symbol = command[1:]  # Remove the '/' prefix
        
        # Skip known non-coin commands
        if coin_symbol.lower() in ['start', 'help', 'news', 'weather', 'subscribe', 'unsubscribe', 
                                  'status', 'cryptostats', 'support', 'about', 'timezone', 'coin']:
            # Unknown command
            send_telegram(
                f"Sorry, I don't understand the command '{command}'. Type /help to see available commands.",
                chat_id
            )
        else:
            # Try as coin command
            handle_coin_command(chat_id, user_id, coin_symbol)
    else:
        # Unknown command
        send_telegram(
            f"Sorry, I don't understand the command '{command}'. Type /help to see available commands.",
            chat_id
        )

def handle_start_command(chat_id, user_id, username, first_name, last_name):
    """Handle the /start command."""
    from api.telegram import send_telegram
    
    name = first_name or username or "there"
    welcome_message = f"""
🗞️ *Welcome to ChoyNewsBot, {name}!*

I'm your personal news assistant. I can provide you with:
• 📰 Latest news updates
• 🌤️ Weather information
• 💰 Cryptocurrency market data
• ⏰ Scheduled news delivery

*Available Commands:*
/start - Show this welcome message
/news - Get latest news digest
/help - Get help and see all commands
/status - Check bot status
/about - Learn about ChoyNewsBot features


Type /help for more detailed information about what I can do!
    """
    
    send_telegram(welcome_message, chat_id)
    logger.info(f"Sent welcome message to user {user_id} ({username})")

def handle_help_command(chat_id):
    """Handle the /help command."""
    from api.telegram import send_telegram
    
    help_message = """
📚 *ChoyNewsBot Commands*

*📰 News & Information:*
🚀 /start - Initialize the bot and get a welcome message
📰 /news - Get the compact daily news digest
🌤️ /weather - Get Dhaka weather information
👤 /status - Check your subscription status and timezone
🤖 /server - Check bot server status and uptime

*📰 Category News (10 items each):*
🇧🇩 /local - Bangladesh local news
🌍 /global - International global news
🚀 /tech - Technology and innovation news
🏆 /sports - Sports news and updates
💼 /finance - Financial markets and business news

*💰 Cryptocurrency:*
📊 /cryptostats - Get AI summary of crypto market
🪙 /coin <symbol> - Get price and 24h change for any coin
   Examples: /coin btc, /btc, /eth, /pepe, /shib
📈 /<symbol>stats - Get detailed analysis with technicals, RSI, support/resistance
   Examples: /btcstats, /ethstats, /pepestats, /shibstats
📋 /coinstats <symbol> - Same as above, alternative format

*⚙️ Settings & Subscriptions:*
🕒 /timezone <zone> - Set your timezone for news digest times
   Examples: /timezone +6, /timezone Asia/Dhaka
📬 /subscribe - Get news digests automatically at 8am, 1pm, 7pm, 11pm
📭 /unsubscribe - Stop receiving automatic news digests

*🆘 Support:*
❓ /help - Show this help message
ℹ️ /about - Learn about ChoyNewsBot features and capabilities
🆘 /support - Contact the developer for support

*Popular Crypto Commands:*
• /btc, /eth, /doge, /ada, /sol, /xrp, /pepe, /shib - Quick price
• /btcstats, /ethstats, /dogestats, /pepestats - Detailed analysis with technicals, RSI, forecasts

🪙 *Supports 17,500+ coins from CoinGecko!* Try any coin symbol like /pepe, /shib, /link, /uni, etc.
📊 *Add 'stats' for detailed analysis:* /pepestats, /shibstats, /linkstats, etc.

All times are shown in your local timezone. Use /timezone to set yours!
    """
    
    send_telegram(help_message, chat_id)
    logger.info(f"Sent help message to chat {chat_id}")

def handle_status_command(chat_id, user_id):
    """Handle the /status command - show user subscription status and timezone."""
    from api.telegram import send_telegram
    
    try:
        # For now, we'll show placeholder info since subscription DB is not fully implemented
        # TODO: Integrate with actual subscription database when implemented
        
        status_message = f"""
👤 *Your Account Status*

📬 **Subscription Status:** Active (Demo)
🕒 **Your Timezone:** Asia/Dhaka (UTC+6) 
📅 **Auto Digest Schedule:**
   • Morning: 8:00 AM
   • Midday: 1:00 PM  
   • Evening: 7:00 PM
   • Night: 11:00 PM

🔧 **Available Commands:**
   • `/news` - Get latest news digest
   • `/weather` - Current weather in Dhaka
   • `/cryptostats` - Crypto market overview
   • `/timezone <zone>` - Change your timezone
   • `/unsubscribe` - Stop auto digests

Type `/help` for more commands.
        """
        
        send_telegram(status_message, chat_id)
        logger.info(f"Sent status message to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting user status for user {user_id}: {e}")
        send_telegram("Sorry, there was an error retrieving your status. Please try again later.", chat_id)

def handle_server_command(chat_id):
    """Handle the /server command - show server/bot status."""
    from api.telegram import send_telegram
    import datetime
    
    try:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        status_message = f"""
🤖 **BOT STATUS**
🕒 Current time: {current_time}
✅ Bot is online and running
📡 API connection: Active
🔧 Services: Bot + Auto News

All systems operational! 🚀
        """
        
        send_telegram(status_message, chat_id)
        logger.info(f"Sent server status message to chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error getting server status: {e}")
        send_telegram("Sorry, there was an error retrieving server status. Please try again later.", chat_id)

def handle_news_command(chat_id, user_id, args):
    """Handle the /news command with compact format and add inline keyboard for category navigation and details."""
    from api.telegram import send_telegram
    from core.news_fetcher import get_compact_news_digest
    try:
        # Send loading message
        send_telegram("📰 Loading latest news...", chat_id)
        # Build and send compact news digest
        digest, section_data, main_buttons = get_compact_news_digest()
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        # For each section, add a [SEE MORE] button next to the section title
        for section in section_data:
            see_more_btn = InlineKeyboardButton(f"{section['title']}: [SEE MORE]", callback_data=section['command'])
            keyboard.append([see_more_btn])
            # For each news item, add a [Details] button
            for item in section['news_items']:
                news_item_store[item['id']] = item
                keyboard.append([InlineKeyboardButton(f"[Details] {item['title'][:20]}...", callback_data=f"details_{item['id']}")])
        # Add a 2x3 grid of main category buttons at the bottom
        grid = []
        for i in range(0, len(main_buttons), 3):
            row = [InlineKeyboardButton(title, callback_data=command) for title, command in main_buttons[i:i+3]]
            grid.append(row)
        keyboard.extend(grid)
        reply_markup = InlineKeyboardMarkup(keyboard)
        from api.telegram import send_telegram_with_markup
        send_telegram_with_markup(digest, chat_id, reply_markup)
        logger.info(f"Sent compact news digest to user {user_id}")
    except Exception as e:
        logger.error(f"Error generating compact news digest for user {user_id}: {e}")
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
    # Handle category navigation
    if data in ['/local', '/global', '/tech', '/sports', '/finance', '/cryptostats']:
        if data == '/cryptostats':
            handle_cryptostats_command(chat_id, user_id)
        else:
            category = data[1:]
            handle_category_news_command(chat_id, user_id, category)
        # Optionally, answer the callback to remove the loading spinner
        try:
            from api.telegram import answer_callback_query
            answer_callback_query(query_id)
        except Exception:
            pass
    # Handle [Details] button for news item
    elif data.startswith('details_'):
        news_id = data[len('details_'):]
        item = news_item_store.get(news_id)
        if item:
            from core.news_fetcher import analyze_news_item
            summary = analyze_news_item(item['title'], item['summary'], item['source'])
            from api.telegram import send_telegram
            send_telegram(summary, chat_id)
        try:
            from api.telegram import answer_callback_query
            answer_callback_query(query_id)
        except Exception:
            pass
    # (You can add more callback handling here if needed)
    # (No further news or content after this)

def handle_weather_command(chat_id, user_id):
    """Handle the /weather command."""
    from api.telegram import send_telegram
    from core.news_fetcher import get_weather_data
    
    try:
        # Send loading message first
        send_telegram("🌤️ Getting latest weather data...", chat_id)
        
        # Get weather data
        weather_message = get_weather_data("Dhaka")
        send_telegram(weather_message, chat_id)
        
        logger.info(f"Sent weather info to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting weather for user {user_id}: {e}")
        send_telegram("Sorry, weather information is temporarily unavailable.", chat_id)

def handle_cryptostats_command(chat_id, user_id):
    """Handle the /cryptostats command."""
    from api.telegram import send_telegram
    from core.advanced_news_fetcher import get_crypto_stats_digest
    
    try:
        send_telegram("� Fetching latest crypto market data with AI analysis...", chat_id)
        
        crypto_section = get_crypto_stats_digest()
        if crypto_section:
            send_telegram(crypto_section, chat_id)
        else:
            send_telegram("Sorry, cryptocurrency market data is temporarily unavailable.", chat_id)
        
        logger.info(f"Sent crypto stats to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting crypto stats for user {user_id}: {e}")
        send_telegram("Sorry, cryptocurrency market data is temporarily unavailable.", chat_id)

def handle_coin_command(chat_id, user_id, coin_symbol):
    """Handle coin price commands like /btc, /eth, etc."""
    from api.telegram import send_telegram
    from core.advanced_news_fetcher import get_individual_crypto_stats
    
    try:
        send_telegram(f"🔄 Fetching latest {coin_symbol.upper()} data...", chat_id)
        
        coin_data = get_individual_crypto_stats(coin_symbol)
        if coin_data:
            send_telegram(coin_data, chat_id)
        else:
            send_telegram(f"Sorry, I couldn't find '{coin_symbol.upper()}' on CoinGecko. Please check the symbol and try again. Example: `/pepe` for PEPE, `/btc` for Bitcoin.", chat_id)
        
        logger.info(f"Sent {coin_symbol} price to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting {coin_symbol} price for user {user_id}: {e}")
        send_telegram(f"Sorry, I couldn't get price data for {coin_symbol.upper()}.", chat_id)

def handle_coinstats_command(chat_id, user_id, coin_symbol):
    """Handle coin stats commands like /btcstats, /ethstats, /pepestats, etc."""
    from api.telegram import send_telegram
    from core.news_fetcher import fetch_coin_detailed_stats
    
    try:
        send_telegram(f"🔄 Analyzing {coin_symbol.upper()} with advanced analytics...", chat_id)
        
        # Use the new detailed analysis function
        coin_analysis = fetch_coin_detailed_stats(coin_symbol)
        send_telegram(coin_analysis, chat_id)
        
        logger.info(f"Sent {coin_symbol} detailed stats to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error getting {coin_symbol} detailed stats for user {user_id}: {e}")
        send_telegram(f"Sorry, I couldn't get detailed stats for {coin_symbol.upper()}. Please try again later.", chat_id)

def handle_subscribe_command(chat_id, user_id, username, first_name, last_name):
    """Handle the /subscribe command."""
    from api.telegram import send_telegram
    
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
    from api.telegram import send_telegram
    
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
    from api.telegram import send_telegram
    
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
    from api.telegram import send_telegram
    
    support_message = """
🆘 *Support & Contact*

For help, feedback, or bug reports:

👨‍💻 *Developer:* Shanchoy Noor
� *Message:* @shanchoynoor
�📧 *Email:* shanchoyzone@gmail.com
🐛 *Issues:* Report bugs via telegarm or email

*Common Issues:*
• News not loading: Check your internet connection
• Wrong timezone: Use `/timezone` to set correct zone
• Missing features: Many features are still in development

*Bot Status:* Active development
*Version:* v2.0.0

Thank you for using ChoyNewsBot! 🚀
    """
    
    send_telegram(support_message, chat_id)
    logger.info(f"Sent support info to chat {chat_id}")

def handle_about_command(chat_id):
    """Handle the /about command."""
    from api.telegram import send_telegram
    import json
    import os
    
    try:
        # Load bot information from memory.json
        memory_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "memory.json")
        
        with open(memory_file, 'r', encoding='utf-8') as f:
            bot_data = json.load(f)
        
        bot_info = bot_data["bot_info"]
        
        # Build the about message
        about_message = f"""
🤖 *{bot_info["name"]}*
_{bot_info["tagline"]}_

{bot_info["description"]}

*🏷️ Version:* {bot_info["version"]}
*🛠️ Built with:* {", ".join(bot_info["technologies"])}

{bot_info["what_makes_special"]["title"]}

"""
        
        # Add special features
        for feature in bot_info["what_makes_special"]["features"]:
            about_message += f"• {feature}\n"
        
        about_message += f"\n{bot_info['core_features']['title']}\n\n"
        
        # Add core feature sections
        for section in bot_info["core_features"]["sections"]:
            about_message += f"*{section['title']}*\n"
            about_message += f"{section['description']}\n\n"
            
            for feature in section["features"]:
                about_message += f"{feature}\n"
            about_message += "\n"
        
        # Add statistics
        stats = bot_info["statistics"]
        about_message += f"""
*📊 Key Statistics:*
• News Sources: {stats["news_sources"]} premium outlets
• Update Frequency: {stats["update_frequency"]}
• Daily Digests: {stats["daily_digests"]} scheduled times
• Timezone Support: {stats["supported_timezones"]} worldwide
• Crypto Coverage: {stats["crypto_coins_supported"]} cryptocurrencies

*👨‍💻 Developer:*
{bot_info["developer"]["name"]}
📱 Telegram: {bot_info["developer"]["contact"]["telegram"]}
📧 Email: {bot_info["developer"]["contact"]["email"]}
🔗 GitHub: {bot_info["developer"]["contact"]["github"]}

*🚀 Ready to get started?*
Type /help to see all available commands!
        """
        
        send_telegram(about_message, chat_id)
        logger.info(f"Sent about info to chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error loading about info: {e}")
        # Fallback message
        fallback_message = """
🤖 *ChoyNewsBot*
_AI-Powered Breaking News & Crypto Intelligence_

I'm an advanced Telegram news bot that provides:
• 📰 Real-time breaking news from 50+ sources
• 🤖 AI-powered crypto analysis with DeepSeek
• 🌤️ Live weather and market data
• ⏰ Smart scheduling with zero duplicate news

Type /help to explore all my features!

*Developer:* Shanchoy Noor
*Contact:* @shanchoynoor
        """
        send_telegram(fallback_message, chat_id)

def handle_category_news_command(chat_id, user_id, category):
    """Handle category-specific news commands (/local, /global, /tech, /sports, /finance) with [Details] inline buttons."""
    from api.telegram import send_telegram
    from core.news_fetcher import get_category_news
    try:
        # Send loading message
        category_names = {
            'local': 'local Bangladesh',
            'global': 'global',
            'tech': 'technology',
            'sports': 'sports',
            'finance': 'finance'
        }
        category_name = category_names.get(category, category)
        send_telegram(f"📰 Loading {category_name} news...", chat_id)
        # Get category news and news_items for [Details]
        news_message, news_items = get_category_news(category, limit=10)
        # Build inline keyboard with [Details] button for each news item
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        for item in news_items:
            # Store news item in global store for callback lookup
            news_item_store[item['id']] = item
            keyboard.append([InlineKeyboardButton("[Details]", callback_data=f"details_{item['id']}")])
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        from api.telegram import send_telegram_with_markup
        if reply_markup:
            send_telegram_with_markup(news_message, chat_id, reply_markup)
        else:
            send_telegram(news_message, chat_id)
        logger.info(f"Sent {category} news to user {user_id}")
    except Exception as e:
        logger.error(f"Error getting {category} news for user {user_id}: {e}")
        send_telegram(
            f"Sorry, I encountered an error while fetching {category} news. Please try again later.",
            chat_id
        )
