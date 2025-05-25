import os
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from tinydb import TinyDB, Query
from cleanup import cleanup_db
from utils import get_trending_memecoins, filter_scams
from settings import save_setting

# Load tokens
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-bot-name.onrender.com

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
    welcome_text = (
        "👋 Welcome to the Memecoin Tracker Bot!\n\n"
        "Use /alerts to see trending memecoins.\n"
        "Use /hot to see currently hot memecoins 🔥.\n"
        "Use /settings to configure your alert preferences."
    )
    await update.message.reply_text(welcome_text)

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
        message = "\n".join([f"{coin['name']} - ${coin['price']}" for coin in safe_coins])
        await update.message.reply_text(f"📢 Trending Memecoins:\n{message}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching memecoins: {str(e)}")

async def hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        memecoins = get_trending_memecoins()
        safe_coins = filter_scams(memecoins)
        message = "\n".join([f"{coin['name']} - ${coin['price']}" for coin in safe_coins])
        if not message:
            message = "No hot memecoins found right now."
        await update.message.reply_text(f"🔥 Hot & Trending Memecoins:\n{message}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching hot memecoins: {str(e)}")

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

# Optional: Button handler for settings (placeholder — expand later)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"You selected: {query.data} (Coming soon!)")

# ========== REGISTER HANDLERS ==========

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("settings", settings_menu))
application.add_handler(CommandHandler("alerts", send_alert))
application.add_handler(CommandHandler("hot", hot))
application.add_handler(CommandHandler("set_frequency", set_frequency))
application.add_handler(CommandHandler("set_price", set_price))
application.add_handler(CommandHandler("set_api", set_api))
application.add_handler(CallbackQueryHandler(button_handler))  # for button presses

# ========== FLASK WEBHOOK ROUTES ==========

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook() -> str:
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK"

@flask_app.route("/", methods=["GET"])
def home():
    return "🚀 Telegram bot is live!"

# ========== STARTUP ==========

if __name__ == "__main__":
    import asyncio
    asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}"))
    print(f"✅ Webhook set: {WEBHOOK_URL}/{TOKEN}")
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
