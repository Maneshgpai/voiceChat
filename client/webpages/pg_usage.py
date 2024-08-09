import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timedelta
import pandas as pd
import pygsheets
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

if "firestore_db" not in st.session_state:
    db = firestore.Client.from_service_account_json("firestore_key.json")
else:
    db = st.session_state["firestore_db"]
google_client = pygsheets.authorize(service_file="firestore_key.json")


def convert_ts(timestamp):
    # print(f"timestamp:{timestamp}")
    if isinstance(timestamp, datetime):
        # print(f"Data type is datetime!")
        timestamp += timedelta(hours=5, minutes=30)                
        timestamp = timestamp.replace(tzinfo=None)
    else:
        # print(f"Data type is string!")
        format = '%Y-%m-%d %H:%M:%S'
        dt = datetime.strptime(timestamp, format)
        timestamp = dt.replace(tzinfo=None)
    return timestamp

def process_messages(messages):
    processed_messages = []
    for message in messages:
        processed_message = message.copy()
        if 'timestamp' in processed_message:
            firestore_timestamp = processed_message['timestamp']
            processed_message['timestamp'] = convert_ts(firestore_timestamp)
        processed_messages.append(processed_message)
    return processed_messages

def download_tg_users():
    collection_ref = db.collection('voiceClone_tg_users')
    docs = collection_ref.stream()
    data = []
    for doc in docs:
        doc_id = doc.id
        array = doc_id.split("_")
        doc_data = doc.to_dict()
        doc_data['document_id'] = doc_id
        doc_data['tg_user_id'] = array[0]
        doc_data['char_id'] = array[1]
        data.append(doc_data)
    columns = ['document_id', 'tg_user_id', 'char_id', 'created_on', 'first_name', 'id', 'is_bot', 'language_code', 'last_chatted_on', 'last_name', 'last_updated_on', 'username']
    df = pd.DataFrame(data, columns=columns)
    print("Downloading User data...")
    return df

def download_tg_characters():
    print("Downloading Character data...")
    collection_ref = db.collection('voiceClone_characters')
    docs = collection_ref.stream()
    data = []
    for doc in docs:
        doc_id = doc.id
        doc_data = doc.to_dict()
        doc_data['char_id'] = doc_id
        settings = doc_data.pop('setting', {})
        for key, value in settings.items():
            doc_data[key] = value
  
        data.append(doc_data)
    columns = ['char_id', 'character_descr', 'last_updated_on', 'name', 'character_name', 'frequency_penalty', 'language', 'length_penalty', 'max_tokens','min_tokens','model','negative_prompt','presence_penalty','prompt','prompt_tail','repetition_penalty','response_rules','temperature','top_k','top_p','user_context','verbosity','voice_id','voice_similarity_boost','voice_stability','voice_style','voice_use_speaker_boost']
    df = pd.DataFrame(data, columns=columns)
    return df

def download_tg_chat():
    print("Downloading chat data...")
    collection_ref = db.collection('voiceClone_tg_chats')
    docs = collection_ref.stream()
    data = []
    for doc in docs:
        doc_id = doc.id
        doc_data = doc.to_dict()
        messages = doc_data.get('messages', [])
        processed_messages = process_messages(messages)        
        for message in processed_messages:
            message['document_id'] = doc_id
            array = doc_id.split("_")
            message['tg_user_id'] = array[0]
            message['char_id'] = array[1]
            data.append(message)
    columns = ['document_id', 'tg_user_id', 'char_id', 'content', 'timestamp', 'role', 'content_type', 'response_status','update.message.message_id','update.update_id']
    df = pd.DataFrame(data, columns=columns)
    return df

def download_tg_logs():
    print("Downloading log data...")
    data = []
    collection_ref = db.collection('voiceClone_tg_logs')
    for doc in collection_ref.stream():
        doc_id = doc.id
        array = doc_id.split("_")
        tg_user_id = array[0]
        char_id = array[1]
        doc_data = doc.to_dict()
        for key, value in doc_data.items():
            # print(f"doc_id: {doc_id}\nkey:{key}\nvalue:{value}")
            # if key=='timestamp' or key=='message' or key=='message_id' or key=='origin' or key=='status' or key=='status_cd':
            if value.get('timestamp') or value.get('message') or value.get('message_id') or value.get('origin') or value.get('status') or value.get('status_cd'):
                data.append({
                    'document_id': doc_id,
                    'tg_user_id': tg_user_id,
                    'char_id': char_id,
                    'message': value.get('message', None),
                    'message_id': value.get('message_id', None),
                    'origin': value.get('origin', None),
                    'status': value.get('status', None),
                    'status_cd': value.get('status_cd', None),
                    'timestamp': convert_ts(value.get('timestamp', None)),
                })
            else:
                for k,v in value.items():
                    # print(f"doc_id: {doc_id}\nk:{k}\nv:{v}\n\n")
                    data.append({
                        'document_id': doc_id,
                        'tg_user_id': tg_user_id,
                        'char_id': char_id,
                        'message': v.get('message', None),
                        'message_id': v.get('message_id', None),
                        'origin': v.get('origin', None),
                        'status': v.get('status', None),
                        'status_cd': v.get('status_cd', None),
                        'timestamp': convert_ts(v.get('timestamp', None)),
                    })
    columns = ['document_id', 'tg_user_id', 'char_id', 'message', 'message_id', 'origin', 'status', 'status_cd', 'timestamp']
    df = pd.DataFrame(data, columns=columns)
    return df

def export_file(df1,s1,df2,s2,df3,s3,df4,s4):
    spreadsheet_id = os.getenv("USAGE_RPT_SPREADSHEET_ID")
    sh = google_client.open_by_key(spreadsheet_id)
    
    # sh.add_worksheet(s1)
    wks_write = sh.worksheet_by_title(s1)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df1, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1

    # sh.add_worksheet(s2)
    wks_write = sh.worksheet_by_title(s2)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df2, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1

    # sh.add_worksheet(s3)
    wks_write = sh.worksheet_by_title(s3)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df3, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1

    # sh.add_worksheet(s4)
    wks_write = sh.worksheet_by_title(s4)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df4, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1

    # print("Exporting to file...")
    # file_path = 'usage_rpt/telegram_usage_report_'+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'.xlsx'
    # with pd.ExcelWriter(file_path) as writer:
    #     df1.to_excel(writer, sheet_name=s1, index=False)
    #     df2.to_excel(writer, sheet_name=s2, index=False)
    #     df3.to_excel(writer, sheet_name=s3, index=False)
    #     df4.to_excel(writer, sheet_name=s4, index=False)
    return True

st.subheader(f"Generate Usage Report")
generate_report = st.button("Generate Usage Report")
if generate_report:
    with st.spinner('Generating report...'):
        try:
            flag = export_file(download_tg_users(),'users',download_tg_characters(),'characters',download_tg_chat(),'chats',download_tg_logs(),'error_logs')
            if (flag):
                st.success("Report generated: https://docs.google.com/spreadsheets/d/1PxbQlTAcl2qRTAXu8MU7M0IF0uWjgS_9gJhQMTvHupA/edit?usp=sharing")
        except Exception as e:
            error = "Error: {}".format(str(e))
            st.error(error)

