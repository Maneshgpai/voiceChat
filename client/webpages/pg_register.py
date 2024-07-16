import streamlit as st
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import hmac
from dotenv import load_dotenv
import os
import requests
import json
load_dotenv()

if "firestore_db" not in st.session_state:
    db = firestore.Client.from_service_account_json("firestore_key.json")
else:
    db = st.session_state["firestore_db"]

ist = timezone(timedelta(hours=5, minutes=30))
# voice_api_key = os.getenv("ELEVENLABS_API_KEY")

# if "status" not in st.session_state:
#     st.session_state.status = st.session_state.get("status", "unverified")
# if "voice_id_disabled" not in st.session_state:
#     st.session_state["voice_id_disabled"] = False
# if "voice_id_val" not in st.session_state:
#     st.session_state["voice_id_val"] = ""
#     print("********* 1 st.session_state['voice_id_val']:", st.session_state["voice_id_val"])

# def check_password():
#     if hmac.compare_digest(st.session_state.password, os.getenv("LOGIN_PASSWORD")):
#         st.session_state.status = "verified"
#     else:
#         st.session_state.status = "incorrect"
#     st.session_state.password = ""
# def login_prompt():
#     st.text_input("Enter password:", key="password", type="password", on_change=check_password)
#     if st.session_state.status == "incorrect":
#         st.warning("Incorrect password. Please try again.")
# def validate_voice_id():
#     print(f"pg_settings > validate_voice_id > {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Validating Voice ID: {st.session_state.voice_id}")
#     url = f"https://api.elevenlabs.io/v1/voices/{st.session_state.voice_id}"
#     headers = {
#         "Accept": "application/json",
#         "xi-api-key": voice_api_key
#     }
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         st.session_state["voice_id_disabled"] = True
#         st.session_state["voice_id_val"] = st.session_state.voice_id
#         print(f"pg_settings > validate_voice_id > {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Voice ID VALIDATED")
#     else:
#         st.session_state["voice_id_disabled"] = False
#         st.warning("Invalid Voice ID. Please try again.")
# def set_voice_setting(voice_id):
#     new_voice_setting = {"model": st.session_state.model,
#         "temperature": st.session_state.temperature,
#         "prompt": st.session_state.prompt,
#         "negative_prompt": st.session_state.negative_prompt,
#         "response_rules": st.session_state.response_rules,
#         "prompt_tail": st.session_state.prompt_tail,
#         "character_name": st.session_state.character_name,
#         "language": st.session_state.language,
#         "verbosity": st.session_state.verbosity,
#         "user_context": st.session_state.user_context,
#         "voice_stability": st.session_state.voice_stability,
#         "voice_similarity_boost": st.session_state.voice_similarity_boost,
#         "voice_style": st.session_state.voice_style,
#         "voice_use_speaker_boost": st.session_state.voice_use_speaker_boost}
    
#     print(f"pg_settings > set_voice_setting > Setting Updated Voice Setting")
#     st.session_state["context"] = new_voice_setting
#     db.collection('voiceClone_characters').document(voice_id).set({
#         "last_updated_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),
#         "name":st.session_state.character_name,
#         "voice_id":voice_id,
#         "setting":new_voice_setting})
#     st.success("Setting updated successfully!")
# def reset_model_setting():
#     for setting, value in st.session_state["context"].items():
#         # print(setting, value)
#         if setting == "model":
#             model = value
#         elif setting == "temperature":
#             temperature = value
#     return model, temperature
# def reset_prompt_setting():
#     for setting, value in st.session_state["context"].items():
#         if setting == "prompt":
#             return value
# def reset_negative_prompt_setting():
#     for setting, value in st.session_state["context"].items():
#         if setting == "negative_prompt":
#             return value
# def reset_response_rules_setting():
#     for setting, value in st.session_state["context"].items():
#         if setting == "response_rules":
#             return value
# def reset_prompt_tail_setting():
#     for setting, value in st.session_state["context"].items():
#         if setting == "prompt_tail":
#            return value
# def reset_name_lang_verbosity_setting():
#     for setting, value in st.session_state["context"].items():
#         if setting == "character_name":
#             character_name = value
#         elif setting == "language":
#             language = value
#         elif setting == "verbosity":
#             verbosity = value
#     return character_name, language, verbosity
# def reset_user_context_setting():
#     for setting, value in st.session_state["context"].items():
#         if setting == "user_context":
#             return value
# def reset_voice_setting():
#     for setting, value in st.session_state["context"].items():
#         if setting == "voice_stability":
#             voice_stability = value
#         elif setting == "voice_similarity_boost":
#             voice_similarity_boost = value
#         elif setting == "voice_style":
#             voice_style = value
#         elif setting == "voice_use_speaker_boost":
#             voice_use_speaker_boost = value
#     return voice_stability, voice_similarity_boost, voice_style, voice_use_speaker_boost
# def get_voice_setting(voice_id):
#     print("pg_settings >> get_voice_setting")
#     ## If exists, fetch settings from DB
#     setting = db.collection('voiceClone_characters').document(voice_id)
#     doc = setting.get()
#     voice_setting = {}
#     if doc.exists:
#         print("pg_settings >> get_voice_setting > Fetching voice settings from DB")
#         setting = doc.to_dict()
#         # print("pg_settings >> get_voice_setting > Voice settings from DB as Dict:",setting)
#         for k, v in setting.items():
#             if k == 'setting':
#                 voice_setting = v
#     else:
#         print("pg_settings >> get_voice_setting > Fetching default voice settings from config files")
#         voice_setting = json.loads(os.getenv("DEFAULT_VOICE_SETTING"))
#         print("pg_settings >> get_voice_setting > Default voice settings:",voice_setting)
#         db.collection('voiceClone_characters').document(voice_id).set({
#             "last_updated_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),
#             "name":voice_setting['character_name'],
#             "voice_id":voice_id,
#             "setting":voice_setting,
#             "action":"created_new_profile"})

#     return voice_setting
# def render_setting_pg(context):
#     # context = 
#     # if "context" not in st.session_state:
#     #     context = get_voice_setting()
#     #     print(f"pg_settings > render_setting_pg > context not in session. Getting it from DB: {context}")
#     #     st.session_state["context"] = context
#     # else:
#     #     context = st.session_state["context"]

#     model  = context['model']
#     temperature = float(context['temperature'])
#     prompt  = context['prompt']
#     negative_prompt  = context['negative_prompt']
#     response_rules = context['response_rules']
#     prompt_tail = context['prompt_tail']
#     character_name  = context['character_name']
#     language  = context['language']
#     verbosity  = context['verbosity']
#     user_context  = context['user_context']
#     voice_stability  = float(context['voice_stability'])
#     voice_similarity_boost  = float(context['voice_similarity_boost'])
#     voice_style  = float(context['voice_style'])
#     voice_use_speaker_boost = context['voice_use_speaker_boost']

#     # if bool(context): ## If there is value saved in DB, set it on load
#     #     print(f"pg_settings > render_setting_pg > Setting DB values for setting")
#     #     model  = context['model']
#     #     temperature = context['temperature']
#     #     prompt  = context['prompt']
#     #     negative_prompt  = context['negative_prompt']
#     #     response_rules = context['response_rules']
#     #     prompt_tail = context['prompt_tail']
#     #     character_name  = context['character_name']
#     #     language  = context['language']
#     #     verbosity  = context['verbosity']
#     #     user_context  = context['user_context']
#     #     voice_stability  = context['voice_stability']
#     #     voice_similarity_boost  = context['voice_similarity_boost']
#     #     voice_style  = context['voice_style']
#     #     voice_use_speaker_boost  = context['voice_use_speaker_boost']
#     # else: ## Else assign default values
#     #     print(f"pg_settings > render_setting_pg > Setting default values for setting")
#     #     model, temperature = reset_model_setting()
#     #     prompt = reset_prompt_setting()
#     #     negative_prompt = reset_negative_prompt_setting()
#     #     response_rules = reset_response_rules_setting()
#     #     prompt_tail = reset_prompt_tail_setting()
#     #     character_name, language, verbosity = reset_name_lang_verbosity_setting()
#     #     user_context = reset_user_context_setting()
#     #     voice_stability, voice_similarity_boost, voice_style, voice_use_speaker_boost = reset_voice_setting()

#     ## Set on load values for dropdowns
#     dropdown_val_model = ["gpt-3.5-turbo", "gpt-4o"]#, "claude-3-5-sonnet-20240620"]
#     index_model = 1
#     for i, item in enumerate(dropdown_val_model):
#         if item == model:
#             index_model = i
#     dropdown_val_lang = ["Hinglish", "Tanglish", "Hindi", "English", "Tamil"]
#     index_lang = 4
#     for i, item in enumerate(dropdown_val_lang):
#         if item == language:
#             index_lang = i
#     dropdown_val_verbosity = ["Concise", "Detailed"]
#     index_verbosity = 0
#     for i, item in enumerate(dropdown_val_verbosity):
#         if item == verbosity:
#             index_verbosity = i

#     ## Populate setting form
#     with st.form("setting_form"): 
#         ## Setting LLM Parameters: model and temperature
#         with st.expander("Models", expanded=False, icon=":material/psychology:"):
#             col1, col2 = st.columns([1,1], gap="medium")
#             with col1:
#                 st.selectbox("LLM", dropdown_val_model, index=index_model, key="model",label_visibility="visible", help="Choose from different LLM models. Default = gpt-4o")
#             with col2:
#                 st.slider("Prompt Adherence", min_value=0.0, max_value=1.0, value=temperature, step=0.1, key="temperature", help="Degree of creativity and rendomness in the model responses. Higher number lets the A.I be more creative. Default = 0.7")
#         ## Setting LLM Prompt parameters: prompt, response rules, exclusion rules and additional guideline for prompt rule in prompt_tail
#         with st.expander("Prompt", expanded=False, icon=":material/edit_note:"):
#             col1,col2 = st.columns([9,1])
#             with col1:
#                 st.text_area("Prompt",value=prompt, key="prompt", label_visibility="collapsed", help="The Description for how you want the response to be.")
#             with col2:
#                 with st.popover("?", use_container_width=True):
#                     st.caption(reset_prompt_setting())

#         with st.expander("Response Rules", expanded=False, icon=":material/rule:"):
#             col1,col2 = st.columns([9,1])
#             with col1:
#                 st.text_area("Response Rules",value=response_rules, key="response_rules", label_visibility="collapsed", help="Rules to be followed by AI to have an enganged and human like conversation.")
#             with col2:
#                 with st.popover("?", use_container_width=True):
#                     st.caption(reset_response_rules_setting())

#         with st.expander("Negative Prompt", expanded=False, icon=":material/backspace:"):
#             col1,col2 = st.columns([9,1])
#             with col1:
#                 st.text_area("Negative Prompt",value=negative_prompt, key="negative_prompt", label_visibility="collapsed", help="The Description for how you want the response to be.")
#             with col2:
#                 with st.popover("?", use_container_width=True):
#                     st.caption(reset_negative_prompt_setting())

#         st.session_state["prompt_tail"] = prompt_tail

#         ## Setting user specifics: Language and user background 
#         with st.expander("Language & context", expanded=False, icon=":material/language:"):
#             col1, col2 = st.columns([1,1], gap="medium")
#             with col1:
#                 st.text_input("Character Name", value=character_name, key="character_name", help="Default = Name associated with the voice")
#                 st.selectbox("Language", dropdown_val_lang, index=index_lang, key="language", help="Default = Hinglish")
#             with col2:
#                 verbosity = st.selectbox("Verbosity Level", dropdown_val_verbosity, index=index_verbosity, key="verbosity", help="Default = Concise")

#             st.text_area("Background & context for the user",value=user_context, key="user_context",label_visibility="visible", help=f"Default = {reset_user_context_setting()}")

#         st.divider()
#         ## Setting Voice setting 
#         with st.expander("Advanced settings for the voice", expanded=False, icon=":material/settings_voice:"):
#             col1, col2 = st.columns([1,1], gap="medium")
#             with col1:
#                 st.slider("Stability", min_value=0.0, max_value=1.0, value=voice_stability, step=0.01, key="voice_stability", help="The stability slider determines how consistent the voice is and the level of randomness between each generation. Lower stability introduces a broader emotional range, while higher stability can lead to a more monotonous voice. Setting stability low means a wider range of randomization, often resulting in a more emotive performance, but this is also highly dependent on the voice itself. For a more lively and dramatic performance, it is recommended to set the stability slider lower and generate a few times until you find a performance you like. Default = 0.50")
#                 st.slider("Similarity Boost", min_value=0.0, max_value=1.0, value=voice_similarity_boost, step=0.01, key="voice_similarity_boost", help="This slider controls how closely the AI adheres to the original voice when attempting to replicate it. Setting it too high may reproduce artifacts or background noise if present in the original recording. Default = 0.75")
#             with col2:
#                 st.slider("Voice Style", min_value=0.0, max_value=1.0, value=voice_style, step=0.01, key="voice_style", help="This setting attempts to amplify the style of the original speaker. It's generally recommended to keep this setting at 0 at all times, as it can make the model slightly less stable as it strives to emphasize and imitate the style of the original voice. Default = 0.0")
#                 st.toggle("Speaker Boost", value=voice_use_speaker_boost, key="voice_use_speaker_boost", help="This setting boosts the similarity to the original speaker. While it can enhance similarity, it also increases computational load and latency. Mostly differences introduced by this setting are generally rather subtle. Default = Off")

#         return st.form_submit_button("Update setting", type="primary")
# def setting_pg(voice_id):
#     context = get_voice_setting(voice_id)
    
#     if "context" not in st.session_state:
#         st.session_state["context"] = context

#     st.subheader(f"Settings Page")
#     st.write(f"You are viewing the settings for character {context['character_name']}")
#     update = render_setting_pg(context)
#     if update:
#         set_voice_setting(voice_id)

def register_new_user():
    with st.form("new_user_register"):
        st.text_input("User Name", key="user_name", help="User Name should be unique id")
        st.text_input("Telegram ID", key="user_telegramid")
        return st.form_submit_button("Create profile", type="primary")

def check_duplicate(db, field_name, field_value):
    duplicate_flag = False
    collection_ref = db.collection('voiceClone_users')
    query = collection_ref.where(field_name, "==", field_value)#.where("population", ">", 1000000)
    docs = query.stream()
    for doc in docs:
        dict = doc.to_dict()
        if dict[field_name] == field_value:
            duplicate_flag = True
    return duplicate_flag

def is_user_name_unique(db ,user_name):
    if check_duplicate(db,'user_name', user_name):
        return "User ID already taken. Please choose another one"
    return True

def is_telegram_id_unique(db ,telegram_id):
    if check_duplicate(db,'telegram_id', telegram_id):
        return "Profile already exists for the given telegram id."
    return True

def is_telegram_id_valid(telegram_id):
    ## Send OTP to telegram number
    ## st.text_input("Input the OTP from Telegram", key="telegram_otp")
    ## Check if True or False
    return True

def create_new_user(user_name, telegram_id):
    db.collection('voiceClone_users').add({
    "created_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),
    "user_name":user_name,
    "telegram_id":telegram_id,
    "action":"created_new_user"})
def send_welcome_telegram_msg(telegram_id):
    return True

############# PAGE START #############
st.subheader("Create Profile")
st.caption(":red[Note: This is a mock login screen. There are not user checks. Please create only one unique user id & telegram id]")
form_submit = register_new_user()
if form_submit:
    if st.session_state.user_name != "" and st.session_state.user_telegramid != "":
        uname_msg = is_user_name_unique(db, st.session_state.user_name)
        print("uname_msg:",uname_msg)

        if uname_msg == True:
            tg_msg = is_telegram_id_unique(db, st.session_state.user_telegramid)
            if tg_msg == True:
                telegram_valid = is_telegram_id_valid(st.session_state.user_telegramid)
                if telegram_valid:
                    create_new_user(st.session_state.user_name, st.session_state.user_telegramid)
                    st.session_state["uname"] = st.session_state.user_name
                    st.session_state["user_telegram"] = st.session_state.user_telegramid
                    st.success(f"Signup successful! Welcome, {st.session_state.user_name}! You can now use your Telegram ID to access additional features.")
                    message_status = send_welcome_telegram_msg(st.session_state.user_telegramid)
                else:
                    st.error("Sorry, the given Telegram id cannot be authenticated.")                
            else:
                st.error(tg_msg)
        else:
            st.error(uname_msg)
    else:
        st.warning("Please fill in all fields")