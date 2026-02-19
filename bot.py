import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
PORT = int(os.getenv('PORT', 10000))

def call_deepseek(user_message):
    """Call DeepSeek API and return the response."""
    url = "https://api.deepseek.com/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Error calling DeepSeek: {e}")
        return f"Error: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages."""
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Call DeepSeek API
    ai_response = call_deepseek(user_message)
    
    # Send response back to user
    await update.message.reply_text(ai_response)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def run_http_server():
    """Run a simple HTTP server for Render health checks."""
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    logger.info(f"HTTP server running on port {PORT}")
    server.serve_forever()

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN or not DEEPSEEK_API_KEY:
        logger.error("Missing environment variables!")
        return
    
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    logger.info("Starting Telegram bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
