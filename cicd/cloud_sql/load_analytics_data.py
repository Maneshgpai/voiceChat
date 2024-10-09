from firebase_admin import credentials, firestore
import pandas as pd
import pygsheets
from dotenv import load_dotenv, find_dotenv
import os
# from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import text
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
1. STRICTLY use only the below tags, which ever are apt to capture the intent and summarize conversation
ILLEGAL_AND_UNLAWFUL,HATE_SPEECH,PROFANITY,HARASSMENT_OR_ABUSE,ROMANTIC_INTENTION,PLATONIC_COMPANIONSHIP,PHYSICAL_CLOSENESS,PERSONAL_INFORMATION,PICTURES,ADVICE_AND_GUIDANCE,GENERAL_CURIOSITY,IDENTITY_AND_BACKGROUND,PREFERENCES,LIFE_EXPERIENCE,POSITIVE_EMOTION,NEGATIVE_EMOTIONS,SEEKING_EMOTIONAL_SUPPORT,EXPLICIT_REQUEST,SEXUAL_INNUENDO,BOUNDARY_VIOLATIONS,MOVIES_AND_TV,MUSIC,CELEBRITY_GOSSIP,VOICE_TALK,GENERAL_CONVERSATION,HUMOR_AND_PLAYFULNESS,CAREER_DISCUSSION,ACADEMIC_DISCUSSION
Any other tags which do not come under the above categories to be marked as "OTHERS"
2. You can have one or multiple tags as you feel necessary to capture the essense of summary or user ask.
3. Do not include examples from the chat.
4. Only include word tags in your response. Do not include explanation or title or summary or any other text, apart from word tags.
5. Follow the below format for response
Example 1: ROMANTIC INTENTIONS,PHYSICAL CLOSENESS,ADVICE AND GUIDANCE
Example 2: GENERAL CURIOSITY, IDENTITY AND BACKGROUND, PREFERENCES AND LIKES
Example 3: CAREER AND ACADEMIC DISCUSSIONS
Example 4: OTHERS

MESSAGE CONVERSATIONS:"""
    return system_prompt
def process_chat(user_message):
  system_prompt = get_chat_analysis_prompt()
  system_prompt += "\n"+str(user_message)
  system_message = [{"role": "system", "content": system_prompt}]
  response = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=system_message,
      stream=False,
      temperature=0)
  full_response = response.choices[0].message.content

  # enc = tiktoken.encoding_for_model("gpt-4o-mini")
  # full_response = str(len(enc.encode(system_prompt)))

  return full_response
def load_tg_chat_analytics(df):
    load_logs = []
    ## Exclude Reachouts from assistant
    df = df[df['reachout'] != True]

    ## Keep only 4 columns which are needed for LLM categorization: document_id, content, timestamp, role
    df_chat = df.drop(df.columns[[4,5,6,7,8]], axis=1)

    ## selecting sample data ste for testing
    sel_doc_id = ['1612746679_bPm741abegxqm3t7rfeB','6799283616_bPm741abegxqm3t7rfeB','1781890703_jyNYGKS4xNjls2YbfFvV','6057885035_IJfd3UlnIo6vtbreVaQT']
    df_chat = df_chat[df_chat['document_id'].isin(sel_doc_id)]

    ## Classify user only chats for classification: START
    chat_role = ['user']
    df_chat = df_chat[df_chat['role'].isin(chat_role)]
    df.drop(columns=['role'])
    result = df_chat.groupby('document_id').apply(lambda x: x[['role', 'content', 'timestamp']].to_dict(orient='records')).to_dict()
    # result = df_chat.groupby('document_id').apply(lambda x: x[['content']].to_dict(orient='records')).to_dict()
    print(f"************** {df}")
    ## Classify user only chats for classification: END

    result_ordered = []
    for key, value in result.items():
      temp = {}
      temp['document_id'] = key
      temp['messages'] = str(value)
      result_ordered.append(temp)
    result_df = pd.DataFrame(result_ordered)

    exclude_doc_id = ['6697940905','7142807432','6733334932']
    now = datetime.now()
    data_loaded_on = now_utc.astimezone(ist_timezone)
    j=1

    batch_size = 10
    num_records = len(result_df)
    for i in range(0, num_records, batch_size):
        batch = result_df.iloc[i:min(i + batch_size, num_records)]
        chat_tags = []
        data = []

        print(f"Processing batch {i+1}/{len(result_df)}")
        for index, content in batch.iterrows():
          user_message = content['messages']
          document_id = content['document_id']

          array = str(document_id).split("_")
          if array[0] not in exclude_doc_id:
            chat_analysis = {}
            print(f"Analysing {j}/{len(result_df)} : {document_id}")

            try:
              full_response = process_chat(user_message)
            except Exception as e:
                error = format(str(e))
                print("Error when analysing tag for",document_id,": Error:",error)
                load_logs.append(f"Error when analysing tag for {document_id}: Error: {error}")
                continue

            chat_analysis['document_id'] = document_id
            chat_analysis['chat_analysis_tags'] = full_response
            chat_analysis['data_loaded_on'] = data_loaded_on
            data.append(chat_analysis)

            temp_tags = full_response.split(',')
            temp_tags = [tag.strip() for tag in temp_tags]
            chat_tags.extend(temp_tags)

            j += 1
          else:
            print(f"Skipping document_id:{document_id}")
            load_logs.append(f"Skipping document_id:{document_id}")

        try:
            chat_analysis_df = pd.DataFrame(data, columns=['document_id', 'chat_analysis_tags','data_loaded_on'])
            chat_analysis_df.to_sql('chat_analysis', con = pool, if_exists = 'append', chunksize = 1000, index=False)

            # ## Updating the column type for collation correction
            # sql_statements = [
            #     "ALTER TABLE chat_analysis MODIFY COLUMN document_id VARCHAR(50) COLLATE utf8mb4_unicode_ci",
            #     "ALTER TABLE chat_analysis MODIFY COLUMN chat_analysis_tags VARCHAR(1000) COLLATE utf8mb4_unicode_ci",
            #     "ALTER TABLE chat_analysis MODIFY COLUMN data_loaded_on datetime COLLATE utf8mb4_unicode_ci",
            #     "ALTER TABLE chat_analysis_pivot MODIFY COLUMN document_id VARCHAR(50) COLLATE utf8mb4_unicode_ci",
            #     "ALTER TABLE chat_analysis_pivot MODIFY COLUMN tag_key text COLLATE utf8mb4_unicode_ci"
            # ]
            # with pool.connect() as connection:
            #     for statement in sql_statements:
            #         connection.execute(sqlalchemy.text(statement))


        except Exception as e:
            error = format(str(e))
            print(f"Error when load data chat_analysis for {document_id}: Error:",error)
            load_logs.append(f"Error when load data chat_analysis for {document_id}: Error: {error}")
            continue

        print(f"Batch {i+1}: {data}")
        try:
          chat_tags_df = pd.DataFrame(chat_tags, columns=['chat_tags'])
          chat_tags_df.to_sql('chat_tag_lookup', con = pool, if_exists = 'append', chunksize = 1000, index=False)
        except Exception as e:
            error = format(str(e))
            print(f"Error when load data chat_tag_lookup for {document_id}: Error:",error)
            load_logs.append(f"Error when load data chat_tag_lookup for {document_id}: Error: {error}")
            continue

    if len(load_logs) > 0:
      load_logs_df = pd.DataFrame(load_logs, columns=['logs'])
      load_logs_df.to_csv("/content/drive/MyDrive/temp_to_delete/chat_analysis_load_logs.csv", sep='\t', encoding='utf-8', index=False, header=True)

def load_tg_characters(df):
    print("Exporting CHARACTER to SQL DB")
    try:
        df = df[['char_id', 'character_name']].copy()
        df.to_sql('voiceClone_characters', con = pool, if_exists = 'append', chunksize = 1000, index=False)
        print("Inserted data into voiceClone_characters!")

        ## Updating the column type for collation correction
        sql_statements = [
            "ALTER TABLE voiceClone_characters MODIFY COLUMN char_id VARCHAR(50) COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_characters MODIFY COLUMN character_name VARCHAR(50) COLLATE utf8mb4_unicode_ci",
        ]
        with pool.connect() as connection:
            for statement in sql_statements:
                connection.execute(sqlalchemy.text(statement))

        return "Character data loaded to analytics DB"
    except Exception as e:
        error = "Character data load : Error: {}".format(str(e))
        return error
def load_tg_users(df):
    print("Exporting USERS to SQL DB")
    try:
        df['created_on_date'] = df['created_on'].dt.date
        df['created_on_time'] = df['created_on'].dt.time
        df = df.drop(columns=['created_on'])
        df = df.drop(columns=['last_chatted_on'])
        # df = df.drop(columns=['last_updated_on'])
        df = df.drop(columns=['status_change_dt'])
        df.to_sql('voiceClone_tg_users', con = pool, if_exists = 'replace', chunksize = 1000, index=False)
        print("Inserted data into voiceClone_tg_users!")

        ## Updating the column type for collation correction
        sql_statements = [
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN document_id TEXT COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN tg_user_id TEXT COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN char_id TEXT COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN first_name TEXT COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN last_name TEXT COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN username TEXT COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN status TEXT COLLATE utf8mb4_unicode_ci",
            "ALTER TABLE voiceClone_tg_users MODIFY COLUMN is_bot TINYINT(1) COLLATE utf8mb4_unicode_ci"
        ]
        with pool.connect() as connection:
            for statement in sql_statements:
                connection.execute(sqlalchemy.text(statement))

        return "User data loaded to analytics DB"
    except Exception as e:
        error = "User data load : Error: {}".format(str(e))
        return error
def load_tg_chat(df):
    print("Exporting CHAT to SQL DB")
    try:
        df['content'] = df['content'].str.replace('\n', '')
        df['content'] = df['content'].str.slice(0,1000)
        df['response_status'] = df['response_status'].str.slice(0,255)
        df['data_loaded_on'] = now_ist
        df.to_sql('voiceClone_tg_chats', con = pool, if_exists = 'append', chunksize = 1000, index=False)

        print("Inserted data into voiceClone_tg_chats!")

        # try:
        #     load_tg_chat_analytics(df)
        # except Exception as e:
        #     error = "Chats Analysis data load : Error: {}".format(str(e))
        #     print(error)

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
    df = {}
    collection_ref = db.collection('voiceClone_tg_users')
    print("\n\n\nDownloading USERS from Firebase")
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
    print(f"Loaded {len(df)} users into DF...")
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
    collection_ref = db.collection('voiceClone_tg_chats')
    print("\n\n\nDownloading CHAT messages from Firebase")
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

    ## Logic for Incremental loading
    with pool.connect() as connection:
        result = connection.execute(text('SELECT max(data_loaded_on) FROM voiceClone_tg_chats'))
        for row in result:
            last_data_loaded_on = row[0]

    ## Take only records which are greater than last loaded date
    if last_data_loaded_on != None:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[df['timestamp'] > last_data_loaded_on]

    ## Adding current timestamp for incremental rows
    now_ist = now_utc.astimezone(ist_timezone)
    df['data_loaded_on'] = now_ist

    print(f"Loaded {len(df)} chat messages into DF...")
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
def get_chat_usage_sql():
    sql = """
    with user_chat_kpi as (with user_msg as (select document_id as col1,DATE_FORMAT(timestamp, "%d %M %Y") as col2, count(message_id) as user_msg_cnt from voiceClone_tg_chats where reachout is null and role = 'user' group by document_id,DATE_FORMAT(timestamp, "%d %M %Y")),
    chat_duration as (select document_id as col1, chatdt as col2, sum(duration_in_sec) as chat_duration_in_sec 
            from (SELECT document_id, DATE_FORMAT(timestamp, "%d %M %Y") as chatdt, IF(TIMESTAMPDIFF(SECOND, IF(LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)='01-01-1900',null,LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)) , timestamp)>1800,null,TIMESTAMPDIFF(SECOND, IF(LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)='01-01-1900',null,LAG(timestamp, 1,0) OVER (PARTITION BY document_id, DATE_FORMAT(timestamp, "%d %M %Y") ORDER BY timestamp)) , timestamp)) as duration_in_sec 
            FROM voiceClone_tg_chats where reachout is null) t1 group by document_id, chatdt)
    select distinct c.document_id
    , DATE_FORMAT(timestamp, "%d %M %Y") as chat_date
    , DATEDIFF(c.timestamp, u.created_on_date) as day_count
    , cd.chat_duration_in_sec as duration_in_sec
    , um.user_msg_cnt
    from voiceClone_tg_chats c
    inner join voiceClone_tg_users u on u.document_id = c.document_id
    left join user_msg um on um.col1 = c.document_id and um.col2 = DATE_FORMAT(c.timestamp, "%d %M %Y")
    left join chat_duration cd on cd.col1 = c.document_id and cd.col2 = DATE_FORMAT(c.timestamp, "%d %M %Y")
    where u.is_bot = 'false'
    and c.reachout is null)
    select distinct u.tg_user_id
    , CONCAT(u.first_name, ' ',u.last_name) as user_fullname
    , u.username
    , u.status as user_status
    , u.created_on_date as user_created_on_date
    , u.document_id
    , ch.character_name
    , vw.chat_date
    , ifnull(vw.day_count,0) as day_count
    , ifnull(vw.duration_in_sec,0) as duration_in_sec
    , ifnull(vw.user_msg_cnt,0) as user_msg_cnt
    , replace(replace(lower(chat_analysis_tags),'_',' '),', ',',') as chat_analysis_tags
    from user_chat_kpi vw
    inner join voiceClone_tg_users u on u.document_id = vw.document_id
    inner join voiceClone_characters ch on u.char_id = ch.char_id 
    left join voiceClone_tg_chats c on c.document_id = vw.document_id
    left join chat_analysis ca on ca.document_id = c.document_id
    where c.reachout is null
    and u.is_bot = 0
    and u.created_on_date >= '2024-08-15'
    and u.tg_user_id not in ('6697940905','7142807432','6733334932')
    """
    return sql
def export_file():
    sh = google_client.open_by_key(spreadsheet_id)
    print("Exporting data to Google sheet")
    print("Exporting User data...")
    # # sh.add_worksheet(s1)
    # wks_write = sh.worksheet_by_title(s1)
    # wks_write.clear('A1',None,'*')
    # wks_write.set_dataframe(df1, (1,1), encoding='utf-8', fit=True)
    # wks_write.frozen_rows = 1
    # # sh.add_worksheet(s2)
    # # print("Exporting Character data...")
    # # wks_write = sh.worksheet_by_title(s2)
    # # wks_write.clear('A1',None,'*')
    # # wks_write.set_dataframe(df2, (1,1), encoding='utf-8', fit=True)
    # # wks_write.frozen_rows = 1
    # # sh.add_worksheet(s3)
    # print("Exporting Chat data...")
    # wks_write = sh.worksheet_by_title(s3)
    # wks_write.clear('A1',None,'*')
    # wks_write.set_dataframe(df3, (1,1), encoding='utf-8', fit=True)
    # wks_write.frozen_rows = 1
    # # sh.add_worksheet(s4)
    # # print("Exporting Error log data...")
    # # wks_write = sh.worksheet_by_title(s4)
    # # wks_write.clear('A1',None,'*')
    # # wks_write.set_dataframe(df4, (1,1), encoding='utf-8', fit=True)
    # # wks_write.frozen_rows = 1
    # # sh.add_worksheet(s5)
    # print("Exporting Reachout data...")
    # wks_write = sh.worksheet_by_title(s5)
    # wks_write.clear('A1',None,'*')
    # wks_write.set_dataframe(df5, (1,1), encoding='utf-8', fit=True)
    # wks_write.frozen_rows = 1
    ## Code to execute a query in MYSQL using sqlalchemy and output the result into a CSV
    chat_usage_df = pd.read_sql(get_chat_usage_sql(), con=pool)
    tags_dummies = chat_usage_df['chat_analysis_tags'].str.get_dummies(sep=',')
    chat_usage_df = pd.concat([chat_usage_df, tags_dummies], axis=1)
    chat_usage_df.fillna('', inplace=True)

    usage_df1 = chat_usage_df
    tags = usage_df1['chat_analysis_tags'].str.get_dummies(sep=',')
    tags = tags.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    usage_df1 = pd.concat([usage_df1, tags], axis=1)
    usage_df1.fillna('', inplace=True)
    usage_df1 = usage_df1.drop(columns=['tg_user_id'])
    usage_df1 = usage_df1.drop(columns=['user_fullname'])
    usage_df1 = usage_df1.drop(columns=['username'])
    usage_df1 = usage_df1.drop(columns=['user_status'])
    usage_df1 = usage_df1.drop(columns=['user_created_on_date'])
    usage_df1 = usage_df1.drop(columns=['character_name'])
    usage_df1 = usage_df1.drop(columns=['chat_date'])
    usage_df1 = usage_df1.drop(columns=['day_count'])
    usage_df1 = usage_df1.drop(columns=['duration_in_sec'])
    usage_df1 = usage_df1.drop(columns=['user_msg_cnt'])
    usage_df1 = usage_df1.drop(columns=['chat_analysis_tags'])
    value_vars = usage_df1.columns[1:]
    chat_tag_lookup_df = pd.melt(usage_df1, id_vars=[usage_df1.columns[0]], value_vars=value_vars, var_name='tag_key', value_name='tag_values')

    wks_write = sh.worksheet_by_title('chat_usage')
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(chat_usage_df, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1

    wks_write = sh.worksheet_by_title('chat_tag_lookup')
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(chat_tag_lookup_df, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1

    ## Create C
    query = """select document_id, content, content_type,timestamp, message_id, response_status as chat_ts,role  from voiceClone_tg_chats where reachout is null"""
    chats_df = pd.read_sql(query, con=pool)

    wks_write = sh.worksheet_by_title('chats')
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(chats_df, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1

    return True

# df_characters = download_tg_characters()
# df_users = download_tg_users()
# df_chat = download_tg_chat()
# df_reachout = download_tg_reachout()
df_logs = download_tg_logs()

# flag = export_file(df_users,'users',df_characters,'characters',df_chat,'chats',df_logs,'error_logs',df_reachout,'reachout_history')
# flag = export_file()
# if (flag):
#     print("Report generated: https://docs.google.com/spreadsheets/d/"+spreadsheet_id+"/edit?usp=sharing")





