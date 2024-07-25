import os
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, CommandHandler

# Replace with your actual bot token
BOT_TOKEN = os.getenv("TELEGRAM_API_KEY_SAJNI123_BOT")
bot = telegram.Bot(token=BOT_TOKEN)

app = Flask(__name__)

# Set webhook URL
@app.route('/{}'.format(BOT_TOKEN), methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Define a handler for the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm a simple bot.")

# Create a dispatcher
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))

# Set webhook
bot.set_webhook(url='https://api-tgbot.onrender.com/{}'.format(BOT_TOKEN))

if __name__ == '__main__':
    app.run(debug=True)