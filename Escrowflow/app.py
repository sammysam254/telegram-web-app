import sys
if sys.version_info >= (3, 12):
    raise RuntimeError("Python 3.12+ not supported. Use Python 3.11")import os
import hashlib
import hmac
from flask import Flask, request, jsonify, render_template
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Flask app initialization (must be named 'app')
app = Flask(__name__)
app.secret_key = os.urandom(24)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBAPP_URL = 'https://t.me/Escrowflow_bot/Escrowflow'

# Telegram bot setup
async def setup_bot():
    bot = Application.builder().token(BOT_TOKEN).build()
    
    async def start(update: Update, context: CallbackContext):
        await update.message.reply_text(
            "🚀 Welcome to Escrowflow!",
            reply_markup={
                "inline_keyboard": [[{
                    "text": "Open Dashboard", 
                    "web_app": {"url": WEBAPP_URL}
                }]]
            }
        )
    
    bot.add_handler(CommandHandler("start", start))
    return bot

# Web routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webapp')
def webapp():
    return render_template('webapp.html')

# API endpoints
@app.route('/api/auth', methods=['POST'])
def auth():
    if verify_telegram_data(request.form.get('initData')):
        return jsonify({"status": "success"})
    return jsonify({"status": "unauthorized"}), 403

def verify_telegram_data(data: str) -> bool:
    try:
        params = dict(pair.split('=') for pair in data.split('&'))
        hash_str = '\n'.join(f"{k}={v}" for k,v in sorted(params.items()) if k != 'hash')
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        return hmac.new(secret, hash_str.encode(), hashlib.sha256).hexdigest() == params['hash']
    except:
        return False

# Gunicorn compatibility
application = app  # Critical for Render deployment

if __name__ == '__main__':
    import asyncio
    asyncio.run(setup_bot())
    application.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
