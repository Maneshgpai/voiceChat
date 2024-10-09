from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import os
import json
from dotenv import load_dotenv
from transformers import AutoTokenizer
import telegram
# import tiktoken

ist = timezone(timedelta(hours=5, minutes=30))
load_dotenv()
default_setting = json.loads(os.getenv("DEFAULT_CHARACTER_SETTING"))

# encoding = tiktoken.get_encoding("cl100k_base")

def get_datetime():
    return (str(datetime.now())).replace('.','').replace(':','').replace(' ','').replace('-','')

def set_default_settings(voice_id):
    db = firestore.Client.from_service_account_json(str(os.getenv("SECRETS_PATH")+"/firestore_key_agent.json"))
    db.collection('voiceClone_characters').document(voice_id).set({"timestamp": datetime.now(ist),"action":"update_profile","setting":default_setting})

def get_default_settings():
    return json.loads(os.getenv("DEFAULT_CHARACTER_SETTING"))

def update_user_status(document_name,user_status, db):
    doc_ref = db.collection('voiceClone_tg_users').document(document_name)
    doc = doc_ref.get()
    if doc.exists:
        print(f"functionSrvr/update_user_status > Updating user {document_name} as {user_status}")
        user_data = {'status': user_status,'status_change_dt': datetime.now(ist)}
        doc_ref.update(user_data)

def check_user_status(bot_token,tg_user_id,db,document_name):
    # check if DB status = active.
    # If there is no DB status, then only do the below 
    userdata = get_tg_user_data(document_name, db)
    user_status = userdata.get('status',False)
    if user_status == False:
        try:
            # print(f"Checking user status for {document_name}...")
            bot = telegram.Bot(token=bot_token)
            bot.send_chat_action(chat_id=tg_user_id,action=telegram.ChatAction.TYPING)
            user_status = 'active'
        except telegram.error.Unauthorized:
            # print('User blocked bot')
            user_status = 'blocked_bot'
            update_user_status(document_name,user_status, db)
        except telegram.error.BadRequest as e:
            if "chat not found" in str(e):
                # print('User deleted bot')
                user_status = 'deleted_bot'
                update_user_status(document_name,user_status, db)
        except Exception as e:
            error = "Error: {}".format(str(e))
            if "Invalid token" in str(e):
                user_status = 'invalid_token'
                update_user_status(document_name,user_status, db)
            print("check_user_active >> error:",error)

    return user_status

def get_tg_user_data(document_name, db):
    doc_ref = db.collection('voiceClone_tg_users').document(document_name)
    doc = doc_ref.get()
    if doc.exists:
        userdata = doc.to_dict()
    else:
        userdata = {}
    return userdata

def get_voice_setting(voice_id, db):
    setting = db.collection('voiceClone_characters').document(voice_id)
    doc = setting.get()
    voice_setting = {}
    if doc.exists:
        setting = doc.to_dict()
        for k, v in setting.items():
            if k == 'setting':
                voice_setting = v
    else:
        voice_setting = get_default_settings()
    return voice_setting

def get_tg_chat_history(document_id, db, msg_id):
    try:
        chat_ref = db.collection('voiceClone_tg_chats').document(document_id)
        doc = chat_ref.get()
        if doc.exists:
            print("TG_Bot/functionSrvr/get_tg_chat_history > Fetching chat history from 'chat' for ",document_id)
            return doc.to_dict().get('messages', [])
        else:
            print("TG_Bot/functionSrvr/get_tg_chat_history > Creating new chat for 'chat' for ",document_id)
            chat_ref.set({'messages': []})
            return []
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print("*** ERROR *** TG_Bot/functionSrvr/get_tg_chat_history > Error ",error)
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_tg_chat_history", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(document_id)
        createLog(log_ref, log_response)
        return error

def createLog(log_ref, response):
    # log_ref.collection("session_"+datetime.now(ist).strftime('%Y-%m-%d')).document(str(datetime.now(ist))).set(response)
    doc = log_ref.get()
    if doc.exists:
        log_ref.update(response)
    else:
        log_ref.set(response)

def set_tg_user_data(db_document_name, user_id, update, db, msg_id):
    try:
        doc_ref = db.collection('voiceClone_tg_users').document(db_document_name)
        doc = doc_ref.get()
        if doc.exists:
            print("TG_Bot/functionSrvr/set_tg_user_data > Updating 'user' for ",db_document_name)
            user_data = {'first_name' : update.message.from_user.first_name,
            'last_name' : update.message.from_user.last_name,
            'username' : update.message.from_user.username,
            'language_code' : update.message.from_user.language_code,
            'status' : 'active',
            'last_updated_on': datetime.now(ist)}
            doc_ref.update(user_data)
        else:
            print("TG_Bot/functionSrvr/set_tg_user_data > Creating new entry in 'user' for ",db_document_name)
            user_data = {'id' : update.message.from_user.id,
            'first_name' : update.message.from_user.first_name,
            'last_name' : update.message.from_user.last_name,
            'username' : update.message.from_user.username,
            'is_bot' : update.message.from_user.is_bot,
            'language_code' : update.message.from_user.language_code,
            'status' : 'active',
            'created_on' : datetime.now(ist),
            'last_updated_on': datetime.now(ist)}
            doc_ref.set(user_data)

            ## Create joining free credits
            print("TG_Bot/functionSrvr/set_tg_user_data > Creating new entry in 'voiceClone_tg_credits' for ",str(update.message.from_user.id))
            doc_ref = db.collection('voiceClone_tg_credits').document(str(update.message.from_user.id))
            doc_ref.set({"total_credits_remaining": int(os.getenv("JOINING_CREDITS")), 'created_on' : datetime.now(ist), 'last_updated_on': datetime.now(ist)})
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print("*** ERROR *** TG_Bot/functionSrvr/set_tg_user_data > Error in updating 'voiceClone_tg_users'",error)
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"set_tg_user_data.voiceClone_tg_users", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        createLog(log_ref, log_response)

def get_tg_char_setting(db_document_name,char_id, db, msg_id):
    char_setting = {}
    try:
        # print(f"In functionSrvr.py >> get_tg_char_setting > char_id:{char_id}, db_document_name:{db_document_name}")
        setting = db.collection('voiceClone_characters').document(char_id)
        doc = setting.get()
        if doc.exists:
            print("TG_Bot/functionSrvr/get_tg_char_setting > Fetching character setting from DB, for char_id ",char_id)
            setting = doc.to_dict()
            for k, v in setting.items():
                if k == 'setting':
                    char_setting = v
        else:
            print("TG_Bot/functionSrvr/get_tg_char_setting > Character settings not present in DB. Reverting to Default setting. For char_id ",char_id)
            char_setting = json.loads(os.getenv("DEFAULT_CHARACTER_SETTING"))
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("*** ERROR *** TG_Bot/functionSrvr/get_tg_char_setting > ",error)
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"get_tg_char_setting", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        createLog(log_ref, log_response)
    return char_setting

def get_user_info(telegram_id, db):
    collection_ref = db.collection('voiceClone_tg_users')
    field_name = 'telegram_id'
    field_value = telegram_id
    query = collection_ref.where(field_name, '==',field_value)
    results = query.stream()
    for doc in results:
        doc_data = doc.to_dict()
        if field_name in doc_data:
            if doc_data[field_name] == field_value:
                user_name = doc_data['user_name']
                document_id = doc.id
            else:
                print("Given Telegram ID does not exist in DB")
    return user_name, document_id

def calculate_tokens(model, input_text, db, db_document_name, msg_id):
    try:
        if 'llama' in model.lower():
            # tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B", token=os.getenv("HUGGINGFACE_API_KEY"))
            tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-70B", token=os.getenv("HUGGINGFACE_API_KEY"))
            tokens = tokenizer.tokenize(input_text)
            token_count = len(tokens)
        return token_count
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("*** ERROR *** TG_Bot/functionSrvr/get_tg_char_setting > ",error)
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"calculate_tokens", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        createLog(log_ref, log_response)
