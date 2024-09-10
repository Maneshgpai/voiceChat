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
db = firestore.Client.from_service_account_json("firestore_key_agent.json")

def get_character_dtls():
    print("Downloading Character data...")
    collection_ref = db.collection('profile')
    docs = collection_ref.stream()
    charid_bottoken = []
    charid_prompt = []
    for doc in docs:
        doc_id = doc.id
        charid_bottoken_doc = {}
        charid_prompt_doc = {}
        settings = doc.to_dict().pop('setting', {})
        for key, value in settings.items():
            if key == "bot_token":
                charid_bottoken_doc[doc_id] = value
            if key == "reachout_prompt":
                charid_prompt_doc[doc_id] = value
        charid_bottoken.append(charid_bottoken_doc)
        charid_prompt.append(charid_prompt_doc)
    return charid_bottoken, charid_prompt

def update_user_status(document_name,user_status):
    doc_ref = db.collection('user').document(document_name)
    doc = doc_ref.get()
    user_data = {'status': user_status,'status_change_dt': datetime.now(ist)}
    doc_ref.update(user_data)

def set_user_status(bot_token,tg_user_id,document_name):
    user_status = 'inactive'
    try:
        # print(f"Checking user status for {document_name}")
        bot = telegram.Bot(token=bot_token)
        bot.send_chat_action(chat_id=tg_user_id,action=telegram.ChatAction.TYPING)
        user_status = 'active'
        update_user_status(document_name,user_status)
    except telegram.error.Unauthorized:
        user_status = 'blocked_bot'
        update_user_status(document_name,user_status)
    except telegram.error.BadRequest as e:
        if "chat not found" in str(e):
            user_status = 'deleted_bot'
            update_user_status(document_name,user_status)
    except Exception as e:
        error = "Error: {}".format(str(e))
        if "Invalid token" in str(e):
            user_status = 'invalid_token'
            update_user_status(document_name,user_status)
        else:
            user_status = str(e)
        print("check_user_active >> error:",error)
    
    if user_status == 'inactive':
        update_user_status(document_name,user_status)
    print(f"Updating user {document_name} as {user_status}")

charid_bottoken, charid_prompt = get_character_dtls()
collection_ref = db.collection("user")
docs = collection_ref.stream()
for doc in docs:
    document_name = doc.id
    array = document_name.split("_")
    tg_user_id = array[0]
    char_id = array[1]
    for key, value in enumerate(charid_bottoken):
        for k, v in value.items():
            if k == char_id:
                bot_token = v
    # print(f"Checking status for bot {bot_token} for {document_name}")
    set_user_status(bot_token,tg_user_id,document_name)