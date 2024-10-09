import streamlit as st
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import hmac
import os
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

if "firestore_db" not in st.session_state:
    db = firestore.Client.from_service_account_json(str(os.getenv("SECRETS_PATH")+"/firestore_key_agent.json"))
else:
    db = st.session_state["firestore_db"]
if "status" not in st.session_state:
    st.session_state.status = st.session_state.get("status", "unverified")
ist = timezone(timedelta(hours=5, minutes=30))
def check_password():
    with st.spinner('Loading...'):
        if hmac.compare_digest(st.session_state.password, os.getenv("LOGIN_PASSWORD")):
            st.session_state.status = "verified"
        else:
            st.session_state.status = "incorrect"
        st.session_state.password = ""
def login_prompt():
    st.text_input("Enter password:", key="password", type="password", on_change=check_password)
    if st.session_state.status == "incorrect":
        st.warning("Incorrect password. Please try again.")
def get_all_voices():
    users_ref = db.collection('voice')
    docs = users_ref.stream()
    user_data = []
    for doc in docs:
        char_id1 = doc.id
        user_info = doc.to_dict()
        user_data.append((
            user_info.get('id', '<Not given!>'),
            user_info.get('name', '<Not given!>'),
            user_info.get('gender', '<Not given!>'),
            user_info.get('age', '<Not given!>'),
            user_info.get('ethnicity', '<Not given!>'),
            user_info.get('language', '<Not given!>'),
            user_info.get('tags', '<Not given!>'),
            char_id1))
    df = pd.DataFrame(user_data, columns=['Voice Id','Name', 'Gender', 'Age', 'Ethnicity', 'Language', 'Tags', 'doc_id'])
    return(df)
def update_voice(doc_id,voice_id,voice_name,voice_gender,voice_age,voice_ethnicity,voice_language,voice_tags):
    print(f"****************** doc_id:{doc_id}, voice_id:{voice_id}, voice_name:{voice_name}")
    print()
    try:
        db.collection('voice').document(doc_id).set({
        "last_updated_on": datetime.now(ist),
        "name":voice_name,
        "gender":voice_gender,
        "age":voice_age,
        "ethnicity":voice_ethnicity,
        "language":voice_language,
        "id":voice_id,
        "tags":voice_tags})
    except Exception as e:
        error = "Error: {}".format(str(e))
        print(f"{datetime.now(ist)}**********pg_settings>pg_voice_settings>updatevoice()>> ERROR {error}")
        if ["error"] not in st.session_state:
            st.session_state["error"] = error
        return False
    return True
def get_voice(voice_id):
    ## Logic to retrieve doc_id for the given voice id
    v_dict = []
    all_voice_df = st.session_state["all_voices"]
    print("get_voice >> voice_id:",voice_id)
    print("get_voice >> all_voice_df:",all_voice_df)
    try:
        result = all_voice_df.loc[all_voice_df['Voice Id'] == voice_id, 'doc_id']
        document_id = result.iloc[0]
        setting = db.collection('voice').document(document_id)
        doc = setting.get()
        if doc.exists:
            v_dict = doc.to_dict()
            v_dict['doc_id'] = document_id
            print("****************** document_id",document_id)
            print("****************** v_dict",v_dict)
        else:
            print("No data exists in DB for given Voice ID")
            st.error("No data exists in DB for given Voice ID")
    except Exception as e:
        error = "Error: {}".format(str(e))
        print(f"{datetime.now(ist)}**********pg_settings>pg_voice_settings>updatevoice()>> ERROR {error}")
        if ["error"] not in st.session_state:
            st.session_state["error"] = error
        # st.error(error)
    return v_dict
def popover_add_voice():
    with st.popover("Add Voice"):
        st.subheader("Add new Voice:")
        with st.form("add_new_voice", border=False):
            col1, col2 = st.columns([1,1])
            with col1:
                st.text_input("Voice Id", key="create_new_voice_id")
                st.text_input("Name", key="create_new_voice_name")
                st.text_input("Ethnicity", key="create_new_voice_ethnicity")
            with col2:
                st.text_input("Gender", key="create_new_voice_gender")
                st.text_input("Age", key="create_new_voice_age")
                st.text_input("Language", key="create_new_voice_language")
            st.text_input("Tags", key="create_new_voice_tags")
            submit_new_voice = st.form_submit_button("Add")
        if submit_new_voice:
            if (st.session_state.create_new_voice_id == "" or st.session_state.create_new_voice_name == "" or st.session_state.create_new_voice_gender == "" or st.session_state.create_new_voice_language == ""):
                st.warning("Voice Id, Name, Gender and Language are mandatory fields")
            else:
                stat = update_voice(st.session_state.create_new_voice_id,st.session_state.create_new_voice_id,st.session_state.create_new_voice_name,st.session_state.create_new_voice_gender,st.session_state.create_new_voice_age,st.session_state.create_new_voice_ethnicity,st.session_state.create_new_voice_language,st.session_state.create_new_voice_tags)
                if stat:
                    st.success("Voice Added successfully! Press 'R' to refresh the voice data")
                else:
                    st.error(st.session_state["error"])
def popover_edit_voice():
    with st.popover("Edit Voice"):
        if "edit_id" not in st.session_state:
            st.session_state["edit_id"] = ""
        if "edit_age" not in st.session_state:
            st.session_state["edit_age"] = ""
        if "edit_name" not in st.session_state:
            st.session_state["edit_name"] = ""
        if "edit_gender" not in st.session_state:
            st.session_state["edit_gender"] = ""
        if "edit_ethnicity" not in st.session_state:
            st.session_state["edit_ethnicity"] = ""
        if "edit_language" not in st.session_state:
            st.session_state["edit_language"] = ""
        if "edit_tags" not in st.session_state:
            st.session_state["edit_tags"] = ""
        if "edit_doc_id" not in st.session_state:
            st.session_state["edit_doc_id"] = ""

        st.subheader("Edit Existing Voice:")
        voice_info = []
        with st.form("provide_voice_id", border=False):
            v_existing_voice_id = st.text_input("Copy 'Voice Id' from table above", key="existing_voice_id")
            submit_edit = st.form_submit_button("Get data")
        if submit_edit:    
            voice_info = get_voice(v_existing_voice_id)
            print("*********** voice_info:",voice_info)
            if voice_info == []:
                st.error("No data exists in DB for given Voice Id")
            else:
                st.session_state["edit_id"] = voice_info.get('id', '<Not given!>')
                st.session_state["edit_age"] = voice_info.get('age', '<Not given!>')
                st.session_state["edit_name"] = voice_info.get('name', '<Not given!>')
                st.session_state["edit_gender"] = voice_info.get('gender', '<Not given!>')
                st.session_state["edit_ethnicity"] = voice_info.get('ethnicity', '<Not given!>')
                st.session_state["edit_language"] = voice_info.get('language', '<Not given!>')
                st.session_state["edit_tags"] = voice_info.get('tags', '<Not given!>')
                st.session_state["edit_doc_id"] = voice_info.get('doc_id', '<Not given!>')
                # print(f"1 st.session_state.edit_doc_id:",st.session_state["edit_doc_id"])

        with st.form("update_voice_id", border=False):
            col1, col2 = st.columns([1,1])
            with col1:
                st.text_input("Voice Id",value=st.session_state["edit_id"], key="update_new_voice_id")
                st.text_input("Name",value=st.session_state["edit_name"], key="update_new_voice_name")
                st.text_input("Gender",value=st.session_state["edit_gender"], key="update_new_voice_gender")
            with col2:
                st.text_input("Age",value=st.session_state["edit_age"], key="update_new_voice_age")
                st.text_input("Ethnicity",value=st.session_state["edit_ethnicity"], key="update_new_voice_ethnicity")
                st.text_input("Language",value=st.session_state["edit_language"], key="update_new_voice_language")
                st.text_input("Tags",value=st.session_state["edit_tags"], key="update_new_voice_tags")
            update_voice_button = st.form_submit_button("Update")
            if update_voice_button:
                if (st.session_state.update_new_voice_id == "" or st.session_state.update_new_voice_name == "" or st.session_state.update_new_voice_gender == "" or st.session_state.update_new_voice_language == ""):
                    st.warning("Voice Id, Name, Gender and Language are mandatory fields")
                else:
                    stat = update_voice(st.session_state["edit_doc_id"], st.session_state.update_new_voice_id,st.session_state.update_new_voice_name,st.session_state.update_new_voice_gender,st.session_state.update_new_voice_age,st.session_state.update_new_voice_ethnicity,st.session_state.update_new_voice_language,st.session_state.update_new_voice_tags)
                    if stat:
                        st.success("Voice Added successfully! Press 'R' to refresh the voice data")
                    else:
                        st.error(st.session_state["error"])


if st.session_state.status != "verified":
    login_prompt()
    st.stop()
else:
    print("********* Session valid, password validated. ")
    voice_df = get_all_voices()
    st.session_state["all_voices"] = voice_df
    st.write("Voices available in system:")
    st.dataframe(data=voice_df.drop(['doc_id'], axis=1))
    popover_add_voice()
    popover_edit_voice()
