# pip install SQLAlchemy pandas
# pip install "cloud-sql-python-connector[pg8000]"

import sqlalchemy

from google.cloud.sql.connector import Connector
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timedelta
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
db = firestore.Client.from_service_account_json("firestore_key.json")

GOOGLE_APPLICATION_CREDENTIALS="firestore_key.json"
connector = Connector()

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

def getconn():
    conn = connector.connect(
        "chatmate-3fdd8:asia-south1-a:mitrrs-analytics",  # Your AlloyDB instance connection name
        "pg8000",  # DB driver to be used
        user="mitrrs_analyst",  # e.g., 'postgres'
        password="Analyst@560029",
        db="postgres"  # Database name
    )
    return conn

def create_connection():
    # Create a SQLAlchemy engine using the connector
    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn
    )

    # Test connection
    connection = engine.connect()
    print("Connection successful")
    connection.close()
    return engine

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
    columns = ['document_id', 'tg_user_id', 'char_id', 'content', 'timestamp', 'role', 'content_type','reachout', 'response_status','update.message.message_id','update.update_id']
    df = pd.DataFrame(data, columns=columns)
    return df


# Assuming df is your DataFrame
df = download_tg_chat()
engine = create_connection()
df.to_sql('chats', engine, if_exists='replace', index=False)

# Optional: Close the connection
engine.dispose()