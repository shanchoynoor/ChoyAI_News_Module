import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import news
from user_logging import log_user_interaction, init_db

load_dotenv()
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