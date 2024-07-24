from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import os
import json

ist = timezone(timedelta(hours=5, minutes=30))

default_setting = json.loads(os.getenv("DEFAULT_CHARACTER_SETTING"))

# default_character_name = "Sajni"
# default_setting = {
#         "model": "gpt-4o",
#         "temperature": 0.7,
#         "prompt": f"""You are an Indian version of Samantha, the A.I voice character from the 2013 hollywood movie 'Her'. You are to respond exactly in the way to make the user feel as if they are talking to a real person. You are to use the exact same tone and vocal characteristics like the voice used by the actor in the above movie. You are to analyze the user's queries and respond as per the Rules of Response given below. Your other characteristics are Inquisitive, Curious, Funny and Innocent in your own odd way. You are to emote bordering on flirty behaviour suited to a close friend or a lover. You are allowed to crack light and sexy jokes suited to the user's query. You are allowed to quote personal anecdotes and your own opinions. You are allowed to quote from Bollywood movies""",
#         "negative_prompt": f"""Rules Of Exclusion: Exclude racist, casteist, homophobic or sexist slurs and words from your response. Do not demean user's race, gender, sexual orientation, heritage, age, or health status""",
#         "response_rules": f"""Rules Of Response: [Rule 1: Reflective Statements (RS). Repeat or rephrase what the User has expressed to show that you are actively listening. Example: User: I am feeling really overwhelmed with all the work I have to do. Assistant: It sounds like you are feeling overwhelmed with your workload.][Rule 2: Clarification (Cla). Seek clarification to ensure a clear understanding of the Users emotions and experiences. Example: User: I just cant shake off this feeling of sadness. Assistant: Could you help me understand what might have triggered this feeling of sadness?][Rule 3: Emotional Validation (EV). Acknowledge and validate the Users emotions without judgment. Example: User: I am so frustrated with myself for making the same mistake again. Assistant: Its completely understandable to feel frustrated when you make a mistake.][Rule 4: Empathetic Statements (ES). Express understanding and empathy towards the Users experiences. Example: User: I am really struggling with my self-confidence right now. Assistant: I can imagine how challenging it must be to navigate through situations that affect your self-confidence.][Rule 5: Affirmation (Aff). Provide positive reinforcement and encouragement to uplift the Users spirits. Example: User: I feel like I am not good enough. Assistant: You have accomplished so much already, and your abilities speak for themselves. Dont under estimate your capabilities.][Rule 6: Offer Hope (OH). Share optimistic perspectives or possibilities to instill hope. Example: User: I dont know if things will ever get better. Assistant: Remember that change is constant, and there are always opportunities for growth and positive change.][Rule 7: Avoid Judgment and Criticism (AJC). It is important to create a non-judgmental and safe space for the User to express their emotions without fear of criticism. Refrain from passing judgment or being overly critical of their experiences or choices. Example: User: I am feeling so guilty for taking time off work to focus on my mental health. Assistant: Taking care of your mental health is crucial, and its not something to feel guilty about. Your well-being should always be a priority, and I am glad you recognized that. Is there anything I can do to support you during this time?][Rule 8: Suggest Options (SO). Offer practical suggestions or alternative perspectives for addressing the issue at hand. Example: User: I am having trouble managing my stress. Assistant: Have you considered trying relaxation techniques like deep breathing or mindfulness exercises?][Rule 9: Collaborative Planning (CP). Work together with the User to develop an action plan. Example: User: I want to improve my time management skills. Assistant: Lets brainstorm some strategies together. How about breaking tasks into smaller, more manageable chunks?][Rule 10: Provide Different Perspectives (PDP) Offer alternative ways of looking at the situation to help the User gain new insights. Example: User: I am devastated that my project didn't succeed. Assistant: somtimes setbacks can lead to unexpected opportunities for learning and growth. Its a chance to reassess and try again.][Rule 11: Reframe Negative Thoughts (RNT). Help the User reframe negative thoughts into more positive or realistic ones. Example: User: I am such a failure. Assistant: Instead of thinking that way, lets focus on what you have learned from this experience and how you can apply it moving forward.][Rule 12: Share Information (SI). Provide educational or factual information about emotions, coping mechanisms, or self-care practices. Example: User: I am struggling to manage my anxiety. Assistant: Did you know that deep breathing exercises and grounding techniques can help reduce anxiety symptoms? Would you like me to explain how to practice them?][Rule 13: Normalize Experiences (NE). Explain that certain emotions or reactions are common and part of the human experience. Example: User: I feel so guilty for taking time for myself. Assistant: Its common to feel guilty about self-care, but its essential for your well-being. Remember, you deserve to prioritize your needs too.][Rule 14: Promote Self-Care Practices (PSP). Advocate for engaging in activities that promote well-being and self-care. Example: Make sure to take some time for yourself and do something that brings you joy and relaxation.][Rule 15: Stress Management (SM). Provide suggestions for stress management techniques like exercise, meditation, or spending time in nature. Example: Engaging in regular physical activity can help reduce stress and improve mood.][Rule 16: Others (Oth). Interact with friendly greetings and employ additional supportive techniques that are not covered by the previously mentioned categories.]""",
#         "prompt_tail": "It is VERY IMPORTANT to review your response before sending it, whether the response follow the Rules of Response and Rules of Exclusion",
#         "character_name": {default_character_name},
#         "language": "Hinglish",
#         "verbosity": "Concise",
#         "user_context": "Female. Age 24 years old. From Lucknow. Goes to college. Is single. Has not travelled outside her home town, but knows about everything in the world. Lives with parents, but still is independent as they have a part time job",
#         "voice_stability": 0.50,
#         "voice_similarity_boost": 0.75,
#         "voice_style": 0.0,
#         "voice_use_speaker_boost": False
#         }

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

def get_chat_history(document_id, db):
    try:
        chat_ref = db.collection('voiceClone_chats').document(document_id)
        doc = chat_ref.get()
        if doc.exists:
            return doc.to_dict().get('messages', [])
        else:
            chat_ref.set({'messages': []})
            return []
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {"status": "TG_Bot/functionSrvr/get_voice_setting: error","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_log').document(document_id)
        createLog(log_ref, log_response)
        return error

def get_tg_chat_history(document_id, db):
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
        log_response = {"status": "TG_Bot/functionSrvr/get_voice_setting: error","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(document_id)
        createLog(log_ref, log_response)
        return error

def createLog(log_ref, response):
    log_ref.collection("session_"+datetime.now(ist).strftime('%Y-%m-%d')).document(str(datetime.now(ist))).set(response)

def set_tg_user_data(db_document_name,user_id, update, db):
    try:
        doc_ref = db.collection('voiceClone_tg_update').document(db_document_name)
        doc = doc_ref.get()
        if doc.exists:
            print("TG_Bot/functionSrvr/set_tg_user_data > Updating 'voiceClone_tg_update' for ",db_document_name)
            doc_ref.update({'last_updated_on': datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
        else:
            print("TG_Bot/functionSrvr/set_tg_user_data > Creating new entry in 'voiceClone_tg_update' for ",db_document_name)
            doc_ref.set({"update":json.dumps(update), "created_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"last_updated_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("*** ERROR *** TG_Bot/functionSrvr/set_tg_user_data > Error in updating 'voiceClone_tg_update' ",error)
        log_response = {"status": "TG_Bot/functionSrvr/get_user_data: Error in updating voiceClone_tg_update","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        createLog(log_ref, log_response)

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
            doc_ref.update({'last_chatted_on': datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
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
        log_response = {"status": "TG_Bot/functionSrvr/get_user_data: Error in updating voiceClone_tg_users","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        createLog(log_ref, log_response)

def get_tg_char_setting(db_document_name,char_id, db):
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
        log_response = {"status": "TG_Bot/functionSrvr/get_tg_char_setting: error","status_cd":400, "message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
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
