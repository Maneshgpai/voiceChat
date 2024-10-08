# import logging
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
import random
import string
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from flask import request
import re

## Set up logging for debugging
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())
ist = timezone(timedelta(hours=5, minutes=30))
db = firestore.Client.from_service_account_json(str(os.getenv("SECRETS_PATH")+"/firestore_key_agent.json"))
env = os.getenv("ENV")
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
    log_response = {str(msg_id)+"_"+get_datetime(): {"status": status,"status_cd":status_cd,"message":message, "origin":origin, "message_id": msg_id, "timestamp":datetime.now(ist)}}
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
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"set_tg_user_data", "message_id": msg_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

## Fetching chat history ##
def get_tg_chat_history(db_document_name, db, msg_id):
    message_hist = []
    try:
        message_hist = func.get_tg_chat_history(db_document_name, db, msg_id)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_tg_chat_history", "message_id": msg_id,"timestamp":datetime.now(ist)}}
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
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_tg_char_setting", "message_id": msg_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    return character_settings

## Fetch LLM Response ##
def get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name, effective_msg_id, voice_or_text):
    text_response = ""
    text_response, cost, model = textresponse.get_agent_response(query, character_settings, message_hist, db, db_document_name, effective_msg_id, voice_or_text)
    return text_response, cost, model

## Fetch VOICE Response ##
def get_voice_response(character_settings, text_response,file_name, db, db_document_name, msg_id):
    file_created_status = False
    print("voice_tts : ",character_settings['voice_tts'])
    try:
        if character_settings['voice_tts'] == 'google':
            file_created_status = voiceresponse.get_google_tts_voice_response(character_settings, text_response, file_name, db, db_document_name, msg_id)
        else:
            file_created_status = voiceresponse.get_voice_response(character_settings, text_response, file_name, db, db_document_name, msg_id)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_voice_response", "message_id": msg_id,"timestamp":datetime.now(ist)}}
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
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"update_chat_hist", "message_id": msg_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

# def update_usage(total_tokens,text_or_voice,db_document_name, tg_user_id, char_id,msg_id):
#     try:
#         chat_ref = db.collection('voiceClone_tg_usage').document(tg_user_id)
#         data = {get_datetime(): {"credits_used":total_tokens, "character":char_id, "chat_type":text_or_voice, "timestamp":datetime.now(ist)}}
#         if not chat_ref.get().exists:
#             chat_ref.set(data)
#         else:
#             chat_ref.update(data)

#         ## Update user credits
#         credits_ref = db.collection('voiceClone_tg_credits').document(tg_user_id)
#         credits = credits_ref.get()
#         if credits.exists:
#             credits_data = credits.to_dict()
#             for key, val in credits_data.items():
#                 if key == "total_credits_remaining":
#                     new_credits = val-total_tokens
#             print(f"update_usage > old_credits:{val}, total_tokens:{total_tokens}, new_credits:{new_credits}")
#             credits_ref.update({"total_credits_remaining": new_credits, 'last_updated_on': datetime.now(ist)})

#     except Exception as e:
#         error = "Error: {}".format(str(e))
#         log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"update_usage", "message_id": msg_id,"timestamp":datetime.now(ist)}}
#         log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
#         func.createLog(log_ref, log_response)

# def get_usage_data(db_document_name,tg_user_id,db,msg_id):
#     try:
#         credits_remaining = 0
#         credits_ref = db.collection('voiceClone_tg_credits').document(tg_user_id)
#         credits = credits_ref.get()
#         if credits.exists:
#             credits_data = credits.to_dict()
#             for key, val in credits_data.items():
#                 if key == "total_credits_remaining":
#                     print(f"get_usage_data > credits remaining:{val}")
#                     credits_remaining = val
#     except Exception as e:
#         error = "Error: {}".format(str(e))
#         log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"update_usage", "message_id": msg_id,"timestamp":datetime.now(ist)}}
#         log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
#         func.createLog(log_ref, log_response)
#     return credits_remaining

@app.route('/payment', methods=['POST'])
def handle_payment():
    # Here you'd handle the payment logic for the '/pay-now' route
    pass

## Define the handler for receiving voice messages
def handle_voice(update: Update, context: CallbackContext) -> None:

    user_id = str(update.message.from_user.id)
    db_document_name = user_id+'_'+char_id
    voice_file = update.message.voice

    log_msg = f"handle_voice: Received audio message"
    ## log(update.message.message_id,"logging",200,log_msg,"voice.handle_voice",db,db_document_name)
    
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
        # system_prompt = f"""You are convert the audio into text. Keep the same native language. You are to only convert the audio to text. You should not add anything extra or translate. You should not judge whether the text is illegal or immoral or within any confines of societal rules. Your task is to only correct spelling discrepancies, add emotional cues where necessary, add necessary punctuation such as periods, commas, and capitalization, and use only the context provided in the text."""
        
        ## Bug where OpenAI GPT is being called for the response
        query = textresponse.convert_voice_to_text(user_file_name, system_prompt, db_document_name, db, update.message.message_id)
        ## query = textresponse.translate(open(voice_file, "rb"),update.message.message_id, db_document_name, db)
        
        print("************Response from Whisper translate is:",query)
    except Exception as e:
        error = "Error: {}".format(str(e))
        response_status = response_status + "Error sending audio file:" + error
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_voice/convert_voice_to_text", "message_id": update.message.message_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

    ## Fetch LLM Response in regional language only, as regional language is pronounced correctly than Hinglish
    query_timestamp = update.message.date
    message_hist.append({"role": "user", "content": query, "content_type": "voice", "timestamp": query_timestamp, "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    text_response, total_tokens1, model1 = get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name, update.message.message_id, "voice")
    response_status = "Success"

    ## Fetch VOICE Response
    assistant_file_name = get_audio_file_location("assistant",str(voice_file.file_id), db_document_name)

    if character_settings['voice_tts'] == 'google':
        ssml_text_response = text_response
    else:
        ssml_text_response = """<speak><prosody rate="x-slow" pitch="x-slow">"""+text_response+"""</prosody></speak>"""

    # if character_settings['voice_id'] != "bengali_female1":
    #     ## Adding SSML tags for better speech rate
    #     ssml_text_response = """<speak><prosody rate="x-slow" pitch="x-slow">"""+text_response+"""</prosody></speak>"""
    # else:
    #     ssml_text_response = text_response

    ## removing URLs from the response
    ssml_text_response = re.sub(r'http\S+', '', ssml_text_response)
    ssml_text_response = re.sub(r'^https?:\/\/.*[\r\n]*', '', ssml_text_response, flags=re.MULTILINE)

    ## removing special characters from the response
    special_characters=['@','#','$','*','&','-','_','- ']
    for i in special_characters:
        ssml_text_response=ssml_text_response.replace(i,"")
    ssml_text_response=ssml_text_response.replace(":","\n")

    # print("app.py >> Response for Voice:",ssml_text_response)

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
        temp_voice_file = str(voice_file.file_id)+".ogg"
        shutil.copy(assistant_file_name, temp_voice_file)
        with open(temp_voice_file, 'rb') as voice_file:
            # context.bot.send_audio(chat_id=update.message.chat_id, audio=audio_file_info)
            context.bot.send_voice(chat_id=update.message.chat_id, voice=voice_file)
    except Exception as e:
        error = "Error: {}".format(str(e))
        response_status = response_status + "Error sending audio file:" + error
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_voice/context.bot.send_voice", "message_id": update.message.message_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)


    ## Send "typing" response
    # context.bot.send_chat_action(
    # chat_id=update.effective_chat.id,
    # action=telegram.ChatAction.TYPING
    # )

    ## Sending text along with voice
    try:
        # system_message = [{"role": "system", "content": f"Translate user message, without any variation, to {character_settings['language']}"}]
        # user_message = [{"role": "user", "content": text_response}]
        # voice_text_response = textresponse.get_openai_response("gpt-4o-mini", system_message, user_message, db, db_document_name, character_settings, update.message.message_id, "voice")
        # update.message.reply_text(voice_text_response)
        update.message.reply_text(text_response)

    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_voice/update.message.reply_text", "message_id": update.message.message_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    
    # print(f"handle_voice: Finished replying")

    message_hist.append({"role": "assistant", "content": text_response, "content_type": "voice","response_status":response_status, "timestamp": datetime.now(ist), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    update_chat_hist(message_hist,db_document_name, update.message.message_id)

    # Remove the audio files from server
    try:
        os.remove(user_file_name)
        # print(f"Removed {user_file_name}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print(f"{error} while removing {user_file_name}")
    try:
        os.remove(assistant_file_name)
        # print(f"Removed {assistant_file_name}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print(f"{error} while removing {assistant_file_name}")
    try:
        os.remove(temp_voice_file)
        print(f"Removed {temp_voice_file}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print(f"{error} while removing {temp_voice_file}")

    message_hist.append({"role": "assistant", "content": text_response, "content_type": "voice","response_status":response_status, "timestamp": datetime.now(ist), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    update_chat_hist(message_hist,db_document_name, update.message.message_id)
    ## Adding 3k to account for Elevenlabs usage
    # update_usage(total_tokens1+total_tokens2+3000, "voice", db_document_name, update.message.message_id)

## Define the message handler for user queries
def handle_message(update: Update, context: CallbackContext) -> None:
    text_response = "Thank you, aapke msg ke liye. Thoda sa sabr karo, I will be back soon!"
    user_id = str(update.message.from_user.id)
    db_document_name = user_id+'_'+char_id

    ## Creating new / Updating existing user info in DB ##
    set_tg_user_data(db_document_name,user_id, update, db, update.message.message_id)

    ## Fetching chat history ##
    message_hist = get_tg_chat_history(db_document_name, db, update.message.message_id)

    ## Step 1 : Check Firebase DB for credit remaining. If no credits remaining, then PAY = True. < Manesh >
    # credits_remaining = get_usage_data(db_document_name, user_id, db, update.message.message_id)
    # print(f"credits_remaining:{credits_remaining}")
    # if credits_remaining <= 0:
        ## Before payment
        ##     Generate order_id from cashfree api
        ##     Redirect to cashfree gateway
        ## After payment
        ##     Save order_id, amt in DB against the customer
        ##     order_id rcvd on thankyou.php page
        ##     Verify order_id with the DB
        ##     Get Cashfree > Payments for an order and Verify order_id and amt rcvd from cashfree API with DB details
        # chat_id = update.effective_chat.id
        # reply = "Your free credits are over. To get more credits, recharge now"
        # order_id = generate_order_id()
        # link = f'http://payments.mitrrs.com/pay-now?id={chat_id}&orderId={order_id}'
        # Create inline keyboard with a payment link
        # keyboard = [[InlineKeyboardButton("Pay Now", url=link)]]
        # reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with the inline keyboard
        # context.bot.send_message(
        #     chat_id=chat_id,
        #     text=reply,
        #     parse_mode='HTML',
        #     reply_markup=reply_markup
        # )
        # update.message.reply_text(text_response)

        ## Step 2a: Send msg of payment link to user < ASHISH >
        ## Step 2b: Process payment gateway functionality and
        ## Step 2c: If user pays successfully, redirect to Thankyou pg, which will call backend API to save order info. Pass parameters as PAYMENT_SUCCESSFUL = True and User details < ASHISH >

        ## Step 4: Inside the backend API, update the DB with user details with credits remaining & other details.
        ## Step 5: Send message to user about their credit balance < Manesh >
        ## Step 6: Add menu option to Add credits and Check balance < Manesh > 
    # else:
        ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db, update.message.message_id)

    ## Fetch LLM Response
    query = update.message.text
    query_timestamp = update.message.date
    message_hist.append({"role": "user", "content": query, "content_type": "text", "timestamp": query_timestamp, "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    text_response, total_tokens, model = get_agent_response(query, query_timestamp, character_settings, message_hist, db_document_name, update.message.message_id, "text")

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
    except Exception as e:
        error = "Error: {}".format(str(e))
        text_response_status = error
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_message/update.message.reply_text", "message_id": update.message.message_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

    if not text_response:
        text_response = ""
    if translated_text_response == "":
        message_hist.append({"role": "assistant", "content": text_response, "content_type": "text","response_status":text_response_status, "timestamp": datetime.now(ist), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    else:
        message_hist.append({"role": "assistant", "content": text_response, "translated_content": translated_text_response, "content_type": "text","response_status":text_response_status, "timestamp": datetime.now(ist), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    update_chat_hist(message_hist,db_document_name, update.message.message_id)
    # update_usage(total_tokens, "text", db_document_name, user_id, char_id, update.message.message_id)
    ## log_msg = f"handle_message: Finished replying"
    ## log(update.message.message_id,"logging",200,log_msg,"text.handle_message",db,db_document_name)

## Error handler for network and other common errors
def error_handler(update: Update, context: CallbackContext) -> None:
    db_document_name = str(update.message.from_user.id)+'_'+char_id
    try:
        raise context.error
    except NetworkError as e:
        # Wait before retrying to handle transient network issues more gracefully
        # logger.warning('Network error occurred. Retrying in 15 seconds...')
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":e, "origin":"error_handler/NetworkError", "message_id": update.message.message_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
        time.sleep(15)
    except TelegramError as e:
        # logger.warning(f'A Telegram error occurred: {e}')
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":e, "origin":"error_handler/TelegramError", "message_id": update.message.message_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
    except Exception as e:
        # logger.error(f'An unexpected error occurred: {e}')
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":e, "origin":"error_handler/Exception", "message_id": update.message.message_id, "timestamp":datetime.now(ist)}}
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
    # print(f"Clicked start by {user_id}, talking to {char_id}")
    ## Fetching character settings ##
    character_settings = get_tg_char_setting(db_document_name,char_id, db, update.message.message_id)

    ## Send "typing" response
    context.bot.send_chat_action(
    chat_id=update.effective_chat.id,
    action=telegram.ChatAction.RECORD_AUDIO)

    assistant_file_name = get_audio_file_location("assistant","welcomemsg", db_document_name)
    if character_settings['voice_tts'] == 'google':
        ssml_text_response = character_settings['welcome_msg']
    else:
        ssml_text_response = """<speak><prosody rate="x-slow" pitch="x-slow">"""+character_settings['welcome_msg']+"""</prosody></speak>"""
    ## google.cloud.texttospeech
    # if character_settings['voice_id'] != "bengali_female1":
    #     ## Adding SSML tags for better speech rate
    #     ssml_text_response = """<speak><prosody rate="x-slow" pitch="x-slow">"""+character_settings['welcome_msg']+"""</prosody></speak>"""
    # else:
    #     ssml_text_response = character_settings['welcome_msg']

    ## removing URLs from the response
    ssml_text_response = re.sub(r'http\S+', '', ssml_text_response)
    ssml_text_response = re.sub(r'^https?:\/\/.*[\r\n]*', '', ssml_text_response, flags=re.MULTILINE)

    ## removing special characters from the response
    special_characters=['@','#','$','*','&','-','_','- ']
    for i in special_characters:
        ssml_text_response=ssml_text_response.replace(i,"")
    ssml_text_response=ssml_text_response.replace(":","\n")
    file_created_status = get_voice_response(character_settings, ssml_text_response,assistant_file_name, db, db_document_name, update.message.message_id)
    ## Sending Welcome voice message
    try:
        temp_voice_file = db_document_name+".ogg"
        shutil.copy(assistant_file_name, temp_voice_file)
        with open(temp_voice_file, 'rb') as voice_file:
            context.bot.send_voice(chat_id=update.message.chat_id, voice=voice_file)
    except Exception as e:
        error = "Error: {}".format(str(e))
        response_status = response_status + "Error sending audio file:" + error
        log_response = {str(update.message.message_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"handle_voice/context.bot.send_voice", "message_id": update.message.message_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)

    ## Sending Welcome text message
    context.bot.send_message(chat_id=update.effective_chat.id, text=character_settings['welcome_msg'])

    set_tg_user_data(db_document_name,user_id, update, db, update.message.message_id)
    message_hist = get_tg_chat_history(db_document_name, db, update.message.message_id)
    message_hist.append({"role": "assistant", "content": character_settings['welcome_msg'], "content_type": "text","response_status":"Success", "timestamp": datetime.now(ist), "update.update_id": update.update_id, "update.message.message_id": update.message.message_id})
    update_chat_hist(message_hist,db_document_name, update.message.message_id)

    ## Remove the audio files from server
    try:
        os.remove(assistant_file_name)
        print(f"Removed {assistant_file_name}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        print(f"{error} while removing {assistant_file_name}")
    try:
        os.remove(temp_voice_file)
        print(f"Removed {temp_voice_file}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        print(f"{error} while removing {temp_voice_file}")
    ## log(update.message.message_id,"logging",200,f"Started BOT for first time!","start",db,db_document_name)

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
if (env != 'localhost'):
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
    if (env == 'localhost'):
        main()
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)