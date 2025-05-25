import os
import requests
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from tinydb import TinyDB, Query
from cleanup import cleanup_db
from utils import get_trending_memecoins, filter_scams
from settings import save_setting

# Load tokens
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-bot-name.onrailway.app

# Flask app
flask_app = Flask(__name__)

# Telegram app
application = Application.builder().token(TOKEN).build()

# TinyDB and cleanup
db = TinyDB('settings.json')
UserSettings = Query()
cleanup_db(db)

# ========== COMMAND HANDLERS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 Received /start command")
    welcome_text = (
        "👋 Welcome to the Memecoin Tracker Bot!\n\n"
        "Use /alerts to see trending memecoins.\n"
        "Use /hot to see currently hot memecoins 🔥.\n"
        "Use /settings to configure your alert preferences."
    )
    await update.message.reply_text(welcome_text)

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("⚙️ Received /settings command")
    keyboard = [
        [InlineKeyboardButton("🔔 Set Alert Frequency", callback_data="set_frequency")],
        [InlineKeyboardButton("📈 Set Price Filter", callback_data="set_price_filter")],
        [InlineKeyboardButton("🔍 Enable Rug-Pull Detection", callback_data="enable_rug_detection")],
        [InlineKeyboardButton("⚙️ Select APIs", callback_data="select_api")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Configure Your Alerts:", reply_markup=reply_markup)

async def send_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📢 Received /alerts command")
    try:
        memecoins = get_trending_memecoins()
        safe_coins = filter_scams(memecoins)
        message = "\n".join([f"{coin['name']} - ${coin['price']}" for coin in safe_coins])
        await update.message.reply_text(f"📢 Trending Memecoins:\n{message}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching memecoins: {str(e)}")

# ========== FLASK ROUTES ==========

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook() -> str:
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        application.update_queue.put(update)
        return "OK"
    except Exception as e:
        print(f"❌ Error in webhook: {e}")
        return "Error", 500

@flask_app.route("/", methods=["GET"])
def home():
    return "🚀 Telegram bot is live!"

# ========== STARTUP ==========

if __name__ == "__main__":
    import asyncio

    async def startup():
        try:
            # Initialize bot
            await application.initialize()
            await application.start()

            # Set webhook
            full_url = f"{WEBHOOK_URL}/{TOKEN}"
            await application.bot.set_webhook(url=full_url)
            print(f"✅ Webhook set to: {full_url}")
        except Exception as e:
            print(f"❌ Failed to start bot or set webhook: {e}")

        # Start Flask server
        flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

    asyncio.run(startup())
