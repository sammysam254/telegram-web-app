import json
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, jsonify
import threading

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token (using environment variable for security)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8125885886:AAGcoIuTJ0hA7ASMYckc86STF3xruOCfygE")

# Flask app for health check
app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "escrowflow-bot"})

# Your web app URL (using the registered short_name)
WEB_APP_URL = "https://t.me/Escrowflow_bot/Escrowflow"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with a button that opens the web app."""
    user = update.effective_user
    
    # Create web app button
    keyboard = [
        [InlineKeyboardButton("🔒 Open Escrowflow", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🔒 *Welcome to Escrowflow!*

Hello {user.first_name}! 👋

Escrowflow is your secure escrow service for safe transactions. Our platform provides:

✅ Secure escrow services
✅ Real-time transaction tracking  
✅ Multi-currency support
✅ Dispute resolution
✅ 24/7 customer support

Click the button below to open the Escrowflow app and start your secure transactions!
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help information."""
    help_text = """
🔒 *Escrowflow Help*

*Available Commands:*
/start - Start the bot and open web app
/help - Show this help message
/support - Contact support

*How to use:*
1. Click "Open Escrowflow" to launch the web app
2. Create a new escrow transaction
3. Invite your counterparty
4. Complete the secure transaction

*Features:*
• Secure escrow holding
• Multi-currency support
• Real-time notifications
• Dispute resolution
• Transaction history

For support, contact @your_support_username
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send support information."""
    support_text = """
🆘 *Escrowflow Support*

Need help? We're here for you!

*Contact Options:*
• Email: support@escrowflow.com
• Telegram: @escrowflow_support
• Live Chat: Available in the web app

*Business Hours:*
Monday - Friday: 9 AM - 6 PM UTC
Saturday - Sunday: 10 AM - 4 PM UTC

*Emergency Support:*
For urgent issues, use the emergency contact in the web app.
    """
    
    await update.message.reply_text(support_text, parse_mode='Markdown')

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle data sent from the web app."""
    try:
        # Parse the web app data
        web_app_data = json.loads(update.effective_message.web_app_data.data)
        action = web_app_data.get('action')
        data = web_app_data.get('data')
        
        user = update.effective_user
        
        if action == 'create_escrow':
            # Handle escrow creation
            escrow_info = f"""
🔒 *Escrow Created Successfully!*

*Transaction Details:*
• Title: {data.get('title')}
• Amount: {data.get('amount')} {data.get('currency')}
• Counterparty: {data.get('counterparty')}
• Description: {data.get('description', 'No description')}
• Creator: {user.first_name} ({user.id})

*Next Steps:*
1. Share this escrow with your counterparty
2. Wait for them to accept the terms
3. Complete the transaction securely

*Transaction ID:* ESC-{user.id}-{hash(str(data))%10000:04d}
            """
            
            await update.effective_message.reply_text(
                escrow_info,
                parse_mode='Markdown'
            )
            
        # You can add more actions here as needed
        
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")
        await update.effective_message.reply_text(
            "❌ Error processing your request. Please try again."
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "support":
        await support_command(update, context)

def run_flask():
    """Run Flask app for health checks"""
    port = int(os.environ.get('PORT', 10000))
    from gunicorn.app.wsgiapp import WSGIApplication
    
    class StandaloneApplication(WSGIApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()
        
        def load_config(self):
            config = {key: value for key, value in self.options.items()
                     if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)
        
        def load(self):
            return self.application
    
    options = {
        'bind': f'0.0.0.0:{port}',
        'workers': 1,
        'timeout': 120,
    }
    
    StandaloneApplication(app, options).run()

def main() -> None:
    """Start the bot."""
    try:
        # Start Flask app in a separate thread for health checks
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("support", support_command))
        application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
        
        # Add callback query handler
        from telegram.ext import CallbackQueryHandler
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Run the bot
        print("🚀 Escrowflow bot is starting...")
        logger.info("Bot started successfully")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()