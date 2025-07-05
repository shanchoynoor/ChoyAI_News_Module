import os
<<<<<<< HEAD
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import news
from user_logging import log_user_interaction, init_db
=======
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
>>>>>>> 5295c2b (updated from vps. fixed running issues)

# Load environment variables
load_dotenv()
<<<<<<< HEAD
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
print("Loaded token:", BOT_TOKEN)  # DEBUG: Show which token is loaded

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env file!")

def escape_markdown_v2(text):
    # Use the same escape as in news.py
    import re
    if not text:
        return ""
    escape_chars = r'_\*\[\]()~`>#+=|{}.!-'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_interaction(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        message_type="/news",
        location=None,
        last_interaction=None
    )
    msg = news.main()
    # Escape for MarkdownV2
    msg = escape_markdown_v2(msg)
    if len(msg) > 4096:
        for i in range(0, len(msg), 4096):
            await update.message.reply_text(msg[i:i+4096], parse_mode='MarkdownV2')
    else:
        await update.message.reply_text(msg, parse_mode='MarkdownV2')

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_interaction(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        message_type="/start",
        location=None,
        last_interaction=None
    )
    welcome = (
        "Welcome to the Daily News Digest Bot!\n"
        "Use /news to get the latest news category wise and crypto prices and updates!"
    )
    await update.message.reply_text(welcome)

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("news", news_handler))
    app.add_handler(CommandHandler("start", start_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
=======
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096  # Character limit per message

async def send_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Replace with your news fetching logic
        news_text = "Latest news updates would appear here"
        
        if not news_text:
            await update.message.reply_text("No updates available.")
            return
            
        # Split long messages to avoid truncation
        for i in range(0, len(news_text), TELEGRAM_MESSAGE_LIMIT):
            await update.message.reply_text(news_text[i:i+TELEGRAM_MESSAGE_LIMIT])
            
    except Exception as e:
        logger.error(f"Error in news handler: {e}")
        await update.message.reply_text("⚠️ Error fetching news updates")

def main():
    try:
        logger.info("Starting bot in polling mode...")
        
        # Build application
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add command handler
        app.add_handler(CommandHandler("news", send_news))
        
        # Start polling
        app.run_polling(
            drop_pending_updates=True,  # Skip old updates
            allowed_updates=["message", "callback_query"]  # Only listen to these
        )
        
    except Exception as e:
        logger.critical(f"Bot failed: {e}")
        raise

if __name__ == "__main__":
    main()
>>>>>>> 5295c2b (updated from vps. fixed running issues)
