import os
import logging
from telegram.ext import Updater, MessageHandler, Filters
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

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

def handle_message(update, context):
    """Handle incoming Telegram messages."""
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")
    
    # Show typing indicator
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Call DeepSeek API
    ai_response = call_deepseek(user_message)
    
    # Send response back to user
    update.message.reply_text(ai_response)

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN or not DEEPSEEK_API_KEY:
        logger.error("Missing environment variables!")
        return
    
    logger.info("Starting Telegram bot...")
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add handler for all text messages
    message_handler = MessageHandler(Filters.text & ~Filters.command, handle_message)
    dispatcher.add_handler(message_handler)
    
    # Start polling
    updater.start_polling()
    logger.info("Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
