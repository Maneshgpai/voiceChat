import streamlit as st

st.set_page_config(page_title="Voice Chat", page_icon=":material/record_voice_over:")

pg = st.navigation([
        # st.Page("webpages/pg_home.py", title="Home", icon=":material/home:"),
        st.Page("webpages/pg_register.py", title="Signup", icon=":material/person_add:"),
        st.Page("webpages/pg_chat.py", title="Chat", icon=":material/voice_chat:"),
        st.Page("webpages/pg_settings.py", title="Settings", icon=":material/tune:"),
    ], position="sidebar")


pg.run()