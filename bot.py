import os
import requests
import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tinydb import TinyDB, Query
from cleanup import cleanup_db
from utils import get_trending_memecoins, filter_scams

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TOKEN)

# Initialize TinyDB
db = TinyDB('settings.json')
UserSettings = Query()

# Function to save user settings
def save_setting(user_id, key, value):
    db.upsert({'user_id': user_id, key: value, 'timestamp': os.time()}, UserSettings.user_id == user_id)

# Function to retrieve user settings
def get_setting(user_id, key, default=None):
    result = db.get(UserSettings.user_id == user_id)
    return result[key] if result and key in result else default

# Settings Menu Function
def settings_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("🔔 Set Alert Frequency", callback_data="set_frequency")],
        [InlineKeyboardButton("📈 Set Price Filter", callback_data="set_price_filter")],
        [InlineKeyboardButton("🔍 Enable Rug-Pull Detection", callback_data="enable_rug_detection")],
        [InlineKeyboardButton("⚙️ Select APIs", callback_data="select_api")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("⚙️ Configure Your Alerts:", reply_markup=reply_markup)

# Cleanup database periodically
cleanup_db(db)

# Telegram command to send alerts
def send_alert(update, context):
    try:
        memecoins = get_trending_memecoins()
        safe_coins = filter_scams(memecoins)
        message = "\n".join([f"{coin['name']} - {coin['price']}" for coin in safe_coins])
        update.message.reply_text(f"🔥 Trending Memecoins:\n{message}")
    except Exception as e:
        update.message.reply_text(f"❌ Error fetching memecoins: {str(e)}")

# Bot Command Handlers
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("settings", settings_menu))
dp.add_handler(CommandHandler("set_frequency", set_frequency))
dp.add_handler(CommandHandler("set_price", set_price))
dp.add_handler(CommandHandler("set_api", set_api))
dp.add_handler(CommandHandler("alerts", send_alert))

updater.start_polling()
updater.idle()
