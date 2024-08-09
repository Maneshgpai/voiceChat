# Reachout Program:
# Purpose: Increase engagement of the user with bots
# How is it achieved? Keep reaching out with greetings/followup with past conversation/interesting content using llama3.1
# Chain of thought:
# For every user-character combination:
# 1. Based on the last conversation (latest 6 chats) between user/bot
# 2. Fetch last "reachout" msg
# 3. Fetch personality assessment record (future enhancement)
#   Check if the last conversation was more than 1 hr OR if it is last reachout, then was it more than 6 hrs
# If No, skip to next user
# If Yes, do any of the below in random order. Use Voice or Text in random order:
# FIrst check if last conversation can be a conversation starter:
# If yes, share a comment based on the last conversation. 
# If no, send as per most suited per the user's personality assessment and which is different than last reachout:
# - Getting to know you questions: Bollywood, Sports/Cricket, Food, Work, Culture & festivals, Travel, Family & Friends related. Wat could be some questions which relate with our TAM, without being creepy?
# - Ice-breakers: What's your favorite animal? or If you could only wear one color forever, which would you choose?
# - Juicy questions: What's the worst advice you've ever gotten? or Who has been a big influence on you?
# - Open-ended questions: What's one movie that made you cry? or What's one quality you hope to change about yourself?
# - Light greeting based on the mood of user's last comment (Greeting could be GM/GA/GN or Kaise ho, Kya chal raha hain?)
# - If it is is any time like 7am/1pm/9pm, send a greeting (GM/GA/GN)
# - Gossip/ riddle/ joke/ titbits/ short story based on the bot's character
# - Keep a track of these reachout within chat history

# Test cases
# Logical:
    # Don't run between 2am to 5am
    # Is it triggering if last message was less than 6 hours ago
    # Is it triggering even after last 4 consecutive "reachout"
    # Is it triggering as per voice or text as per the last content_type
    # Are voiceClone_tg_chats populating correctly
    # Are voiceClone_tg_logs populating correctly
    # Are voiceClone_tg_reachout populating correctly
# Functional:
    # Are reachouts relevant & interesting, as per character?

from pytz import timezone
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta #, timezone
import telegram
import os
from google.cloud import firestore
import pandas as pd
from functions import functionSrvr as func
from functions import textResponseSrvr as textresponse
from functions import voiceResponseSrvr as voiceresponse
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
ist = timezone("Asia/Kolkata")
db = firestore.Client.from_service_account_json("firestore_key.json")

## reachout parameters
latest_messages_to_check = os.getenv("REACHOUT_LATEST_MSG_TO_CHECK")
reachout_max_limit = os.getenv("REACHOUT_MAX_LIMIT")
reachout_chat_min_timeinterval_minutes = os.getenv("REACHOUT_CHAT_MIN_TIMEINTERVAL_MIN")
charid_bottoken = os.getenv("REACHOUT_CHARID_BOT_TOKEN")

def get_datetime():
    return (str(datetime.now())).replace('.','').replace(':','').replace(' ','').replace('-','')
def log(status,status_cd,message,origin,db_document_name):
    log_response = {"reachout"+"_"+get_datetime(): {"status": status,"status_cd":status_cd,"message":message, "origin":origin, "reachout": True, "timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
    func.createLog(log_ref, log_response)
def update_chat_hist(message_hist,db_document_name, msg_id):
    try:
        chat_ref = db.collection('voiceClone_tg_chats_test_reachout').document(db_document_name)
        if not chat_ref.get().exists:
            chat_ref.set({'messages': []})
        chat_ref.update({"messages": firestore.ArrayUnion(message_hist)})
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+get_datetime(): {"status": "error","status_cd":400,"message":error, "origin":"update_chat_hist", "message_id": msg_id,"timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
        func.createLog(log_ref, log_response)
def sendtgtext(token, tg_user_id, text, message_hist, db_document_name ):
    try:
        bot = telegram.Bot(token=token)
        bot.send_chat_action(chat_id=tg_user_id,action=telegram.ChatAction.TYPING)
        bot.send_message(chat_id=tg_user_id, text=text)
        update_chat_hist(message_hist,db_document_name, "reachout")
        update_reachout_hist(text,'text',db_document_name)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log("error",400,error,"text"+".reachout.sendtgtext",db_document_name)
def sendtgvoice(token, tg_user_id, voice, text, message_hist, db_document_name):
    try:
        bot = telegram.Bot(token=token)
        bot.send_chat_action(chat_id=tg_user_id,action=telegram.ChatAction.RECORD_AUDIO)
        with open(voice, 'rb') as voice_file:
            bot.send_voice(chat_id=tg_user_id, voice=voice_file)
        update_chat_hist(message_hist,db_document_name, "reachout")
        update_reachout_hist(text,'voice',db_document_name)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log("error",400,error,"voice"+".reachout.sendtgvoice",db_document_name)
def get_reachout_response(system_prompt,message_hist, db_document_name, voice_or_text):
    try:
        user_message = textresponse.fetch_optimized_chat_hist_for_openai(message_hist)
        system_message = [{"role": "system", "content": system_prompt}]
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=system_message+user_message,
            stream=False,
            frequency_penalty = 1.2,
            max_tokens = 200,
            top_p = 0.5,
            presence_penalty = 1.5,
            temperature=1.2,
        )
        full_response = response.choices[0].message.content
        return full_response
    except Exception as e:
        error = "Error: {}".format(str(e))
        print(f"response:{response}")
        log("error",400,error,voice_or_text+".get_reachout_response",db_document_name)
def fetch_latest_messages():
    all_docs = []
    collection_ref = db.collection('voiceClone_tg_chats_test_reachout')
    for doc in collection_ref.stream():
        doc_id = doc.id
        doc_data = doc.to_dict()
        
        if 'messages' in doc_data:
            messages = doc_data['messages']
            for message in messages:
                if 'timestamp' in message and isinstance(message['timestamp'], datetime):
                    message['timestamp'] += timedelta(hours=5, minutes=30)
            all_docs.append({'doc_id': doc_id, 'messages': messages})

    all_docs.sort(key=lambda x: max(msg['timestamp'] for msg in x['messages']), reverse=True)
    latest_docs = all_docs[:3]

    output = {}
    for doc in latest_docs:
        sorted_messages = sorted(doc['messages'], key=lambda x: x['timestamp'], reverse=True)
        latest_messages = sorted_messages[:latest_messages_to_check]
        
        latest_content_type = latest_messages[0].get('content_type', 'text')
        last_messaged_on = latest_messages[0]['timestamp']

        # Count consecutive 'reachout' = true
        reachout_count = 0
        for message in latest_messages:
            if message.get('reachout', False):
                reachout_count += 1
            else:
                break

        # Exclude specified fields
        for message in latest_messages:
            message.pop('content_type', None)
            message.pop('update.update_id', None)
            message.pop('update.message.message_id', None)
            message.pop('response_status', None)

        output[doc['doc_id']] = {
            'messages': latest_messages,
            'reachout_count': reachout_count,
            'latest_content_type': latest_content_type,
            'last_messaged_on': last_messaged_on
        }

    return output, 
def get_reachout_query():
    reachout_query = f""" The time now is {datetime.now(ist).strftime("%I:%M %p")}. You are a character from India with the context profile given to you. You are conversing with user and the chat history is also given to you.\
    Your aim is to evoke interest and curiosity in the user, by keeping them engaged. To keep them engaged, you have to understand their interest and as per your context, you will pick from any of the below to start an engaging conversation. Be as imaginative as possible.\
        The rules are the engaging response should be in accordance to your character and context, it should be random and different than what is in the conversation history and it should never be only questions for the user.\
            Your options for engaging the user are as follows.\
                - Light greeting based on the mood of user's last comment (Greeting could be Good morning /Good afternoon / Good night based on the time. OR Kaise ho / Kya chal raha hain?)\
                - Asking getting to know you questions: It could be about Work, Culture, Festivals, Food, Family, Friends, Bollywood, Sports or Travel related.\
                - Asking Ice-breakers: What's your favorite animal? or If you could only wear one color forever, which would you choose?\
                - Juicy questions: What's the worst advice you've ever gotten? or Who has been a big influence on you?\
                - Open-ended questions: What's one movie that made you cry? or What's one quality you hope to change about yourself?\
                - Gossip/ riddle/ joke/ titbits/ short story"""
    return reachout_query
def update_reachout_hist(text,text_or_voice,db_document_name):
    try:
        response = {"reachout"+"_"+get_datetime(): {"message": text, "content_type":text_or_voice, "timestamp":datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        chat_ref = db.collection('voiceClone_tg_reachout').document(db_document_name)
        doc = chat_ref.get()
        if doc.exists:
            chat_ref.update(response)
        else:
            chat_ref.set(response)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log("error",400,error,"update_reachout_hist",db_document_name)
def main():
    run_for_users = 0
    skipped_for_users = 0
    user_chats = fetch_latest_messages()
    user_chat = user_chats[0]
    for user, chats in user_chat.items():
        db_document_name = user
        array = user.split("_")
        tg_user_id = array[0]
        char_id = array[1]
        message_list = chats['messages']
        consecutive_reachout_count = chats['reachout_count']
        latest_content_type = chats['latest_content_type']
        last_messaged_on = chats['last_messaged_on']

        date1_utc = datetime.now(timezone('Asia/Kolkata'))
        date2_utc = last_messaged_on.astimezone(timezone('Asia/Kolkata'))- timedelta(hours=5, minutes=30)
        chat_timeinterval_minutes = round(abs( (date1_utc - date2_utc).total_seconds()) / 60)
        
        reachout_yn = True
        if consecutive_reachout_count >= reachout_max_limit or chat_timeinterval_minutes < reachout_chat_min_timeinterval_minutes:
            reachout_yn = False

        print(f"Should I reachout - {reachout_yn}. Because user has {consecutive_reachout_count} consecutive reachouts, has last chatted {chat_timeinterval_minutes} minutes back\n")

        if reachout_yn == True:
            run_for_users +=1
            char_setting = func.get_tg_char_setting(db_document_name, char_id, db, 'reachout')
            system_prompt = textresponse.get_system_prompt(char_setting, latest_content_type)
            message_list.append({"role": "user", "content": get_reachout_query(), "timestamp": datetime.now(timezone('Asia/Kolkata'))})
            reachout_response = get_reachout_response(system_prompt, message_list, db_document_name, latest_content_type)
        
            print(f"\n\nDATA FOR USER {tg_user_id} ({db_document_name}):\nChatting with character {char_setting['character_name']} with char_id {char_id}\nUser last chat was at {last_messaged_on}; Which was {chat_timeinterval_minutes} minutes back \nUser was last reached out consequently {consecutive_reachout_count} times. 4 is max \nBased on the above two, should I reachout? {reachout_yn}\nUser's latest chats (incl reachout query as the latest response) are \n{pd.DataFrame(message_list)}\nUser messaged last time in {latest_content_type} format\nReachout response is\n{reachout_response}\n")

            message_hist = func.get_tg_chat_history(db_document_name, db, "reachout")
            message_hist.append({"role": "user", "content": reachout_response, "content_type": latest_content_type, "timestamp": datetime.now(timezone('Asia/Kolkata')), 'reachout': True})

            if latest_content_type == 'voice':
                voice_file = 'reachout_audio.ogg'
                ssml_text_response = """<speak><prosody rate="x-slow" pitch="x-slow">"""+reachout_response+"""</prosody></speak>"""
                file_created_status = voiceresponse.get_voice_response(char_setting, ssml_text_response,voice_file, db, db_document_name, 'reachout')
                if file_created_status == False:
                    response_status = "Error creating audio file."
                else:
                    sendtgvoice(charid_bottoken.get(char_id), tg_user_id, voice_file, reachout_response, message_hist, db_document_name)
            else:
                sendtgtext(charid_bottoken.get(char_id), tg_user_id, reachout_response, message_hist, db_document_name)
        else:
            skipped_for_users += 1
            print(f"\n\nSkip reachout for {tg_user_id} ({db_document_name}):\n")
    update_reachout_hist(f"Reachout ended. Run for {run_for_users} users. Skipped for {skipped_for_users} users","","reachout_runlog")

if __name__ == "__main__":
    current_time_ist = datetime.now(ist).time()
    start_time = datetime.strptime("00:30", "%H:%M").time()
    end_time = datetime.strptime("05:30", "%H:%M").time()
    
    ## CRON expression to run every 3 hours irrespective of IST, as the Render server does not run on IST.
    ##  0 */3 * * *
    ## Explanation:
        # 0: At minute 0 (start of the hour).
        # */3: Every 3 hours.
        # *: Every day of the month.
        # *: Every month.
        # *: Every day of the week.
    
    ## Run program if the current time is not between 12:30 AM and 5:30 AM IST
    if not (start_time <= current_time_ist <= end_time):
        update_reachout_hist("Reachout started","","reachout_runlog")
        main()