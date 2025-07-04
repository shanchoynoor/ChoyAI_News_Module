from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import news  # assuming your script has functions you can reuse
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = news.main(return_msg=True)  # Modify your `main()` to return string
    if len(msg) > 4096:
        for i in range(0, len(msg), 4096):
            await update.message.reply_text(msg[i:i+4096], parse_mode='MarkdownV2')
    else:
        await update.message.reply_text(msg, parse_mode='MarkdownV2')

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("news", news_handler))

app.run_polling()