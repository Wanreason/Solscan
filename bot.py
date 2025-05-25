import os
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from tinydb import TinyDB, Query
from cleanup import cleanup_db
from utils import get_trending_memecoins, filter_scams
from settings import save_setting

# Load Telegram token and initialize app
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-render-url.onrender.com

# Setup Telegram application
application = Application.builder().token(TOKEN).build()

# Initialize TinyDB
db = TinyDB('settings.json')
UserSettings = Query()

# Run DB cleanup
cleanup_db(db)

# Flask server
flask_app = Flask(__name__)

# ===========================
# Command Handlers
# ===========================

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔔 Set Alert Frequency", callback_data="set_frequency")],
        [InlineKeyboardButton("📈 Set Price Filter", callback_data="set_price_filter")],
        [InlineKeyboardButton("🔍 Enable Rug-Pull Detection", callback_data="enable_rug_detection")],
        [InlineKeyboardButton("⚙️ Select APIs", callback_data="select_api")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Configure Your Alerts:", reply_markup=reply_markup)

async def send_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        memecoins = get_trending_memecoins()
        safe_coins = filter_scams(memecoins)
        message = "\n".join([f"{coin['name']} - {coin['price']}" for coin in safe_coins])
        await update.message.reply_text(f"🔥 Trending Memecoins:\n{message}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching memecoins: {str(e)}")

async def set_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        frequency = int(context.args[0])
        user_id = update.message.chat_id
        save_setting(user_id, "alert_frequency", frequency)
        await update.message.reply_text(f"✅ Alerts set every {frequency} minutes.")
    except:
        await update.message.reply_text("❌ Invalid input! Usage: `/set_frequency <minutes>`")

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(context.args[0])
        user_id = update.message.chat_id
        save_setting(user_id, "price_filter", price)
        await update.message.reply_text(f"✅ Memecoins filtered above ${price}.")
    except:
        await update.message.reply_text("❌ Invalid input! Usage: `/set_price <amount>`")

async def set_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args[0] in ["openocean", "bitquery", "mcp"]:
        user_id = update.message.chat_id
        save_setting(user_id, "api_priority", context.args[0])
        await update.message.reply_text(f"✅ API switched to {context.args[0].capitalize()}.")
    else:
        await update.message.reply_text("❌ Invalid choice! Available APIs: `openocean`, `bitquery`, `mcp`")

# ===========================
# Register Commands
# ===========================

application.add_handler(CommandHandler("settings", settings_menu))
application.add_handler(CommandHandler("set_frequency", set_frequency))
application.add_handler(CommandHandler("set_price", set_price))
application.add_handler(CommandHandler("set_api", set_api))
application.add_handler(CommandHandler("alerts", send_alert))

# ===========================
# Flask Webhook Route
# ===========================

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook() -> str:
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK"

@flask_app.route("/", methods=["GET"])
def home():
    return "🚀 Telegram bot is live!"

# ===========================
# Run App and Set Webhook
# ===========================

if __name__ == "__main__":
    import asyncio
    async def run():
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
        print(f"✅ Webhook set: {WEBHOOK_URL}/{TOKEN}")
        application.run_polling()  # Optional fallback

    asyncio.run(run())
    flask_app.run(host="0.0.0.0", port=10000)
