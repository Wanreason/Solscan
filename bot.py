import os
import requests
import telegram
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tinydb import TinyDB, Query
from flask import Flask, request
from cleanup import cleanup_db
from utils import get_trending_memecoins, filter_scams
from settings import save_setting, get_setting

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Flask app for webhook endpoint
app = Flask(__name__)

# Initialize TinyDB
db = TinyDB('settings.json')
UserSettings = Query()

# Telegram bot setup
application = Application.builder().token(TOKEN).build()

# Settings Menu
async def settings_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("🔔 Set Alert Frequency", callback_data="set_frequency")],
        [InlineKeyboardButton("📈 Set Price Filter", callback_data="set_price_filter")],
        [InlineKeyboardButton("🔍 Enable Rug-Pull Detection", callback_data="enable_rug_detection")],
        [InlineKeyboardButton("⚙️ Select APIs", callback_data="select_api")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Configure Your Alerts:", reply_markup=reply_markup)

# Cleanup database periodically
cleanup_db(db)

# Command: Show safe trending memecoins
async def send_alert(update, context):
    try:
        memecoins = get_trending_memecoins()
        safe_coins = filter_scams(memecoins)
        message = "\n".join([f"{coin['name']} - {coin['price']}" for coin in safe_coins])
        await update.message.reply_text(f"🔥 Trending Memecoins:\n{message}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching memecoins: {str(e)}")

# Command: Set alert frequency
async def set_frequency(update, context):
    try:
        frequency = int(context.args[0])
        user_id = update.message.chat_id
        save_setting(user_id, "alert_frequency", frequency)
        await update.message.reply_text(f"✅ Alerts set every {frequency} minutes.")
    except:
        await update.message.reply_text("❌ Invalid input! Usage: `/set_frequency <minutes>`")

# Command: Set price filter
async def set_price(update, context):
    try:
        price = float(context.args[0])
        user_id = update.message.chat_id
        save_setting(user_id, "price_filter", price)
        await update.message.reply_text(f"✅ Memecoins filtered above ${price}.")
    except:
        await update.message.reply_text("❌ Invalid input! Usage: `/set_price <amount>`")

# Command: Choose API
async def set_api(update, context):
    if context.args[0] in ["openocean", "bitquery", "mcp"]:
        user_id = update.message.chat_id
        save_setting(user_id, "api_priority", context.args[0])
        await update.message.reply_text(f"✅ API switched to {context.args[0].capitalize()}.")
    else:
        await update.message.reply_text("❌ Invalid choice! Available APIs: `openocean`, `bitquery`, `mcp`")

# Add command handlers
application.add_handler(CommandHandler("settings", settings_menu))
application.add_handler(CommandHandler("set_frequency", set_frequency))
application.add_handler(CommandHandler("set_price", set_price))
application.add_handler(CommandHandler("set_api", set_api))
application.add_handler(CommandHandler("alerts", send_alert))

# Webhook route for Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

# Set webhook once when app starts
@app.before_first_request
def init_webhook():
    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://solscan-4y5w.onrender.com")
    webhook_url = f"{base_url}/{TOKEN}"
    try:
        application.bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set: {webhook_url}")
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}")

# Run the Flask app if run directly (not required with gunicorn, but safe fallback)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
