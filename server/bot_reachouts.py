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
from datetime import datetime, timedelta, timezone as tz
from dotenv import load_dotenv
import telegram
import json
from google.cloud import firestore
import pandas as pd
from functions import functionSrvr as func
from functions import textResponseSrvr as textresponse
from functions import voiceResponseSrvr as voiceresponse
from openai import OpenAI
import replicate



load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
ist = timezone("Asia/Kolkata")
db = firestore.Client.from_service_account_json("firestore_key.json")

## reachout parameters
latest_messages_to_check = int(os.getenv("REACHOUT_LATEST_MSG_TO_CHECK"))
reachout_max_limit = int(os.getenv("REACHOUT_MAX_LIMIT"))
reachout_chat_min_timeinterval_minutes = int(os.getenv("REACHOUT_CHAT_MIN_TIMEINTERVAL_MIN"))

def get_datetime():
    return (str(datetime.now())).replace('.','').replace(':','').replace(' ','').replace('-','')
def log(status,status_cd,message,origin,db_document_name):
    log_response = {"reachout"+"_"+get_datetime(): {"status": status,"status_cd":status_cd,"message":message, "origin":origin, "reachout": True, "timestamp":datetime.now(ist)}}
    log_ref = db.collection('voiceClone_tg_logs').document(db_document_name)
    func.createLog(log_ref, log_response)
def update_chat_hist(message_hist,db_document_name, msg_id):
    try:
        chat_ref = db.collection('voiceClone_tg_chats').document(db_document_name)
        if not chat_ref.get().exists:
            chat_ref.set({'messages': []})
        chat_ref.update({"messages": firestore.ArrayUnion(message_hist)})
    except Exception as e:
        error = "Error: {}".format(str(e))
        log("error",400,error,"reachout.update_chat_hist",db_document_name)
def sendtgtext(token, tg_user_id, text, message_hist, db_document_name ):
    try:
        bot = telegram.Bot(token=token)
        # bot.send_chat_action(chat_id=tg_user_id,action=telegram.ChatAction.TYPING)
        bot.send_message(chat_id=tg_user_id, text=text)
        update_chat_hist(message_hist,db_document_name, "reachout")
        update_reachout_hist(text,'text',db_document_name)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log("error",400,error,"text.reachout.sendtgtext",db_document_name)
def sendtgvoice(token, tg_user_id, voice, text, message_hist, db_document_name):
    try:
        bot = telegram.Bot(token=token)
        # bot.send_chat_action(chat_id=tg_user_id,action=telegram.ChatAction.RECORD_AUDIO)
        with open(voice, 'rb') as voice_file:
            bot.send_voice(chat_id=tg_user_id, voice=voice_file)
        update_chat_hist(message_hist,db_document_name, "reachout")
        update_reachout_hist(text,'voice',db_document_name)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log("error",400,error,"voice"+".reachout.sendtgvoice",db_document_name)
def get_reachout_response(system_prompt,message_hist, db_document_name, voice_or_text):
    try:
        # user_message = textresponse.fetch_optimized_chat_hist_for_openai(message_hist)
        # system_message = [{"role": "system", "content": system_prompt}]
        # response = client.chat.completions.create(
        #     model='gpt-4o-mini',
        #     messages=system_message+user_message,
        #     stream=False,
        #     frequency_penalty = 1.2,
        #     max_tokens = 200,
        #     top_p = 0.5,
        #     presence_penalty = 1.5,
        #     temperature=1.2,
        # )
        # full_response = response.choices[0].message.content

        final_prompt = system_prompt.replace("\n","\\n")
        new_message_hist = textresponse.fetch_optimized_chat_hist_for_llama(message_hist)
        full_text = []
        for event in replicate.stream(
                "meta/meta-llama-3-70b-instruct",
                input={
                    "top_k": 60,
                    "top_p": 0.90,
                    "prompt": new_message_hist,
                    "max_tokens": 100,
                    "min_tokens": 10,
                    "temperature": 0.95,
                    "system_prompt": final_prompt,
                    "length_penalty": 0.60,
                    "stop_sequences": "<|end_of_text|>,<|eot_id|>",
                    "prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_prompt}<|eot_id|>{prompt}<|start_header_id|>assistant<|end_header_id|>",
                    "presence_penalty": 1.50,
                    "frequency_penalty": 1.20,
                    "repetition_penalty": 1.80,
                    "log_performance_metrics": False
                },
            ):
                full_text.append(str(event))
        full_response = ''.join(full_text)
        return full_response
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print(f"response:{response}")
        log("error",400,error,voice_or_text+".get_reachout_response",db_document_name)
def convert_ts(timestamp):
    # print(f"timestamp:{timestamp}")
    # print(f"type:{type(timestamp)}")
    if not(isinstance(timestamp, datetime)):
        format = '%Y-%m-%d %H:%M:%S'
        dt = datetime.strptime(timestamp, format)
        timestamp = dt.replace(tzinfo=tz.utc)
    return timestamp
def sort_messages_by_ts(all_docs):
    # print(f"************len(all_docs): {len(all_docs)}")
    # for doc in all_docs:
    #     print(doc['doc_id'])
    #     # print(doc['messages'])
    #     for msg in doc['messages']:
    #         print(convert_ts(msg.get('timestamp','')))

    all_docs.sort(key=lambda x: max(convert_ts(msg.get('timestamp','')) for msg in x['messages']), reverse=True)
    # latest_docs = all_docs[:3]

    # docs_with_latest_timestamps = []
    # for doc in all_docs:
    #     latest_timestamp = max(convert_ts(message['timestamp']) for message in doc['messages'])
    #     docs_with_latest_timestamps.append((latest_timestamp, doc))
    # docs_with_latest_timestamps.sort(key=lambda x: x[0], reverse=True)
    # # Extract the sorted documents from the tuples
    # all_docs_sorted = [doc for _, doc in docs_with_latest_timestamps]
    # # latest_docs = all_docs[:3]
    return all_docs
def fetch_latest_messages():
    all_docs = []
    collection_ref = db.collection('voiceClone_tg_chats')

    for doc in collection_ref.stream():
        doc_id = doc.id
        doc_data = doc.to_dict()
        if 'messages' in doc_data:
            messages = doc_data['messages']
            for message in messages:
                if 'timestamp' in message and isinstance(message['timestamp'], datetime):
                    message['timestamp'] += timedelta(hours=5, minutes=30)
                message.pop('content_type', None)
                message.pop('update.update_id', None)
                message.pop('update.message.message_id', None)
                message.pop('response_status', None)

            if len(messages) != 0:
                all_docs.append({'doc_id': doc_id, 'messages': messages})

    latest_docs = sort_messages_by_ts(all_docs)
    
    output = {}
    for doc in latest_docs:
        sorted_messages = sorted(doc['messages'], key=lambda x: convert_ts(x['timestamp']), reverse=True)
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

        output[doc['doc_id']] = {
            'messages': latest_messages,
            'reachout_count': reachout_count,
            'latest_content_type': latest_content_type,
            'last_messaged_on': last_messaged_on
        }
    # print(f"type of output: {type(output)}")
    return output

# def get_reachout_query():
#     # reachout_query1 = f""" You are from India. Your background is available in the 'system prompt' given here. You are conversing with the user and the chat history is also here.\
#     # Your aim is to evoke interest and curiosity in the user, by keeping them engaged. To keep them engaged, you have to understand their interest and as per your context, you will pick from any of the below to start an engaging conversation. Be as imaginative as possible.
    
#     # Rules of the response:
#     # 1. The response should be highly engaging for the user.
#     # 2. The response should be strictly in accordance to your character and context.
#     # 3. It should only be a point to engage user in conversation.\
    
#     # Your options for engaging the user are as follows. You can decide which one to use to increase the egagement, as per the time right now {datetime.now(ist).strftime("%I:%M %p")}. \
#     # - Check if the chat history has a content/ subject which will be interesting enough to initate a conversation. You are allowed to do this only if the subject is enough interesting to be talked abaout again. You will think like a good friend of the user and then judge this.
#     # - If not the chat history, the take any of the below options ramdomly and suited the current time:
#     #     1. Light greeting based on the mood of user's last comment (Greeting could be Good morning /Good afternoon / Good night based on the time. OR Kaise ho / Kya chal raha hain?)\
#     #     2. Asking getting to know you questions: It could be about Work, Culture, Festivals, Food, Family, Friends, Bollywood, Sports or Travel related.\
#     #     3. Asking Ice-breakers: What's your favorite animal? or If you could only wear one color forever, which would you choose?\
#     #     4. Juicy questions: What's the worst advice you've ever gotten? or Who has been a big influence on you?\
#     #     5. Open-ended questions: What's one movie that made you cry? or What's one quality you hope to change about yourself?\
#     #     6. Gossip/ riddle/ joke/ titbits/ short story"""

#     reachout_query = f"""Your mission is to keep the user engaged by sparking their interest and curiosity. You have access to the chat history and background context provided, which you can use to guide your responses.
# Objective: Engage the user in a conversation that is highly interesting and relevant, following these key rules:
#     1 Be Engaging: Your response should captivate the user's attention.
#     2 Stay in Character: Your response must align with your designated persona and the context provided.
#     3 Initiate Conversation: The goal is to start a conversation that keeps the user involved.
# Options for Engagement:
#     1 Review Chat History: If there's a topic from the chat history that's particularly engaging, revisit it. Think like a close friend and assess if it's worth discussing again.
#     2 If Not Using Chat History: Choose one of the following strategies based on the current time ({datetime.now(ist).time()}):
#         ◦ Light Greeting: Tailor your greeting to the user's last mood or the current time (e.g., "Good morning," "Kaise ho?").
#         ◦ Fun Elements: Consider adding a riddle, joke, short story, or gossip to spice up the conversation.
#         ◦ Getting to Know You: Ask about work, culture, festivals, food, family, friends, Bollywood, sports, or travel.
#         ◦ Ice-breakers: Pose a fun question like, "What's your favorite animal?" or "If you could wear one color forever, which would it be?"
#         ◦ Juicy Questions: Stir interest with questions like, "What's the worst advice you've ever received?" or "Who has influenced you the most?"
#     3 Open-ended Questions: Encourage deeper conversation with prompts like, "What's one movie that made you cry?" or "What's one quality you hope to change about yourself?"""
#     return reachout_query

def update_reachout_hist(text,text_or_voice,db_document_name):
    try:
        response = {"reachout"+"_"+get_datetime(): {"message": text, "content_type":text_or_voice, "timestamp":datetime.now(ist)}}
        chat_ref = db.collection('voiceClone_tg_reachout').document(db_document_name)
        doc = chat_ref.get()
        if doc.exists:
            chat_ref.update(response)
        else:
            chat_ref.set(response)
    except Exception as e:
        error = "Error: {}".format(str(e))
        log("error",400,error,"update_reachout_hist",db_document_name)

def get_character_dtls():
    print("Downloading Character data...")
    collection_ref = db.collection('voiceClone_characters')
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

def main():
    print(f"\n\n\n")
    run_for_users = 0
    skipped_for_users = 0

    ## Fetch TG_Tokens and reachout_prompt for every character
    charid_bottoken, charid_prompt = get_character_dtls()
    # charid_bottoken = json.loads(os.getenv("REACHOUT_CHARID_BOT_TOKEN"))
    # charid_prompt = json.loads(os.getenv("REACHOUT_CHARID_BOT_TOKEN"))

    user_chats = fetch_latest_messages()
    log_message = []
    for user, chats in user_chats.items():
        print(f"Processing {user}")
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
        
        ## Check if reachout needed or not
        reachout_yn = True
        if consecutive_reachout_count >= reachout_max_limit or chat_timeinterval_minutes < reachout_chat_min_timeinterval_minutes:
            reachout_yn = False

        ## Comment for GO LIVE
        # if tg_user_id == '7142807432' or tg_user_id == '6733334932':
        #     reachout_yn = True
        # else:
        #     reachout_yn = False

        print(f"{tg_user_id} chatting with character with char_id {char_id} (db_document_name:{db_document_name})\nUser last chat was at {last_messaged_on}; Which was {chat_timeinterval_minutes} minutes back \nUser was last reached out consequently {consecutive_reachout_count} times.\nRules of reachout are that there should be a minimum {reachout_chat_min_timeinterval_minutes} minutes between chats and only send reachout {reachout_max_limit} times.\nBased on the above two, should I reachout? {reachout_yn}\nUser messaged last time in {latest_content_type} format")


        log_message.append({db_document_name : [f"{tg_user_id} chatting with character with char_id {char_id} (db_document_name:{db_document_name})\nUser last chat was at {last_messaged_on}; Which was {chat_timeinterval_minutes} minutes back \nUser was last reached out consequently {consecutive_reachout_count} times.\nRules of reachout are that there should be a minimum {reachout_chat_min_timeinterval_minutes} minutes between chats and only send reachout {reachout_max_limit} times.\nBased on the above two, should I reachout? {reachout_yn}\nUser messaged last time in {latest_content_type} format"]})

        if reachout_yn == True:
            reachout_prompt = ""
            run_for_users +=1
            char_setting = func.get_tg_char_setting(db_document_name, char_id, db, 'reachout')
            system_prompt = textresponse.get_system_prompt(char_setting, latest_content_type)
            for key, value in enumerate(charid_prompt):
                for k, v in value.items():
                    if k == char_id:
                        reachout_prompt = v
            reachout_prompt = reachout_prompt + f"""\nThe time now is {datetime.now(ist).time()}"""
            print(f"################## Reachout prompt:{reachout_prompt}")


            message_list.append({"role": "user", "content": reachout_prompt, "timestamp": datetime.now(timezone('Asia/Kolkata'))})
            reachout_response = get_reachout_response(system_prompt, message_list, db_document_name, latest_content_type)
            reachout_response = reachout_response.replace("\n"," ")
            print(f"################## reachout_response:{reachout_response}")
            message_hist = func.get_tg_chat_history(db_document_name, db, "reachout")
            message_hist.append({"role": "user", "content": reachout_response, "content_type": latest_content_type, "timestamp": datetime.now(timezone('Asia/Kolkata')), 'reachout': True})


            bot_token = ""
            for key, value in enumerate(charid_bottoken):
                for k, v in value.items():
                    if k == char_id:
                        bot_token = v
            print(f"################## bot_token:{bot_token}")

            if latest_content_type == 'voice':
                voice_file = 'reachout_audio.ogg'
                ssml_text_response = """<speak><prosody rate="x-slow" pitch="x-slow">"""+reachout_response+"""</prosody></speak>"""
                file_created_status = voiceresponse.get_voice_response(char_setting, ssml_text_response,voice_file, db, db_document_name, 'reachout')
                if file_created_status == False:
                    response_status = "Error creating audio file."
                else:
                    sendtgvoice(bot_token, tg_user_id, voice_file, reachout_response, message_hist, db_document_name)
            else:
                sendtgtext(bot_token, tg_user_id, reachout_response, message_hist, db_document_name)
            print(f"\n\n\n")
        else:
            skipped_for_users += 1
            print(f"Skip reachout for {tg_user_id} ({db_document_name})")
            print(f"\n\n\n")

    update_reachout_hist(f"Reachout ended. Run for {run_for_users} users. Skipped for {skipped_for_users} users",log_message,"reachout_runlog")

if __name__ == "__main__":
    current_time_ist = datetime.now(ist).time()
    start_time = datetime.strptime("12:30", "%H:%M").time()
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
