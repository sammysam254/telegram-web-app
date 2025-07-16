import os
import hashlib
import hmac
from flask import Flask, request, jsonify, render_template
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

app = Flask(__name__)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8125885886:AAF1Q4MiOHNiTSo2BhjEmnUiQ39yAtGzDYs')
WEBAPP_URL = 'https://t.me/Escrowflow_bot/Escrowflow'

# In-memory database (replace with real database in production)
escrows = {}
users = {}

# Telegram Bot Setup
async def start_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    async def start(update: Update, context: CallbackContext):
        await update.message.reply_text(
            "Welcome to Escrowflow! Click below to access your dashboard:",
            reply_markup={
                "inline_keyboard": [[{
                    "text": "Open Dashboard",
                    "web_app": {"url": WEBAPP_URL}
                }]]
            }
        )
    
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.initialize()
    await bot_app.start()
    return bot_app

# Web App Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webapp')
def webapp():
    return render_template('webapp.html')

# API Endpoints
@app.route('/api/init', methods=['POST'])
def init_escrow():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')
    
    if not user_id or not amount:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400
    
    escrow_id = hashlib.sha256(f"{user_id}{amount}{os.urandom(16)}".encode()).hexdigest()[:16]
    escrows[escrow_id] = {
        'user_id': user_id,
        'amount': amount,
        'status': 'pending',
        'parties': []
    }
    
    return jsonify({
        "status": "success",
        "escrow_id": escrow_id
    })

@app.route('/api/escrow/<escrow_id>', methods=['GET'])
def get_escrow(escrow_id):
    escrow = escrows.get(escrow_id)
    if not escrow:
        return jsonify({"status": "error", "message": "Escrow not found"}), 404
    
    return jsonify({
        "status": "success",
        "escrow": escrow
    })

# Telegram WebApp Verification
def verify_telegram_webapp(data_check_string, telegram_hash):
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return computed_hash == telegram_hash

@app.route('/api/auth', methods=['POST'])
def authenticate():
    init_data = request.form.get('initData')
    if not init_data:
        return jsonify({"status": "error", "message": "No initData provided"}), 400
    
    params = dict(pair.split('=') for pair in init_data.split('&'))
    data_check_string = '\n'.join(
        f"{key}={value}" 
        for key, value in sorted(params.items()) 
        if key != 'hash'
    )
    
    if verify_telegram_webapp(data_check_string, params['hash']):
        user_id = params.get('user', {}).get('id')
        if user_id:
            users[user_id] = params.get('user', {})
            return jsonify({
                "status": "success",
                "user": users[user_id],
                "token": f"tkn_{hashlib.sha256(user_id.encode()).hexdigest()[:32]}"
            })
    
    return jsonify({"status": "error", "message": "Authentication failed"}), 403

if __name__ == '__main__':
    import asyncio
    from threading import Thread
    
    # Start bot in a separate thread
    def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_bot())
    
    Thread(target=run_bot).start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
