from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import os
import json
from dotenv import load_dotenv
from transformers import AutoTokenizer
# import tiktoken

ist = timezone(timedelta(hours=5, minutes=30))
load_dotenv()
default_setting = json.loads(os.getenv("DEFAULT_CHARACTER_SETTING"))
# encoding = tiktoken.get_encoding("cl100k_base")


def set_default_settings(voice_id):
    db = firestore.Client.from_service_account_json("firestore_key.json")
    db.collection('voiceClone_characters').document(voice_id).set({"timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"action":"update_profile","setting":default_setting})

def get_default_settings():
    return default_setting

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

# def get_chat_history(document_id, db):
#     try:
#         chat_ref = db.collection('voiceClone_chats').document(document_id)
#         doc = chat_ref.get()
#         if doc.exists:
#             return doc.to_dict().get('messages', [])
#         else:
#             chat_ref.set({'messages': []})
#             return []
#     except Exception as e:
#         error = "Error: {}".format(str(e))
#         log_response = {"status": "TG_Bot/functionSrvr/get_voice_setting: error","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
#         log_ref = db.collection('voiceClone_log').document(document_id)
#         createLog(log_ref, log_response)
#         return error

def get_tg_chat_history(document_id, db, effective_chat_id):
    try:
        chat_ref = db.collection('voiceClone_tg_chats').document(document_id)
        doc = chat_ref.get()
        if doc.exists:
            print("TG_Bot/functionSrvr/get_tg_chat_history > Fetching chat history from 'voiceClone_tg_chats' for ",document_id)
            return doc.to_dict().get('messages', [])
        else:
            print("TG_Bot/functionSrvr/get_tg_chat_history > Creating new chat for 'voiceClone_tg_chats' for ",document_id)
            chat_ref.set({'messages': []})
            return []
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("*** ERROR *** TG_Bot/functionSrvr/get_tg_chat_history > Error ",error)
        log_response = {"status": "TG_Bot/functionSrvr/get_voice_setting: error","status_cd":400, "message": error,"update.effective_chat.id":effective_chat_id,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(document_id)
        createLog(log_ref, log_response)
        return error

def createLog(log_ref, response):
    log_ref.collection("session_"+datetime.now(ist).strftime('%Y-%m-%d')).document(str(datetime.now(ist))).set(response)

def set_tg_user_data(db_document_name,user_id, update, db,effective_chat_id):
    # try:
    #     doc_ref = db.collection('voiceClone_tg_update').document(db_document_name)
    #     doc = doc_ref.get()
        
    #     tg_update_json = json.dumps(tg_update.message)
    #     tg_update_str = str(tg_update_json)

    #     if doc.exists:
    #         print("TG_Bot/functionSrvr/set_tg_user_data > Updating 'voiceClone_tg_update' for ",db_document_name)
    #         doc_ref.update({"update":tg_update_str,'last_updated_on': datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    #     else:
    #         print("TG_Bot/functionSrvr/set_tg_user_data > Creating new entry in 'voiceClone_tg_update' for ",db_document_name)
    #         doc_ref.set({"update":tg_update_str, "created_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"last_updated_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    # except Exception as e:
    #     error = "Error: {}".format(str(e))
    #     print("*** ERROR *** TG_Bot/functionSrvr/set_tg_user_data > Error in updating 'voiceClone_tg_update' ",error)
    #     log_response = {"status": "TG_Bot/functionSrvr/get_user_data: Error in updating voiceClone_tg_update","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    #     log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
    #     createLog(log_ref, log_response)

    # try:
    #     doc_ref = db.collection('voiceClone_tg_update_message').document(db_document_name)
    #     doc = doc_ref.get()
    #     if doc.exists:
    #         print("TG_Bot/functionSrvr/set_tg_user_data > Updating 'voiceClone_tg_update_message' for ",db_document_name)
    #         doc_ref.update({'last_updated_on': datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    #     else:
    #         print("TG_Bot/functionSrvr/set_tg_user_data > Creating new entry in 'voiceClone_tg_update_message' for ",db_document_name)
    #         doc_ref.set({"update.message":json.dumps(update.message), "created_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"last_updated_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    # except Exception as e:
    #     error = "Error: {}".format(str(e))
    #     print("*** ERROR *** TG_Bot/functionSrvr/set_tg_user_data > Error in updating 'voiceClone_tg_update_message'",error)
    #     log_response = {"status": "TG_Bot/functionSrvr/get_user_data: error","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    #     log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
    #     createLog(log_ref, log_response)

    try:
        doc_ref = db.collection('voiceClone_tg_users').document(db_document_name)
        doc = doc_ref.get()
        if doc.exists:
            print("TG_Bot/functionSrvr/set_tg_user_data > Updating 'voiceClone_tg_users' for ",db_document_name)
            user_data = {'first_name' : update.message.from_user.first_name,
            'last_name' : update.message.from_user.last_name,
            'username' : update.message.from_user.username,
            'language_code' : update.message.from_user.language_code,
            'last_updated_on': datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}
            doc_ref.update(user_data)
        else:
            print("TG_Bot/functionSrvr/set_tg_user_data > Creating new entry in 'voiceClone_tg_users' for ",db_document_name)
            user_data = {'id' : update.message.from_user.id,
            'first_name' : update.message.from_user.first_name,
            'last_name' : update.message.from_user.last_name,
            'username' : update.message.from_user.username,
            'is_bot' : update.message.from_user.is_bot,
            'language_code' : update.message.from_user.language_code,
            'created_on' : datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated_on': datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}
            doc_ref.set(user_data)
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("*** ERROR *** TG_Bot/functionSrvr/set_tg_user_data > Error in updating 'voiceClone_tg_users'",error)
        log_response = {"status": "TG_Bot/functionSrvr/get_user_data: Error in updating voiceClone_tg_users","status_cd":400, "message": error,"update.effective_chat.id":effective_chat_id,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        createLog(log_ref, log_response)

def get_tg_char_setting(db_document_name,char_id, db, effective_chat_id):
    char_setting = {}
    try:
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
        log_response = {"status": "TG_Bot/functionSrvr/get_tg_char_setting: error","status_cd":400, "message": error,"update.effective_chat.id":effective_chat_id,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        createLog(log_ref, log_response)
    return char_setting

def get_user_info(telegram_id, db):
    collection_ref = db.collection('voiceClone_users')
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

def calculate_tokens(model, input_text):
    if 'llama' in model.lower():
        tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B", token=os.getenv("HUGGINGFACE_API_KEY"))
        tokens = tokenizer.tokenize(input_text)
        token_count = len(tokens)
    # elif 'gpt-4o' in model.lower():
    #     encoded_tokens = encoding.encode(input_text)
    #     token_count = len(encoded_tokens)
    return token_count