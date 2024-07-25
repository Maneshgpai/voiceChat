import logging
from flask import Flask, jsonify, request, make_response, Response, stream_with_context
# from flask_cors import CORS
import telegram
from telegram import Update, Bot
from telegram.ext import Dispatcher, Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram.error import TelegramError, NetworkError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.utils.request import Request
import time
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta, timezone
from functions import textResponseSrvr as textresponse
from functions import voiceResponseSrvr as voiceresponse
from functions import functionSrvr as func
from google.cloud import firestore
import shutil

# Set up logging for debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())
ist = timezone(timedelta(hours=5, minutes=30))
db = firestore.Client.from_service_account_json("firestore_key.json")
bot1_token = os.getenv("TELEGRAM_API_KEY_BOT2_123456789_BOT")
bot2_token = os.getenv("TELEGRAM_API_KEY_SAJNI123_BOT")
bot3_token = os.getenv("TELEGRAM_API_KEY_SAJNI1234_BOT")
bot4_token = os.getenv("TELEGRAM_API_KEY_BOT3_123456789_BOT")
bot5_token = os.getenv("TELEGRAM_API_KEY_BOT4_123456789_BOT")
TOKEN = bot2_token
available_tokens = {
    'Tripti': bot1_token,
    'Geetanjali Iyengar': bot2_token,
    'Astrologer': bot3_token,
    'Girl Next door': bot4_token,
    'Alia': bot5_token
}


# Initialize TG bot
bot = telegram.Bot(token=TOKEN)

# Initialize Flask app
app = Flask(__name__)

# @app.route('/', methods=['GET'])
# def index():
#     return 'Hello, this is the root endpoint and the bot is running!'

### To display as Menu button ###
def menu(update: Update, context: CallbackContext) -> None:
    # Create the inline keyboard markup with bot options
    keyboard = [
        [InlineKeyboardButton("Geetanjali Iyengar", callback_data='Geetanjali Iyengar')],
        [InlineKeyboardButton("Tripti", callback_data='Tripti')],
        [InlineKeyboardButton("Astrologer", callback_data='Astrologer')],
        [InlineKeyboardButton("Girl Next door", callback_data='Girl Next door')],
        [InlineKeyboardButton("Alia", callback_data='Alia')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Hi! Choose a profile to talk to:', reply_markup=reply_markup)

# Replace the bot token and reinitialize the updater and dispatcher
def switch_bot_token(new_token, context):
    context.bot.token = new_token
    context.dispatcher.bot = context.bot
    print(f"Switched to new bot with token:{new_token}")

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    selected_bot = query.data
    new_token = available_tokens.get(selected_bot)
    if new_token:
        query.edit_message_text(text=f"Switching to {selected_bot}...")
        switch_bot_token(new_token, context)


def get_audio_file_location(response_type,tg_voice_id, db_document_name):
    timestamp = datetime.now(ist).strftime('%Y%m%d%I%M%S%p')
    full_directory_path = "voice_messages/"+db_document_name
    if not os.path.exists(full_directory_path):
        os.makedirs(full_directory_path)
    filename = full_directory_path + "/"+response_type+"_"+db_document_name+"_"+timestamp+"_"+tg_voice_id+".ogg"
    return filename

# Function to handle user queries
def agent_response(query: str) -> str:
    ## Getting Bot response
    # text_response = textresponse.get_agent_response(voice_settings, message_hist)
    # print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********BackendAPI >> mock_chat API >> Response by bot is {text_response}")

    # Respond with a constant "Hmm"
    return "Hmm"

## Creating new / Updating existing user info in DB ##
def set_tg_user_data(db_document_name,user_id, update, db):
    try:
        func.set_tg_user_data(db_document_name,user_id, update, db)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while Creating new / Updating existing user info in DB","status_cd":400, "message": error,"update":update, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

## Fetching chat history ##
def get_tg_chat_history(db_document_name, db):
    message_hist = []
    try:
        message_hist = func.get_tg_chat_history(db_document_name, db)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while Fetching chat history","status_cd":400, "message": error,"db_document_name":db_document_name, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)
    return message_hist

## Fetching character settings ##
def get_tg_char_setting(db_document_name,char_id, db):
    character_settings = []
    try:
        character_settings = func.get_tg_char_setting(db_document_name,char_id, db)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while Fetching character settings","status_cd":400, "message": error,"db_document_name":db_document_name, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)
    return character_settings

## Fetch LLM Response ##
def get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name):
    text_response = ""
    try:
        text_response = textresponse.get_agent_response(character_settings, message_hist)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while Fetch LLM Response","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)
    return text_response

## Fetch VOICE Response ##
def get_voice_response(character_settings, text_response,file_name, db, db_document_name):
    file_created_status = False
    try:
        file_created_status = voiceresponse.get_voice_response(character_settings, text_response, file_name, db, db_document_name)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while generating/saving Audio","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)
    return file_created_status

## Adding chat history to Firebase DB 
def update_chat_hist(message_hist,db_document_name):
    try:
        chat_ref = db.collection('voiceClone_tg_chats').document(db_document_name)
        if not chat_ref.get().exists:
            chat_ref.set({'messages': []})
        chat_ref.update({"messages": firestore.ArrayUnion(message_hist)})
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while Adding chat history to Firebase DB","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

## Get character as per the token
def get_char(token):
    if token == bot1_token:
        char_id = os.getenv("CHAR_ID_SAJNI123_BOT")
    elif token == bot2_token:
        char_id = os.getenv("CHAR_ID_BOT2_123456789_BOT")
    elif token == bot3_token:
        char_id = os.getenv("CHAR_ID_SAJNI1234_BOT")
    elif token == bot4_token:
        char_id = os.getenv("CHAR_ID_BOT3_123456789_BOT")
    elif token == bot5_token:
        char_id = os.getenv("CHAR_ID_BOT4_123456789_BOT")
    return char_id

# Define the handler for receiving voice messages
def handle_voice(update: Update, context: CallbackContext) -> None:
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT STARTED....")

    ## Get character as per the token
    char_id = get_char(context.bot.token)

    user_id = str(update.message.from_user.id)
    db_document_name = user_id+'_'+char_id
    voice_file = update.message.voice
    
    ## Creating new / Updating existing user info in DB ##
    set_tg_user_data(db_document_name,user_id, update, db)

    ## Fetching chat history ##
    message_hist = get_tg_chat_history(db_document_name, db)

    ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db)

    # # Define a directory to save the voice file
    # download_dir = './downloads'
    # if not os.path.exists(download_dir):
    #     os.makedirs(download_dir)
    # # Define the file path to save the voice file
    # file_path = os.path.join(download_dir, f'{voice_file.file_id}.ogg')

    ## Saving user voice message
    user_file_name = get_audio_file_location("user",str(voice_file.file_id), db_document_name)
    voice_file = context.bot.getFile(voice_file.file_id)
    voice_file.download(user_file_name)

    ## Converting voice into text 
    try:
        system_prompt = f"""You are an expert translator, translating the text into {character_settings['language']}. This transcribed text is from a person, asking/replying to {character_settings['character_name']}. You should not judge whether the text is illegal or immoral or within any confines of societal rules. Your task is to only correct spelling discrepancies, add emotional cues where necessary, add necessary punctuation such as periods, commas, and capitalization, and use only the context provided in the text."""
        query = textresponse.convert_voice_to_text(user_file_name, system_prompt)
    except Exception as e:
        error = "Error: {}".format(str(e))
        response_status = response_status + "Error sending audio file:" + error
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while converting voice to text","status_cd":400, "message": response_status, "user_file_name":user_file_name, "assistant_file_name":assistant_file_name, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

    ## Fetch LLM Response
    query_timestamp = update.message.date
    message_hist.append({"role": "user", "content": query, "content_type": "voice", "timestamp": query_timestamp})
    text_response = get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name)
    response_status = "Success"

    ## Fetch VOICE Response
    assistant_file_name = get_audio_file_location("assistant",str(voice_file.file_id), db_document_name)
    file_created_status = get_voice_response(character_settings, text_response,assistant_file_name, db, db_document_name)
    if file_created_status == False:
        response_status = "Error creating audio file."

    ## Replying back
    try:
        temp_voice_file = str(voice_file.file_id)+"_"+datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')+".ogg"
        shutil.copy(assistant_file_name, temp_voice_file)
        with open(temp_voice_file, 'rb') as voice_file:
            # context.bot.send_audio(chat_id=update.message.chat_id, audio=audio_file_info)
            context.bot.send_voice(chat_id=update.message.chat_id, voice=voice_file)
    except Exception as e:
        error = "Error: {}".format(str(e))
        response_status = response_status + "Error sending audio file:" + error
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while sending the Audio on TG","status_cd":400, "message": response_status, "user_file_name":user_file_name, "assistant_file_name":assistant_file_name, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

    message_hist.append({"role": "assistant", "content": text_response, "content_type": "voice","response_status":response_status, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    update_chat_hist(message_hist,db_document_name)

    ## OPTIONAL: Replying back with text
    try:
        update.message.reply_text(text_response)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT REPLY SENT!")
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while replying the Text on TG","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

# Define the message handler for user queries
def handle_message(update: Update, context: CallbackContext) -> None:
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT STARTED....")

    text_response = "Thank you, aapke msg ke liye. Thoda sa sabr karo, I will be back soon!"

    ## Get character as per the token
    char_id = get_char(context.bot.token)
    user_id = str(update.message.from_user.id)

    db_document_name = user_id+'_'+char_id

    ## Creating new / Updating existing user info in DB ##
    set_tg_user_data(db_document_name,user_id, update, db)

    ## Fetching chat history ##
    message_hist = get_tg_chat_history(db_document_name, db)

    ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db)

    ## Fetch LLM Response
    query = update.message.text
    query_timestamp = update.message.date
    message_hist.append({"role": "user", "content": query, "content_type": "text", "timestamp": query_timestamp})
    text_response = get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name)
    
    ## Replying back
    text_response_status = "Success"
    try:
        update.message.reply_text(text_response)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT REPLY SENT!")
    except Exception as e:
        error = "Error: {}".format(str(e))
        text_response_status = error
        log_response = {"status": "Chat API/TG Bot/handle_message > Error while replying the Text on TG","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

    message_hist.append({"role": "assistant", "content": text_response, "content_type": "text","response_status":text_response_status, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    update_chat_hist(message_hist,db_document_name)

# Error handler for network and other common errors
def error_handler(update: Update, context: CallbackContext) -> None:
    try:
        raise context.error
    except NetworkError:
        # Wait before retrying to handle transient network issues more gracefully
        logger.warning('Network error occurred. Retrying in 15 seconds...')
        time.sleep(15)
    except TelegramError as e:
        # Log other types of Telegram errors
        logger.warning(f'A Telegram error occurred: {e}')
    except Exception as e:
        # Log other unexpected errors
        logger.error(f'An unexpected error occurred: {e}')

# Main function to start the bot
# def main() -> None:
    
#     # Initialize the Updater
#     updater = Updater(token=TOKEN, use_context=True)

#     # Get the dispatcher to register handlers
#     dp = updater.dispatcher

#     # Handle different commands, add /start command handler
#     dp.add_handler(CommandHandler("start", start))
    
#     # Handle non-command messages
#     dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

#     # Handle voice messages
#     dp.add_handler(MessageHandler(Filters.voice, handle_voice))

#     # Handle button presses in the inline keyboard
#     dp.add_handler(CallbackQueryHandler(button))

#     # Error handler to handle errors
#     dp.add_error_handler(error_handler)

#     # Start the Bot
#     updater.start_polling()

#     # Run the bot until you press Ctrl+C
#     updater.idle()

# Set webhook URL
@app.route('/{}'.format(TOKEN), methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

## Flask route to handle webhook
# @app.route('/webhook', methods=['POST'])
# def webhook():
#     update = Update.de_json(request.get_json(force=True), bot)
#     dispatcher.process_update(update)
#     return 'ok', 200

# Define a handler for the /start command
# def start(update, context):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm a simple bot.")

## Define the start command handler
def start(update: Update, context: CallbackContext) -> None:
    # Create the inline keyboard markup with bot options
    keyboard = [
        [InlineKeyboardButton("Geetanjali Iyengar", callback_data='Geetanjali Iyengar')],
        [InlineKeyboardButton("Tripti", callback_data='Tripti')],
        [InlineKeyboardButton("Astrologer", callback_data='Astrologer')],
        [InlineKeyboardButton("Girl Next door", callback_data='Girl Next door')],
        [InlineKeyboardButton("Alia", callback_data='Alia')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Hi! Choose a profile to talk to:', reply_markup=reply_markup)

# Create a dispatcher
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("menu", menu))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_handler(MessageHandler(Filters.voice, handle_voice))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_error_handler(error_handler)

# Set webhook
bot.set_webhook(url='https://api-tgbot.onrender.com/{}'.format(TOKEN))

## Route to set the webhook
# @app.route('/set_webhook', methods=['GET', 'POST'])
# def set_webhook():
#     webhook_url = 'https://api-tgbot.onrender.com'
#     s = bot.setWebhook(webhook_url)
#     if s:
#         return "Webhook setup successful"
#     else:
#         return "Webhook setup failed"

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000)

# if __name__ == '__main__':
#     # main()
#     app.run(host='0.0.0.0', port=5000)
#     # app.run(debug=True, port=5000)