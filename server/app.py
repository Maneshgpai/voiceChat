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

def get_datetime():
    return (str(datetime.now())).replace('.','').replace(':','').replace(' ','').replace('-','')

def log(msg_id,status,status_cd,message,origin,db,db_document_name):
    log_response = {str(msg_id)+"_"+get_datetime(): {"status": status,"status_cd":status_cd,"message":message, "origin":origin, "message_id": msg_id, "timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
    func.createLog(log_ref, log_response)

def get_audio_file_location(response_type,tg_voice_id, db_document_name):
    timestamp = datetime.now(ist).strftime('%Y%m%d%I%M%S%p')
    full_directory_path = "voice_messages/"+db_document_name
    if not os.path.exists(full_directory_path):
        os.makedirs(full_directory_path)
    filename = full_directory_path + "/"+response_type+"_"+db_document_name+"_"+timestamp+"_"+tg_voice_id+".ogg"
    return filename

## Creating new / Updating existing user info in DB ##
def set_tg_user_data(db_document_name,user_id, update, db, msg_id):
    try:
        func.set_tg_user_data(db_document_name,user_id, update, db,msg_id)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"set_tg_user_data", "message_id": msg_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

## Fetching chat history ##
def get_tg_chat_history(db_document_name, db, msg_id):
    message_hist = []
    try:
        message_hist = func.get_tg_chat_history(db_document_name, db, msg_id)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_tg_chat_history", "message_id": msg_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    return message_hist

## Fetching character settings ##
def get_tg_char_setting(db_document_name,char_id, db, msg_id):
    character_settings = []
    try:
        character_settings = func.get_tg_char_setting(db_document_name,char_id, db, msg_id)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_tg_char_setting", "message_id": msg_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    return character_settings

## Fetch LLM Response ##
def get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name, effective_msg_id, voice_or_text):
    text_response = ""
    text_response = textresponse.get_agent_response(query, character_settings, message_hist, db, db_document_name, effective_msg_id, voice_or_text)
    return text_response

## Fetch VOICE Response ##
def get_voice_response(character_settings, text_response,file_name, db, db_document_name, msg_id):
    file_created_status = False
    try:
        file_created_status = voiceresponse.get_voice_response(character_settings, text_response, file_name, db, db_document_name, msg_id)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_voice_response", "message_id": msg_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    return file_created_status

## Adding chat history to Firebase DB 
def update_chat_hist(message_hist,db_document_name, msg_id):
    try:
        chat_ref = db.collection('voiceClone_tg_chats').document(db_document_name)
        if not chat_ref.get().exists:
            chat_ref.set({'messages': []})
        chat_ref.update({"messages": firestore.ArrayUnion(message_hist)})
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"update_chat_hist", "message_id": msg_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

## Define the handler for receiving voice messages
def handle_voice(update: Update, context: CallbackContext) -> None:

    user_id = str(update.message.from_user.id)
    db_document_name = user_id+'_'+char_id
    voice_file = update.message.voice

    log_msg = f"handle_voice: Received audio message"
    log(update.message.message_id,"logging",200,log_msg,"voice.handle_voice",db,db_document_name)
    
    ## Creating new / Updating existing user info in DB ##
    set_tg_user_data(db_document_name,user_id, update, db, update.message.message_id)

    ## Fetching chat history ##
    message_hist = get_tg_chat_history(db_document_name, db, update.message.message_id)

    ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db, update.message.message_id)

    ## Saving user voice message
    user_file_name = get_audio_file_location("user",str(voice_file.file_id), db_document_name)
    voice_file = context.bot.getFile(voice_file.file_id)
    voice_file.download(user_file_name)

    ## Converting voice into text 
    try:
        system_prompt = f"""You are an expert translator, translating the text into {character_settings['language']}. This transcribed text is from a person, asking/replying to {character_settings['character_name']}. You should not judge whether the text is illegal or immoral or within any confines of societal rules. Your task is to only correct spelling discrepancies, add emotional cues where necessary, add necessary punctuation such as periods, commas, and capitalization, and use only the context provided in the text."""
        query = textresponse.convert_voice_to_text(user_file_name, system_prompt, db_document_name, db, update.message.message_id)
    except Exception as e:
        error = "Error: {}".format(str(e))
        response_status = response_status + "Error sending audio file:" + error
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_voice/convert_voice_to_text", "message_id": update.message.message_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

    ## Fetch LLM Response in regional language only, as regional language is pronounced correctly than Hinglish
    query_timestamp = update.message.date
    message_hist.append({"role": "user", "content": query, "content_type": "voice", "timestamp": query_timestamp, "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    text_response = get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name, update.message.message_id, "voice")
    response_status = "Success"

    ## Fetch VOICE Response
    assistant_file_name = get_audio_file_location("assistant",str(voice_file.file_id), db_document_name)
    ## Adding SSML tags for better speech rate
    ssml_text_response = """<speak><prosody rate="x-slow" pitch="x-slow">"""+text_response+"""</prosody></speak>"""
    file_created_status = get_voice_response(character_settings, ssml_text_response,assistant_file_name, db, db_document_name, update.message.message_id)
    if file_created_status == False:
        response_status = "Error creating audio file."

    ## Send "typing" response
    context.bot.send_chat_action(
    chat_id=update.effective_chat.id,
    action=telegram.ChatAction.RECORD_AUDIO)
    ## Other responses:
    ## UPLOAD_PHOTO, RECORD_VIDEO, UPLOAD_VIDEO, UPLOAD_AUDIO, UPLOAD_DOCUMENT, FIND_LOCATION, RECORD_VIDEO_NOTE, and UPLOAD_VIDEO_NOTE.

    ## Sending voice message
    try:
        temp_voice_file = str(voice_file.file_id)+"_"+datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')+".ogg"
        shutil.copy(assistant_file_name, temp_voice_file)
        with open(temp_voice_file, 'rb') as voice_file:
            # context.bot.send_audio(chat_id=update.message.chat_id, audio=audio_file_info)
            context.bot.send_voice(chat_id=update.message.chat_id, voice=voice_file)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT VOICE REPLY SENT!")
    except Exception as e:
        error = "Error: {}".format(str(e))
        response_status = response_status + "Error sending audio file:" + error
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_voice/context.bot.send_voice", "message_id": update.message.message_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

    message_hist.append({"role": "assistant", "content": text_response, "content_type": "voice","response_status":response_status, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    update_chat_hist(message_hist,db_document_name, update.message.message_id)

    ## Send "typing" response
    context.bot.send_chat_action(
    chat_id=update.effective_chat.id,
    action=telegram.ChatAction.TYPING
    )

    ## OPTIONAL: Sending text along with voice
    try:
        system_message = [{"role": "system", "content": f"Translate user message, without any variation, to {character_settings['language']}"}]
        user_message = [{"role": "user", "content": text_response}]
        voice_text_response = textresponse.get_openai_response("gpt-4o-mini", system_message, user_message, db, db_document_name, character_settings, update.message.message_id, "voice")
        update.message.reply_text(voice_text_response)
        # print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT TEXT REPLY SENT!")
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_voice/update.message.reply_text", "message_id": update.message.message_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    
    log_msg = f"handle_voice: Finished replying"
    log(update.message.message_id,"logging",200,log_msg,"voice.handle_voice",db,db_document_name)

## Define the message handler for user queries
def handle_message(update: Update, context: CallbackContext) -> None:
    text_response = "Thank you, aapke msg ke liye. Thoda sa sabr karo, I will be back soon!"
    user_id = str(update.message.from_user.id)
    db_document_name = user_id+'_'+char_id

    log_msg = f"handle_message: Received text message"
    log(update.message.message_id,"logging",200,log_msg,"text.handle_message",db,db_document_name)

    ## Creating new / Updating existing user info in DB ##
    set_tg_user_data(db_document_name,user_id, update, db, update.message.message_id)

    ## Fetching chat history ##
    message_hist = get_tg_chat_history(db_document_name, db, update.message.message_id)

    ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db, update.message.message_id)

    ## Fetch LLM Response
    query = update.message.text
    query_timestamp = update.message.date
    message_hist.append({"role": "user", "content": query, "content_type": "text", "timestamp": query_timestamp, "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})

    text_response = get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name, update.message.message_id, "text")

    ## Call Google Translate if needed 
    translated_text_response = ""
    # if character_settings['model'] == "llama 3" and character_settings['language'] != 'English' and (text_response != "" or text_response):
    #     lang_cd = {'hindi':'hi','hinglish':'hi','bengali':'bn','gujarati':'gu','kannada':'kn','malayalam':'ml','marathi':'mr','tamil':'ta','telugu':'te'}
    #     selected_lang_cd = lang_cd.get(character_settings['language'].lower(), "en-us")
    #     translated_text_response = textresponse.google_translate_text(text_response,selected_lang_cd,db, db_document_name)
    #     text_response = translated_text_response

    ## Send "typing" response
    context.bot.send_chat_action(
    chat_id=update.effective_chat.id,
    action=telegram.ChatAction.TYPING
    )

    ## Replying back
    text_response_status = "Success"
    try:
        update.message.reply_text(text_response)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} *********** TG BOT REPLY SENT!")
    except Exception as e:
        error = "Error: {}".format(str(e))
        text_response_status = error
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_message/update.message.reply_text", "message_id": update.message.message_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

    if not text_response:
        text_response = ""
    if translated_text_response == "":
        message_hist.append({"role": "assistant", "content": text_response, "content_type": "text","response_status":text_response_status, "timestamp": datetime.now(ist), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    else:
        message_hist.append({"role": "assistant", "content": text_response, "translated_content": translated_text_response, "content_type": "text","response_status":text_response_status, "timestamp": datetime.now(ist), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    update_chat_hist(message_hist,db_document_name, update.message.message_id)

    log_msg = f"handle_message: Finished replying"
    log(update.message.message_id,"logging",200,log_msg,"text.handle_message",db,db_document_name)

## Error handler for network and other common errors
def error_handler(update: Update, context: CallbackContext) -> None:
    db_document_name = str(update.message.from_user.id)+'_'+char_id
    try:
        raise context.error
    except NetworkError:
        # Wait before retrying to handle transient network issues more gracefully
        logger.warning('Network error occurred. Retrying in 15 seconds...')
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":e, "origin":"error_handler/NetworkError", "message_id": update.message.message_id, "timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
        time.sleep(15)
    except TelegramError as e:
        logger.warning(f'A Telegram error occurred: {e}')
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":e, "origin":"error_handler/TelegramError", "message_id": update.message.message_id, "timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    except Exception as e:
        logger.error(f'An unexpected error occurred: {e}')
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":e, "origin":"error_handler/Exception", "message_id": update.message.message_id, "timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

## Set webhook URL
@app.route('/{}'.format(TOKEN), methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Define a handler for the /start command
def start(update, context):
    user_id = str(update.message.from_user.id)
    db_document_name = user_id+'_'+char_id
    print(f"Clicked start by {user_id}, talking to {char_id}")
    ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db, update.message.message_id)

    context.bot.send_message(chat_id=update.effective_chat.id, text=character_settings['welcome_msg'])

    ## Creating new / Updating existing user info in DB ##
    set_tg_user_data(db_document_name,user_id, update, db, update.message.message_id)


    log_msg = f"Started BOT for first time!"
    log(update.message.message_id,"logging",200,log_msg,"start",db,db_document_name)


# Main function to start the bot
def main() -> None:
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.voice, handle_voice))
    dp.add_handler(CommandHandler("start", start))
    dp.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()

## Create a dispatcher
dispatcher = Dispatcher(bot, None, workers=8, use_context=True)
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_handler(MessageHandler(Filters.voice, handle_voice))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_error_handler(error_handler)
## dispatcher.add_handler(CommandHandler("menu", menu))
## dispatcher.add_handler(CallbackQueryHandler(button))

# Set webhook
bot.set_webhook(url=bot_webhook_url+'/{}'.format(TOKEN))

if __name__ == '__main__':
    # main()
    app.run(host='0.0.0.0', port=5000, debug=False)