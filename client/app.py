import streamlit as st

st.set_page_config(page_title="Voice Chat", layout="wide", page_icon=":material/record_voice_over:")

pg = st.navigation([
        # st.Page("webpages/pg_chat.py", title="Chat", icon=":material/voice_chat:"),
        st.Page("webpages/pg_settings.py", title="Character Settings", icon=":material/tune:"),
        st.Page("webpages/pg_voice_settings.py", title="Voice Settings", icon=":material/settings_voice:"),
        st.Page("webpages/pg_usage.py", title="Usage report", icon=":material/home:"),
    ], position="sidebar")


pg.run()