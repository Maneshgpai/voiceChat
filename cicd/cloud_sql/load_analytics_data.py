from firebase_admin import credentials, firestore
import pandas as pd
import pygsheets
from dotenv import load_dotenv, find_dotenv
import os
# from google.cloud.sql.connector import Connector
import sqlalchemy
# from sqlalchemy.types import NVARCHAR
# from sqlalchemy import create_engine
# import pymysql
import mysql.connector
from datetime import datetime, timedelta, timedelta
from openai import OpenAI
from datetime import datetime
import pytz

load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
firestore_json_file = "../firebase/cred_cert/prod_serviceAccountKey.json"
db = firestore.Client.from_service_account_json(firestore_json_file)
# connector = Connector()
google_client = pygsheets.authorize(service_file=firestore_json_file)
spreadsheet_id = os.getenv("USAGE_RPT_SPREADSHEET_ID")
now_utc = datetime.now(pytz.utc)
ist_timezone = pytz.timezone('Asia/Kolkata')
now_ist = now_utc.astimezone(ist_timezone)

# def getconn():
#     conn = connector.connect(
#         os.environ.get("INSTANCE_CONNECTION_NAME"),
#         "pytds",
#         user=os.environ.get("DB_USER"),
#         password=os.environ.get("DB_PASS"),
#         db=os.environ.get("DB_NAME")
#     )
#     return conn
# pool = sqlalchemy.create_engine(
#     "mssql+pytds://",
#     creator=getconn,
# )

# def getconn():
#     conn = connector.connect(
#         os.environ.get("INSTANCE_CONNECTION_NAME"),
#         "pymysql",
#         user=os.environ.get("DB_USER"),
#         password=os.environ.get("DB_PASS"),
#         db=os.environ.get("DB_NAME")
#     )
#     return conn
# pool = sqlalchemy.create_engine(
#     "mssql+pymysql://",
#     creator=getconn,
# )

# mysql+<drivername>://<username>:<password>@<server>:<port>/dbname
connection_string = "mysql+mysqlconnector://"+os.environ.get("DB_USER")+":"+os.environ.get("DB_PASS")+"@"+os.environ.get("INSTANCE_CONNECTION_NAME")+":"+os.environ.get("DB_PORT")+"/"+os.environ.get("DB_NAME")
pool = sqlalchemy.create_engine(connection_string, echo=False)
# pool = create_engine("mysql+mysqlconnector://admin:Dontfuckup_682038@35.200.186.51:3306/mitrrs_analytics", echo=True)
# connection = pool.connect()
# result = connection.execute("SELECT * from test_tab1")
# print(result)

# connection = mysql.connector.connect(
#     host=os.environ.get("INSTANCE_CONNECTION_NAME"),
#     user=os.environ.get("DB_USER"),
#     password=os.environ.get("DB_PASS"),
#     database=os.environ.get("DB_NAME"),
#     port=3306
# )

# cursor = connection.cursor()
# cursor.execute("SELECT DATABASE();")

# # Fetch result
# database_name = cursor.fetchone()
# print(f"You're connected to the database: {database_name}")

# # Close the connection
# cursor.close()
# connection.close()

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
def get_chat_analysis_prompt():
    system_prompt = """You are an expert in analysing chats between user and assistant. You will create one or multiple word tags which will help categorize each conversation.
You are given the MESSAGE CONVERSATIONS, which will have below fields:
1. role: This attribute captures whether the chat content is from user or from assistant
2. content: This attribute captures whether the content of chat. It will be either a request from user or response from assistant.\
3. timestamp: This attribute captures the timestamp of the request or response
These are the aspects you will consider to generate word tags. You will not seperate the word tags based on these assumptions. But rather, will create 
1. Tags to summarize the user chat.
2. Tags to capture user requests like song,call,picture,video,phone_nbr,address,IG-handle etc.
3. Tags to capture the topics which user talked about. If there is nothing to capture, you don't have to populate the tag. 

You will follow below rules while generating tags
1. You can create tags on your own which are apt to capture the summary or user ask
2. You can have one or multiple tags as you feel necessary to capture the essense of summary or user ask.
3. Do not include examples from the chat.
4. Only include word tags in your response. Do not include explanation or title or summary or any other text, apart from word tags.
5. Follow the below format for response, but you are allowed to generate your own word tags as per the chat content.
example 1: explicit,casual conversation,personal conversation,asked picture,flirting
example 2: shared name,shared favourite food,asked picture,felt bored,asked video
example 3: friendship proposal,fantasy discussion,roleplay,testing the product,felt frustrated,indepth conversation
example 4: zero messages
example 5: less than 5 messages
example 6: felt bored,irritated requests
example 7: indepth conversation,expressed happiness
example 8: indepth conversation,expressed satisfaction
MESSAGE CONVERSATIONS:"""
    return system_prompt
def load_tg_chat_analytics(df):
    ## Exclude Reachouts from assistant
    df = df[df['reachout'] != True]

    ## Keep only 4 columns which are needed for LLM categorization: document_id, content, timestamp, role
    df_chat = df.drop(df.columns[[4,5,6,7,8]], axis=1)

    # selecting sample data ste for testing
    sel_doc_id = ['1136386025_bPm741abegxqm3t7rfeB','1323078100_IJfd3UlnIo6vtbreVaQT','1351480177_jyNYGKS4xNjls2YbfFvV']
    df_chat = df_chat[df_chat['document_id'].isin(sel_doc_id)]

    result = df_chat.groupby('document_id').apply(lambda x: x[['role', 'content', 'timestamp']].to_dict(orient='records'), include_groups=False).to_dict()
    system_prompt = get_chat_analysis_prompt()
    chat_tags = []
    data = []
    i=1
    for document_id, user_message in result.items():
        chat_analysis = {}
        print(f"Analysing {i}/{len(result)} entries")
        system_prompt += "\n"+str(user_message)
        system_message = [{"role": "system", "content": system_prompt}]
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=system_message,
        #     stream=False,
        #     temperature=0)
        # full_response = response.choices[0].message.content
        full_response = 'test,test,test'
        chat_analysis['document_id'] = document_id
        chat_analysis['chat_analysis_tags'] = full_response
        chat_analysis['added_on'] = now_ist.date()
        data.append(chat_analysis)
        temp_tags = full_response.split(',')
        temp_tags = [tag.strip() for tag in temp_tags]
        chat_tags.extend(temp_tags)
        i += 1
    chat_analysis_df = pd.DataFrame(data, columns=['document_id', 'chat_analysis_tags','added_on'])
    chat_analysis_df.to_sql('chat_analysis', con = pool, if_exists = 'append', chunksize = 1000, index=False)
    print("Inserted data into chat_analysis!")
    
    chat_tags_df = pd.DataFrame(chat_tags, columns=['chat_tags'])
    chat_tags_df.to_sql('chat_tag_lookup', con = pool, if_exists = 'append', chunksize = 1000, index=False)
    print("Inserted data into chat_tag_lookup!")

def load_tg_users(df):
    print("Exporting USERS to SQL DB")
    try:
        df['created_on_date'] = df['created_on'].dt.date
        df['created_on_time'] = df['created_on'].dt.time
        df = df.drop(columns=['created_on'])
        df = df.drop(columns=['last_chatted_on'])
        df = df.drop(columns=['last_updated_on'])
        df = df.drop(columns=['status_change_dt'])
        df.to_sql('voiceClone_tg_users', con = pool, if_exists = 'replace', chunksize = 1000, index=False)
        print("Inserted data into voiceClone_tg_users!")
        return "User data loaded to analytics DB"
    except Exception as e:
        error = "User data load : Error: {}".format(str(e))
        return error
def load_tg_characters(df):
    print("Exporting CHARACTER to SQL DB")
    try:
        df = df[['char_id', 'character_name']].copy()
        df.to_sql('voiceClone_characters', con = pool, if_exists = 'append', chunksize = 1000, index=False)
        print("Inserted data into voiceClone_characters!")
        return "Character data loaded to analytics DB"
    except Exception as e:
        error = "Character data load : Error: {}".format(str(e))
        return error
def load_tg_chat(df):
    print("Exporting CHAT to SQL DB")
    try:
        with pool.connect() as db_conn:
            sql = sqlalchemy.text(
                "truncate table voiceClone_tg_chats",
            )
            db_conn.execute(sql)
            db_conn.commit()
        df['content'] = df['content'].str.replace('\n', '')
        df['content'] = df['content'].str.slice(0,1000)
        df['response_status'] = df['response_status'].str.slice(0,255)
        df.to_sql('voiceClone_tg_chats', con = pool, if_exists = 'append', chunksize = 1000, index=False)
        print("Inserted data into voiceClone_tg_chats!")

        try:
            ## Loading Chat analysis
            load_tg_chat_analytics(df)
        except Exception as e:
            error = "Chats Analysis data load : Error: {}".format(str(e))
            print(error)

        return "Chats data loaded to analytics DB"
    except Exception as e:
        error = "Chats data load : Error: {}".format(str(e))
        return error
def load_tg_logs(df):
    print("Exporting LOG to SQL DB")
    try:
        df['log_date'] = df['timestamp'].dt.date
        df['log_time'] = df['timestamp'].dt.time
        df = df.drop(columns=['timestamp'])
        df.to_sql('voiceClone_tg_logs', con = pool, if_exists = 'replace', chunksize = 1000, index=False)
        print("Inserted data into voiceClone_tg_logs!")
        connector.close()
        return "Log data loaded to analytics DB"
    except Exception as e:
        error = "Log data load : Error: {}".format(str(e))
        return error
def load_tg_reachouts(df):
    print("Exporting REACHOUT to SQL DB")
    try:
        df['reachout_date'] = df['timestamp'].dt.date
        df['reachout_time'] = df['timestamp'].dt.time
        df = df.drop(columns=['timestamp'])
        df.to_sql('voiceClone_tg_reachout', con = pool, if_exists = 'replace', chunksize = 1000, index=False)
        print("Inserted data into voiceClone_tg_reachout!")
        connector.close()
        return "Reachout data loaded to analytics DB"
    except Exception as e:
        error = "Reachout data load : Error: {}".format(str(e))
        return error

def download_tg_users():
    print("Downloading USERS from Firebase")
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
    columns = ['document_id', 'tg_user_id', 'char_id', 'created_on', 'first_name', 'id', 'is_bot', 'language_code', 'last_chatted_on', 'last_name', 'last_updated_on', 'username', 'status', 'status_change_dt']
    df = pd.DataFrame(data, columns=columns)
    print("Exporting to SQL DB...")
    status = load_tg_users(df)
    print(status)
    return df
def download_tg_characters():
    print("Downloading CHARACTERS from Firebase")
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

    print("Exporting to SQL DB...")
    status = load_tg_characters(df)
    print(status)
    return df
def download_tg_chat():
    print("Downloading CHAT from Firebase")
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
    columns = ['document_id', 'content', 'timestamp', 'role', 'content_type', 'reachout', 'response_status','update.message.message_id','update.update_id']
    df = pd.DataFrame(data, columns=columns)
    df.rename(columns={'update.message.message_id': 'message_id', 'update.update_id': 'update_id'}, inplace=True)
    status = load_tg_chat(df)
    print(status)
    return df
def download_tg_logs():
    print("Downloading LOGS from Firebase")
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
                    'message': str(value.get('message', None)),
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
                        'message': str(v.get('message', None)),
                        'message_id': v.get('message_id', None),
                        'origin': v.get('origin', None),
                        'status': v.get('status', None),
                        'status_cd': v.get('status_cd', None),
                        'timestamp': convert_ts(v.get('timestamp', None)),
                    })
    columns = ['document_id', 'tg_user_id', 'char_id', 'message', 'message_id', 'origin', 'status', 'status_cd', 'timestamp']
    df = pd.DataFrame(data, columns=columns)
    print("Exporting to SQL DB...")
    status = load_tg_logs(df)
    print(status)
    return df
def download_tg_reachout():
    print("Downloading REACHOUT from Firebase")
    data = []
    collection_ref = db.collection('voiceClone_tg_reachout')
    for doc in collection_ref.stream():
        if not(doc.id == "reachout_runlog"):
            doc_id = doc.id
            array = doc_id.split("_")
            tg_user_id = array[0]
            char_id = array[1]
            doc_data = doc.to_dict()
            for key, value in doc_data.items():
                if value.get('timestamp') or value.get('message') or value.get('content_type'):
                    data.append({
                        'document_id': doc_id,
                        'tg_user_id': tg_user_id,
                        'char_id': char_id,
                        'message': value.get('message', None),
                        'content_type': value.get('content_type', None),
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
                            'content_type': v.get('content_type', None),
                            'timestamp': convert_ts(v.get('timestamp', None)),
                        })
    columns = ['document_id', 'tg_user_id', 'char_id', 'message', 'content_type', 'timestamp']
    df = pd.DataFrame(data, columns=columns)
    print("Exporting to SQL DB...")
    status = load_tg_reachouts(df)
    print(status)
    return df
def export_file(df1,s1,df3,s3,df5,s5):
    sh = google_client.open_by_key(spreadsheet_id)
    print("Exporting data to Google sheet")
    print("Exporting User data...")
    # sh.add_worksheet(s1)
    wks_write = sh.worksheet_by_title(s1)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df1, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1
    # sh.add_worksheet(s2)
    # print("Exporting Character data...")
    # wks_write = sh.worksheet_by_title(s2)
    # wks_write.clear('A1',None,'*')
    # wks_write.set_dataframe(df2, (1,1), encoding='utf-8', fit=True)
    # wks_write.frozen_rows = 1
    # sh.add_worksheet(s3)
    print("Exporting Chat data...")
    wks_write = sh.worksheet_by_title(s3)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df3, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1
    # sh.add_worksheet(s4)
    # print("Exporting Error log data...")
    # wks_write = sh.worksheet_by_title(s4)
    # wks_write.clear('A1',None,'*')
    # wks_write.set_dataframe(df4, (1,1), encoding='utf-8', fit=True)
    # wks_write.frozen_rows = 1
    # sh.add_worksheet(s5)
    print("Exporting Reachout data...")
    wks_write = sh.worksheet_by_title(s5)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df5, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1    
    return True

df_users = download_tg_users()
# df_characters = download_tg_characters()
# df_chat = download_tg_chat()
# df_reachout = download_tg_reachout()
# df_logs = download_tg_logs()



# flag = export_file(df_users,'users',df_characters,'characters',df_chat,'chats',df_logs,'error_logs',df_reachout,'reachout_history')
# flag = export_file(df_users,'users',df_chat,'chats')
# if (flag):
#     print("Report generated: https://docs.google.com/spreadsheets/d/"+spreadsheet_id+"/edit?usp=sharing")