import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timedelta
import pandas as pd

cred = credentials.Certificate("firestore_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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
    return df

def download_tg_characters():
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
    columns = ['char_id', 'character_descr', 'last_updated_on', 'name', 'character_descr', 'character_name', 'frequency_penalty', 'language', 'length_penalty', 'max_tokens','min_tokens','model','negative_prompt','presence_penalty','prompt','prompt_tail','repetition_penalty','response_rules','temperature','top_k','top_p','user_context','verbosity','voice_id','voice_similarity_boost','voice_stability','voice_style','voice_use_speaker_boost','voice_id']
    df = pd.DataFrame(data, columns=columns)
    return df

def process_messages(messages):
    processed_messages = []
    for message in messages:
        processed_message = message.copy()
        if 'timestamp' in processed_message:
            firestore_timestamp = processed_message['timestamp']
            if isinstance(firestore_timestamp, datetime):
                firestore_timestamp = firestore_timestamp + timedelta(hours=5, minutes=30)
                processed_message['timestamp'] = firestore_timestamp.replace(tzinfo=None)
            else:
                dt = firestore_timestamp.to_datetime()
                processed_message['timestamp'] = dt.replace(tzinfo=None)
        processed_messages.append(processed_message)
    return processed_messages

def download_tg_chat():
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
    collection_ref = db.collection('voiceClone_tg_logs')
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
    return df

# def download_tg_log1():
#     print(f"log 1")
#     collection_name = 'voiceClone_tg_logs'
#     main_collection_ref = db.collection(collection_name)
#     main_collection_docs = main_collection_ref.stream()
#     print(f"main_collection_docs:{main_collection_docs}")
#     data = []
#     for doc in main_collection_docs:
#         print(f"Processing document:{doc}")
#         document_id = doc.id
#         print(f"Processing document_id:{document_id}")
#         nested_collections = db.collection(collection_name).document(document_id).collections()
#         for nested_collection in nested_collections:
#             for nested_doc in nested_collection.stream():
#                 timestamp = nested_doc.id
#                 doc_data = nested_doc.to_dict()
#                 # Create a record with all relevant fields
#                 record = {
#                     'document_id': document_id,
#                     'timestamp': timestamp,
#                     'message': doc_data.get('message', None),
#                     'status': doc_data.get('status', None),
#                     'status_cd': doc_data.get('status_cd', None),
#                     'update.effective_chat.id': doc_data.get('update.effective_chat.id', None),
#                     'update.message.message_id': doc_data.get('update.message.message_id', None),
#                     'update.update_id': doc_data.get('update.update_id', None)
#                 }
#                 data.append(record)

#     columns = ['document_id', 'timestamp', 'message', 'status', 'status_cd', 'update.effective_chat.id', 'update.message.message_id', 'update.update_id']
#     df = pd.DataFrame(data, columns=columns)
#     return df

# def save_dataframe_to_csv(df):
#     csv_file_path = 'usage_rpt/voiceClone_tg_users'+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'.csv'
#     df.to_csv(csv_file_path, index=False)
def save_dataframes_to_excel(df1,s1,df2,s2,df3,s3,df4,s4):
    file_path = 'usage_rpt/telegram_usage_report_'+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'.xlsx'
    with pd.ExcelWriter(file_path) as writer:
        df1.to_excel(writer, sheet_name=s1, index=False)
        df2.to_excel(writer, sheet_name=s2, index=False)
        df3.to_excel(writer, sheet_name=s3, index=False)
        df4.to_excel(writer, sheet_name=s4, index=False)

# save_dataframes_to_excel(download_tg_users(),'users',download_tg_characters(),'characters',download_tg_chat(),'chats',download_tg_logs(),'error_logs')
# print(f"Report generated")
# download_tg_log1()

# db.collection('users').doc(user_id).set({foo:'bar'}, {merge: true})
