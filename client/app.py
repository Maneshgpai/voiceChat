import streamlit as st

st.set_page_config(page_title="Voice Chat", layout="wide", page_icon=":material/record_voice_over:")

pg = st.navigation([
        # st.Page("webpages/pg_home.py", title="Home", icon=":material/home:"),
        # st.Page("webpages/pg_chat.py", title="Chat", icon=":material/voice_chat:"),
        st.Page("webpages/pg_settings.py", title="Character Settings", icon=":material/tune:"),
        st.Page("webpages/pg_addvoice.py", title="Voice Settings", icon=":material/settings_voice:"),
    ], position="sidebar")


pg.run()