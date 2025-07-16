import os
import hashlib
import hmac
from flask import Flask, request, jsonify, render_template
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Version check - Critical for gevent compatibility
import sys
if sys.version_info >= (3, 11):
    raise RuntimeError("Python 3.10 required (current: %s)" % sys.version)

app = Flask(__name__)
app.secret_key = os.urandom(32)  # Strong secret key

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBAPP_URL = 'https://t.me/Escrowflow_bot/Escrowflow'

# Telegram Bot Setup
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
    await bot.initialize()
    return bot

# Web Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webapp')
def webapp():
    return render_template('webapp.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# API Endpoints
@app.route('/api/auth', methods=['POST'])
def auth():
    if verify_telegram_data(request.form.get('initData')):
        return jsonify({"status": "success"})
    return jsonify({"status": "unauthorized"}), 403

def verify_telegram_data(data: str) -> bool:
    try:
        params = dict(pair.split('=') for pair in data.split('&'))
        hash_str = '\n'.join(f"{k}={v}" for k,v in sorted(params.items()) if k != 'hash'
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        return hmac.new(secret, hash_str.encode(), hashlib.sha256).hexdigest() == params['hash']
    except Exception as e:
        app.logger.error(f"Verification failed: {str(e)}")
        return False

# Gunicorn compatibility
application = app

if __name__ == '__main__':
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_bot())
    application.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
