import os
import hashlib
import hmac
from flask import Flask, request, jsonify, render_template
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session security

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBAPP_URL = 'https://t.me/Escrowflow_bot/Escrowflow'

# Initialize bot
async def start_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    async def start(update: Update, context: CallbackContext):
        await update.message.reply_text(
            "🚀 Welcome to Escrowflow! Click below:",
            reply_markup={
                "inline_keyboard": [[{
                    "text": "Open Dashboard",
                    "web_app": {"url": WEBAPP_URL}
                }]]
            }
        )
    
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.initialize()
    return bot_app

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webapp')
def webapp():
    return render_template('webapp.html')

# API Endpoints
@app.route('/api/auth', methods=['POST'])
def auth():
    init_data = request.form.get('initData')
    if verify_telegram_data(init_data):
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 403

def verify_telegram_data(data: str) -> bool:
    try:
        params = dict(pair.split('=') for pair in data.split('&'))
        hash_str = '\n'.join(
            f"{k}={v}" for k, v in sorted(params.items()) 
            if k != 'hash'
        )
        secret_key = hmac.new(
            b"WebAppData", 
            BOT_TOKEN.encode(), 
            hashlib.sha256
        ).digest()
        return hmac.new(
            secret_key, 
            hash_str.encode(), 
            hashlib.sha256
        ).hexdigest() == params['hash']
    except:
        return False

if __name__ == '__main__':
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(start_bot())
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
