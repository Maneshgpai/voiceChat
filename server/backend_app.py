import os
from flask import Flask, jsonify, request, make_response, Response, stream_with_context
from flask_cors import CORS
import json
import base64
from google.cloud import firestore
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta, timezone
from celery import Celery
from functions import textResponseSrvr as textresponse
from functions import functionSrvr as func

load_dotenv(find_dotenv())

from google.cloud import firestore
db = firestore.Client.from_service_account_json("firestore_key.json")
ist = timezone(timedelta(hours=5, minutes=30))

app = Flask(__name__)
CORS(app)
app.config['CELERY_BROKER_URL'] = os.getenv("CELERY_BROKER_URL")
app.config['CELERY_RESULT_BACKEND'] = os.getenv("CELERY_RESULT_BACKEND")
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
voice_id = os.getenv("DEFAULT_VOICE_ID")
celery.conf.update(app.config)

@celery.task
def create_workoutplan_async(phone_number,profile_data):
    async_response = createprofile.create_workoutplan(phone_number,profile_data)
    return async_response

@app.route("/api", methods=['GET'])
def home():
    return jsonify({"message": "You have reached an unavailable URL!"})

@app.route("/api/mockchat", methods=["POST"])
def mockchat():
    document_id = ""
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        user_query = data.get('user_query')
        voice_settings = data.get('voice_setting')
        user_query_timestamp = data.get('user_query_timestamp')

        ## Getting Firebase document ID
        user_name, document_id = func.get_user_info(telegram_id, db)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********BackendAPI >> mock_chat API >> Telegram:{telegram_id}, Query:{user_query}, user_name:{user_name}, document_id:{document_id}")
        
        ## Getting Chat history
        message_hist = func.get_chat_history(document_id, db)
        ## Appending latest query to history 
        message_hist.append({"role": "user", "content": user_query, "timestamp": user_query_timestamp,"source":"chat"})

        ## Getting Bot response
        text_response = textresponse.get_agent_response(voice_settings, message_hist)
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********BackendAPI >> mock_chat API >> Response by bot is {text_response}")
                
        ## Setting up HTTP response
        status_cd = 200
        response = {"status": "Success","status_cd": status_cd,"message": text_response}
        log_response = {"message": "Chat API > Bot responded successfully","status_cd":status_cd,"bot_message": text_response,"user_message":user_query, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}

        ## Collating query & response to chat history, to add to Firebase DB 
        message_hist.append({"role": "assistant", "content": text_response, "timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"source":"chat"})
    except Exception as e:
        error = "Error: {}".format(str(e))
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********BackendAPI >> mock_chat API >> ERROR {error}")
        text_response = error
        status_cd = 400
        log_response = {"status": "Chat API > Error in Chat API call","status_cd":status_cd, "message": error,"user_message":user_query, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        response = {"status": "Error","status_cd":status_cd,"message": error}

    ## Logging start ##
    log_ref = db.collection('voiceClone_log').document(document_id)
    func.createLog(log_ref, log_response)
    ## Logging stop ##

    ## Adding chat history to Firebase DB 
    chat_ref = db.collection('voiceClone_chats').document(document_id)
    if not chat_ref.get().exists:
        chat_ref.set({'messages': []})
    chat_ref.update({"messages": firestore.ArrayUnion(message_hist)})

    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********BackendAPI >> mock_chat API >> End statement in Backend API")
    return jsonify(response), status_cd

@app.route("/api/create_profile", methods=["POST"])
def create_profile():
    try:
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}**********Entered CREATE_PROFILE API") ## [user_health_profile, lang, workoutplan]
        data = request.json
        phone_number = data.get('phone_number')
        profile_data = data.get('profile_data')
        whatsapp_optin_flag = data.get('whatsapp_optin')
        
        ## Save profile to DB
        db.collection('users').document(phone_number).set({"timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"action":"create_profile","profile":profile_data,"Has User given consent for Whatsapp?":whatsapp_optin_flag})

        phone_log_ref = db.collection('log').document(phone_number)
        ## Logging start ##
        resp = {"message": "Saved profile to DB","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        func.createLog(phone_log_ref, resp)
        ## Logging stop ##

        task = create_workoutplan_async(phone_number,profile_data)

        ## Logging start ##
        resp = {"message": "Backend api >> Workout plan created successfully","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        func.createLog(phone_log_ref, resp)
        ## Logging stop ##

        # response = {"status": "Triggered profile creation task","status_cd":200,"message": "Profile is being generated. You will recieve a message once this is complete","timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
    except Exception as e:
        error = "Error: {}".format(str(e))
        response = {"status": "Error in api create_profile","status_cd":400,"message": error,"timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        ## Logging start ##
        func.createLog(phone_log_ref, response)
        ## Logging stop ##

    

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000, debug=False) ### For Render
    app.run(debug=True, port=8080) ### For Local host
    # app.run(port=8080) ### For Local host

