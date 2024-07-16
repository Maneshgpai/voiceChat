import streamlit as st
import requests
from dotenv import load_dotenv
import os
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import requests

load_dotenv()
ist = timezone(timedelta(hours=5, minutes=30))

if "firestore_db" not in st.session_state:
    db = firestore.Client.from_service_account_json("firestore_key.json")
else:
    db = st.session_state["firestore_db"]

if "telegram_id_disabled" not in st.session_state:
    st.session_state["telegram_id_disabled"] = False

if "user_telegram" not in st.session_state:
    st.session_state["user_telegram"] = ""

def render_page():
    st.write("You are now connected and in session...")
    # st.write("Hi ",st.session_state["voice_name"],"You can edit your preferences here.")
    st.divider()
    col1, col2 = st.columns([1,1])
    with col1:
        st.page_link("webpages/pg_chat.py", label="Chat", icon=":material/voice_chat:")
    with col2:
        st.page_link("webpages/pg_settings.py", label="Settings", icon=":material/tune:")

# def validate_voice_id():
#     print(f"pg_home > validate_voice_id > {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Validating Voice ID")
#     url = f"https://api.elevenlabs.io/v1/voices/{st.session_state.voice_id}"
#     headers = {
#         "Accept": "application/json",
#         "xi-api-key": voice_api_key
#     }
#     response = requests.get(url, headers=headers)
    
#     if 'voice_id' not in st.session_state:
#         st.session_state.voice_id = st.session_state['voice_id']

#     if response.status_code == 200:
#         voice_data = response.json()
#         voice_name = voice_data.get("name")
#         # if "voice_name" not in st.session_state:
#         st.session_state["voice_name"] = voice_name
#         st.session_state["voice_id_disabled"] = True
#         st.session_state["voice_id"] = st.session_state.voice_id
#         print(f"pg_home > validate_voice_id > {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Voice ID VALIDATED")
#     else:
#         st.session_state["voice_id_disabled"] = False
#         st.error("Invalid Voice ID. Please try again.")
#         # return False

def validate_user():
# def field_value_exists(collection_name, field_name, field_value):
    collection_ref = db.collection('voiceClone_users')
    field_name = 'telegram_id'
    field_value = st.session_state.telegram_id
    query = collection_ref.where(field_name, '==',field_value)
    results = query.stream()
    for doc in results:
        doc_data = doc.to_dict()
        if field_name in doc_data:
            if doc_data[field_name] == field_value:
                st.session_state["user_telegram"] = st.session_state.telegram_id
            else:
                st.error("User does not exist")


if "user_telegram" not in st.session_state:
    with st.form("home_form", border=False):
        st.text_input("Please login using Telegram Id:", value=st.session_state.telegram_id, key="telegram_id")
        st.form_submit_button("Login", on_click=validate_user, disabled=st.session_state.telegram_id_disabled)
else:
    render_page()

