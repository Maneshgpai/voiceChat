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

## Set up logging for debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())
ist = timezone(timedelta(hours=5, minutes=30))
db = firestore.Client.from_service_account_json("firestore_key.json")

TOKEN = os.getenv("BOT_TELEGRAM_API_KEY")
char_id = os.getenv("BOT_CHAR_ID")
bot_webhook_url = os.getenv("BOT_WEBHOOK_URL")

## Initialize TG bot
bot = telegram.Bot(token=TOKEN)

## Initialize Flask app
app = Flask(__name__)

def get_audio_file_location(response_type,tg_voice_id, db_document_name):
    timestamp = datetime.now(ist).strftime('%Y%m%d%I%M%S%p')
    full_directory_path = "voice_messages/"+db_document_name
    if not os.path.exists(full_directory_path):
        os.makedirs(full_directory_path)
    filename = full_directory_path + "/"+response_type+"_"+db_document_name+"_"+timestamp+"_"+tg_voice_id+".ogg"
    return filename

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
        text_response = textresponse.get_agent_response(query, character_settings, message_hist)
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("************** get_agent_response > error:",error)
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

## Define the handler for receiving voice messages
def handle_voice(update: Update, context: CallbackContext) -> None:
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT STARTED....")

    user_id = str(update.message.from_user.id)
    db_document_name = user_id+'_'+char_id
    voice_file = update.message.voice
    
    ## Creating new / Updating existing user info in DB ##
    set_tg_user_data(db_document_name,user_id, update, db)

    ## Fetching chat history ##
    message_hist = get_tg_chat_history(db_document_name, db)

    ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db)

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
        log_response = {"status": "Chat API/TG Bot/handle_voice > Error while converting voice to text","status_cd":400, "message": response_status, "user_file_name":user_file_name, "assistant_file_name":assistant_file_name, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
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
        log_response = {"status": "Chat API/TG Bot/handle_voice > Error while sending the Audio on TG","status_cd":400, "message": response_status, "user_file_name":user_file_name, "assistant_file_name":assistant_file_name, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
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
        log_response = {"status": "Chat API/TG Bot/handle_voice > Error while replying the Text on TG","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

## Define the message handler for user queries
def handle_message(update: Update, context: CallbackContext) -> None:
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT STARTED....")
    text_response = "Thank you, aapke msg ke liye. Thoda sa sabr karo, I will be back soon!"

    ## Get character as per the token
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

## Error handler for network and other common errors
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

## Set webhook URL
@app.route('/{}'.format(TOKEN), methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Define a handler for the /start command
# def start(update, context):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="Hi!")

# Main function to start the bot
def main() -> None:
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.voice, handle_voice))
    dp.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()

## Create a dispatcher
dispatcher = Dispatcher(bot, None, workers=8, use_context=True)
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_handler(MessageHandler(Filters.voice, handle_voice))
dispatcher.add_error_handler(error_handler)
## dispatcher.add_handler(CommandHandler("start", start))
## dispatcher.add_handler(CommandHandler("menu", menu))
## dispatcher.add_handler(CallbackQueryHandler(button))

# Set webhook
bot.set_webhook(url=bot_webhook_url+'/{}'.format(TOKEN))

if __name__ == '__main__':
    # main()
    app.run(host='0.0.0.0', port=5000, debug=False)