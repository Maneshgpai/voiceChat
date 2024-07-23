import streamlit as st
# from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import hmac
import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from elevenlabs.client import ElevenLabs
from elevenlabs import play,  Voice, VoiceSettings, save
import nest_asyncio
nest_asyncio.apply()

if "firestore_db" not in st.session_state:
    db = firestore.Client.from_service_account_json("firestore_key.json")
else:
    db = st.session_state["firestore_db"]
# cred = credentials.Certificate("firestore_key.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

ist = timezone(timedelta(hours=5, minutes=30))
st.session_state.status = st.session_state.get("status", "unverified")
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

if "telegram_id_disabled" not in st.session_state:
    st.session_state["telegram_id_disabled"] = False

def check_password():
    if hmac.compare_digest(st.session_state.password, os.getenv("LOGIN_PASSWORD")):
        st.session_state.status = "verified"
    else:
        st.session_state.status = "incorrect"
    st.session_state.password = ""
def login_prompt():
    st.text_input("Enter password:", key="password", type="password", on_change=check_password)
    if st.session_state.status == "incorrect":
        st.warning("Incorrect password. Please try again.")
def get_char_setting(char_id):
    ## If exists, fetch settings from DB
    setting = db.collection('voiceClone_characters').document(char_id)
    doc = setting.get()
    char_setting = {}
    if doc.exists:
        setting = doc.to_dict()
        for k, v in setting.items():
            if k == 'setting':
                char_setting = v
    return char_setting
def get_agent_response(voice_setting,user_query):

    ## Based on model from the voice_setting, call different LLMs
    ## if st.session_state["voice_setting"].["model"] == "gpt-3.5-turbo" OR "gpt-4o":
    # response = textresponse.get_openai_response(voice_setting,session_messages)
    ## elif st.session_state["voice_setting"].["model"] == "claude-3-5-sonnet-20240620":
        ## response = textresponse.get_claude_response(st.session_state["voice_setting"],st.session_state.messages)
    # return response

    public_api_url = os.environ['PUBLIC_API_URL']+'/api/mockchat'
    print(f"pg_chat >> get_agent_response > Mock chat >> Calling agent {public_api_url}")
    response = {}
    response = json.dumps(response)
    try:
        response = requests.post(public_api_url
        , json={"telegram_id": st.session_state["user_telegram"],
                "user_query": user_query,
                "voice_setting": voice_setting,
                "user_query_timestamp": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})
        response.raise_for_status()
        print(f"Mock chat >> Agent response: Status code {response.status_code}. Message:{response.json().get('message')}\n")
        return (response.json().get("message"))
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
    except Exception as e:
        error = "Error: {}".format(str(e))
        st.error(error)
def generateVoice(context, input_text,voice_id):
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Voice generation started")
    
    voice_settings = VoiceSettings(
        stability=context['voice_stability'],
        similarity_boost=context['voice_similarity_boost'],
        style=context['voice_style'],
        use_speaker_boost=context['voice_use_speaker_boost']
    )

    print("Default setting for the voice id:",client.voices.get_settings(voice_id))
    audio = client.generate(
        text=input_text,
        voice=Voice(
            voice_id=voice_id,
            settings=client.voices.get_settings(voice_id),
            # settings=voice_settings,
        ),
        model="eleven_multilingual_v2"
    )
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Voice generation finished")
    return audio
def get_voice_response(voice_setting, full_response,voice_id):
    try:
        audio = generateVoice(voice_setting,full_response,voice_id)
        print("Inside pg_chat >> get_voice_response > Generated Audio!")
        timestamp = datetime.now(ist).strftime('%Y%m%d%I%M%S%p')
        directory_path = "voice_chats/"+st.session_state["user_telegram"]
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        filename = directory_path + "/"+ st.session_state["user_telegram"]+"_"+timestamp+".mp3"
        save(audio, filename)
        print("Inside pg_chat >> get_voice_response > Saved Audio file!")
        return filename
    except Exception as e:
        error = "Error: {}".format(str(e))
        st.error(error)
def get_all_characters():
    users_ref = db.collection('voiceClone_characters')
    docs = users_ref.stream()
    user_data = []
    for doc in docs:
        char_id1 = doc.id
        user_info = doc.to_dict()
        name = user_info.get('name', 'not_populated')
        voice_id1 = user_info.get('voice_id', 'not_populated')
        user_data.append((name,voice_id1, char_id1))
    df = pd.DataFrame(user_data, columns=['Character','Voice ID', 'ID'])
    return(df)
def chat_interface():
    print("Inside pg_chat >> chat_interface > Entered func")
    st.subheader(f"You are now chatting with {st.session_state['char_name']}")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                st.audio(message["audio_file"])

    # Input for new HUMAN message
    if prompt := st.chat_input(""):
        st.session_state.messages.append({"role": "user", "content": prompt})
        print("Inside pg_chat >> chat_interface > prompt:",prompt)
        if "user_query" not in st.session_state:
            st.session_state.user_query = prompt

        # Showing Text Output for HUMAN
        with st.chat_message(name="user", avatar=":material/person:"):
            st.markdown(prompt)

        # Showing Text Output for BOT
        with st.chat_message("ai"):
            response = get_agent_response(st.session_state["voice_setting"],prompt)
            st.write(response)
            file_name = get_voice_response(st.session_state["voice_setting"], response, st.session_state["v_voice_id"])
            st.audio(file_name,autoplay=True)
            print(f"Inside pg_chat >> chat_interface > Saving file in :{file_name}")
            st.session_state.messages.append({"role": "assistant", "content": response, "audio_file": file_name})
def validate_user(db, telegram_id):
    user_exist = False
    collection_ref = db.collection('voiceClone_users')

    query = collection_ref.where("telegram_id", "==", telegram_id)#.where("population", ">", 1000000)
    docs = query.stream()
    for doc in docs:
        dict = doc.to_dict()
        if dict['telegram_id'] == telegram_id:
            print("Telegram ID exists in DB")
            st.session_state["user_telegram"] = telegram_id
            st.session_state["uname"] = dict['user_name']
            user_exist = True
    return user_exist
def render_page():
    if "voice_setting" not in st.session_state:
        df = get_all_characters()
        st.subheader(f"Welcome {st.session_state['uname']}")
        with st.form("select_chat_character", border=False):
            print("Entered chat form ",datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'))
            char_name = st.selectbox("Select character to chat", df['Character'].tolist(), key="character_id")
            submit_chat_character = st.form_submit_button("Submit")
        if submit_chat_character:
            with st.spinner("Loading..."):
                result = df.loc[df['Character'] == char_name, 'ID']
                char_id = result.iloc[0]
                result = df.loc[df['Character'] == char_name, 'Voice ID']
                v_voice_id = result.iloc[0]
                voice_setting = get_char_setting(char_id)
                st.session_state["char_id"] = char_id
                st.session_state["v_voice_id"] = v_voice_id
                st.session_state["char_name"] = char_name
                st.session_state["voice_setting"] = voice_setting
                chat_interface()
                st.rerun()

    else:
        chat_interface()

############# PAGE START #############
if "user_telegram" not in st.session_state:
    st.text_input("Please login using Telegram Id:", key="telegram_id")
    login = st.button("Login")
    if login:
        user_exist = validate_user(db, st.session_state.telegram_id)
        print("user_exist:",user_exist)
        if not(user_exist):
            st.error("User does not exist")
        else:
            render_page()
            st.rerun()
else:
    render_page()