import streamlit as st
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import hmac
from dotenv import load_dotenv
import os
import requests
import json
import pandas as pd
load_dotenv()

if "firestore_db" not in st.session_state:
    db = firestore.Client.from_service_account_json(str(os.getenv("SECRETS_PATH")+"/firestore_key_agent.json"))
else:
    db = st.session_state["firestore_db"]

ist = timezone(timedelta(hours=5, minutes=30))
voice_api_key = os.getenv("ELEVENLABS_API_KEY")

if "status" not in st.session_state:
    # st.session_state.status = st.session_state.get("status", "unverified")
    st.session_state.status = st.session_state.get("status", "verified")
if "voice_id_disabled" not in st.session_state:
    st.session_state["voice_id_disabled"] = False
if "action_setting" not in st.session_state:
    st.session_state["action_setting"] = ""
if "voice_id_val" not in st.session_state:
    st.session_state["voice_id_val"] = ""
    # print("********* 1 st.session_state['voice_id_val']:", st.session_state["voice_id_val"])

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
def validate_voice_id():
    url = f"https://api.elevenlabs.io/v1/voices/{st.session_state.voice_id}"
    headers = {
        "Accept": "application/json",
        "xi-api-key": voice_api_key
    }
    response = requests.get(url, headers=headers)
    
    # if 'voice_id' not in st.session_state:
    #     st.session_state.voice_id = st.session_state['voice_id']

    if response.status_code == 200:
        # voice_data = response.json()
        # voice_name = voice_data.get("name")
        # st.session_state["voice_name"] = voice_name
        st.session_state["voice_id_disabled"] = True
        st.session_state["voice_id_val"] = st.session_state.voice_id
    else:
        st.session_state["voice_id_disabled"] = False
        st.warning("Invalid Voice ID. Please try again.")
        # return False
def set_character_setting(char_id):
    ## Default language 'Hinglish' is used in Prompt, Negative prompt & Response rules. It has been noticed sometimes the default Hinglish is missed to be replaced in all places. So below code is to fix replace any if missed.
    prompt = st.session_state.prompt
    negative_prompt = st.session_state.negative_prompt
    response_rules = st.session_state.response_rules
    if st.session_state.language != 'Hinglish':
        prompt = prompt.replace("Hinglish", st.session_state.language)
        negative_prompt = negative_prompt.replace("Hinglish", st.session_state.language)
        response_rules = response_rules.replace("Hinglish", st.session_state.language)

    new_voice_setting = {"model": st.session_state.model,
        "temperature": st.session_state.temperature,
        "top_k": st.session_state.top_k,
        "top_p": st.session_state.top_p,
        "max_tokens": st.session_state.max_tokens,
        "min_tokens": st.session_state.min_tokens,
        "length_penalty": st.session_state.length_penalty,
        "presence_penalty": st.session_state.presence_penalty,
        "frequency_penalty": st.session_state.frequency_penalty,
        "repetition_penalty": st.session_state.repetition_penalty,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "response_rules": response_rules,
        "prompt_tail": st.session_state.prompt_tail,
        "character_name": st.session_state.character_name,
        "character_descr":st.session_state.character_descr,
        "bot_token":st.session_state.bot_token,
        "reachout_prompt":st.session_state.reachout_prompt,
        "welcome_msg":st.session_state.welcome_msg,
        "voice_id":st.session_state.voice_id,
        "language": st.session_state.language,
        "verbosity": st.session_state.verbosity,
        "user_context": st.session_state.user_context,
        "voice_stability": st.session_state.voice_stability,
        "voice_similarity_boost": st.session_state.voice_similarity_boost,
        "voice_style": st.session_state.voice_style,
        "voice_tts": st.session_state.voice_tts,
        "voice_use_speaker_boost": st.session_state.voice_use_speaker_boost}
    # print(f"pg_settings >> set_character_setting > Setting Updated Character Settings")
    st.session_state["character_setting"] = new_voice_setting

    if char_id == 'default_char_id':
        # print("pg_settings >> set_character_setting > Creating document with auto generated doc id")
        db.collection('voiceClone_characters').document().set({
            "last_updated_on": datetime.now(ist),
            "name":st.session_state.character_name,
            "character_descr":st.session_state.character_descr,
            "voice_id":st.session_state.voice_id,
            "setting":new_voice_setting})
    else:
        # print(f"pg_settings >> set_character_setting > Creating document with {char_id} as doc id")
        db.collection('voiceClone_characters').document(char_id).set({
            "last_updated_on": datetime.now(ist),
            "name":st.session_state.character_name,
            "character_descr":st.session_state.character_descr,
            "voice_id":st.session_state.voice_id,
            "setting":new_voice_setting})
    st.success("Setting updated successfully!")
def reset_model_setting():
    for setting, value in st.session_state["character_setting"].items():
        # print(setting, value)
        if setting == "model":
            model = value
        elif setting == "temperature":
            temperature = value
    return model, temperature
def reset_prompt_setting():
    for setting, value in st.session_state["character_setting"].items():
        if setting == "prompt":
            return value
def reset_negative_prompt_setting():
    for setting, value in st.session_state["character_setting"].items():
        if setting == "negative_prompt":
            return value
def reset_response_rules_setting():
    for setting, value in st.session_state["character_setting"].items():
        if setting == "response_rules":
            return value
def reset_prompt_tail_setting():
    for setting, value in st.session_state["character_setting"].items():
        if setting == "prompt_tail":
           return value
def reset_name_lang_verbosity_setting():
    for setting, value in st.session_state["character_setting"].items():
        if setting == "character_name":
            character_name = value
        elif setting == "language":
            language = value
        elif setting == "verbosity":
            verbosity = value
    return character_name, language, verbosity
def reset_user_context_setting():
    for setting, value in st.session_state["character_setting"].items():
        if setting == "user_context":
            return value
def reset_voice_setting():
    for setting, value in st.session_state["character_setting"].items():
        if setting == "voice_stability":
            voice_stability = value
        elif setting == "voice_similarity_boost":
            voice_similarity_boost = value
        elif setting == "voice_style":
            voice_style = value
        elif setting == "voice_use_speaker_boost":
            voice_use_speaker_boost = value
    return voice_stability, voice_similarity_boost, voice_style, voice_use_speaker_boost
def get_char_setting(char_id):
    ## If exists, fetch settings from DB
    setting = db.collection('profile').document(char_id)
    doc = setting.get()
    char_setting = {}
    if doc.exists:
        # print("pg_settings >> get_char_setting > Data exists for the character in DB.")
        setting = doc.to_dict()
        for k, v in setting.items():
            if k == 'setting':
                print(v)
                char_setting = v
    else:
        # print("pg_settings >> get_char_setting > New Character. Fetching default voice settings from config files")
        char_setting = json.loads(os.getenv("DEFAULT_CHARACTER_SETTING"))

    # print("pg_settings >> get_char_setting > Succesfully fetched character setting")


    return char_setting
def validate_character_setting():
    if st.session_state.character_name == "":
        return "Character Name field should not be empty"
    elif st.session_state.character_descr == "":
        return "Character description field should not be empty"
    elif st.session_state.user_context == "":
        return "Background & context field should not be empty"
    elif st.session_state.prompt == "":
        return "Prompt field should not be empty"
    elif st.session_state.bot_token == "":
        return "Populate the Telegram token associated with this character"
    elif st.session_state.reachout_prompt    == "":
        return "Reach out prompt should not be empty"
    else:
        return True
def render_setting_pg(action, context):
    character_name  = context['character_name']
    character_descr = context.get('character_descr', '<Not provided!>')
    bot_token = context['bot_token']
    reachout_prompt = context['reachout_prompt']
    welcome_msg = context['welcome_msg']
    voice_id = context.get('voice_id', '<Not provided!>')
    language  = context['language']
    model  = context['model']
    temperature = float(context['temperature'])
    top_k =int(context['top_k'])
    top_p =float(context['top_p'])
    max_tokens =int(context['max_tokens'])
    min_tokens =int(context['min_tokens'])
    length_penalty =float(context['length_penalty'])
    presence_penalty =float(context['presence_penalty'])
    frequency_penalty =float(context['frequency_penalty'])
    repetition_penalty =float(context['repetition_penalty'])
    prompt  = context['prompt']
    negative_prompt  = context['negative_prompt']
    response_rules = context['response_rules']
    prompt_tail = context['prompt_tail']
    verbosity  = context['verbosity']
    user_context  = context['user_context']
    voice_stability  = float(context['voice_stability'])
    voice_similarity_boost  = float(context['voice_similarity_boost'])
    voice_style  = float(context['voice_style'])
    voice_tts = context.get('voice_tts')
    voice_use_speaker_boost = context['voice_use_speaker_boost']

    if (action == "create_new_char"):
        character_name = ""
        character_descr = ""
        prompt = ""
        user_context = ""
        bot_token = ""
        reachout_prompt = ""
        welcome_msg = ""

    ## Set on load values for dropdowns
    # dfsdf
    dropdown_val_model = ["gpt-4o-mini", "gpt-4o", "llama 3", "llama 3.1"]
    index_model = 1
    for i, item in enumerate(dropdown_val_model):
        if item == model:
            index_model = i
    dropdown_val_lang = ["German", "Hinglish", "English", "Hindi", "Bengali", "Tamil", "Gujarati", "Telugu", "Kannada", "Marathi", "Malayalam"]
    index_lang = 0
    for i, item in enumerate(dropdown_val_lang):
        if item == language:
            index_lang = i
    dropdown_val_verbosity = ["Concise", "Detailed"]
    index_verbosity = 0
    for i, item in enumerate(dropdown_val_verbosity):
        if item == verbosity:
            index_verbosity = i
    voice_df = get_all_voices()
    try:
        index_voice_name = voice_df[voice_df['Voice ID'] == voice_id].index[0]
    except Exception as e:
        error = "Error: {}".format(str(e))
        index_voice_name = 0
    
    ## Populate setting form
    with st.form("setting_form", border=False):
        ## Setting user specifics: Language and user background 
        ## Get all voice details from DB
        with st.expander("Name and background", expanded=False, icon=":material/manage_accounts:"):
            col1, col2, col3 = st.columns([1,1,1], gap="medium")
            with col1:
                st.text_input("Character Name", value=character_name, key="character_name", help="Default = Name associated with the voice")
            with col2:
                st.selectbox("Language", dropdown_val_lang, index=index_lang, key="language", help="Default = Hinglish")
            with col3:
                st.selectbox("Response Verbosity Level", dropdown_val_verbosity, index=index_verbosity, key="verbosity", help="Default = Concise")
            
            st.text_area("Character description (only for UI)",value=character_descr, key="character_descr", label_visibility="visible", help="Short Description of the character.")
            
            st.text_area("Welcome Message",value=welcome_msg, key="welcome_msg",label_visibility="visible", help="Default = Welcome message suited to the Character, in their own language. Tell who the character is, what can they do. Tell that they can text or send voice message.")
            st.text_area("Background & context of the character",value=user_context, key="user_context",label_visibility="visible", help="Default = User's background, story, personal details etc")

        with st.expander("Reachout Prompt & TG Token", expanded=False, icon=":material/manage_accounts:"):
            st.text_area("Reachout Prompt",value=reachout_prompt, key="reachout_prompt", label_visibility="visible", help="Prompt for reachouts.")
            st.text_input("Telegram token", value=bot_token, key="bot_token", help="Telegram token for the character")

        ## Setting LLM Parameters: model and temperature
        with st.expander("Models", expanded=False, icon=":material/psychology:"):
            st.selectbox("LLM", dropdown_val_model, index=index_model, key="model",label_visibility="visible", help="Cheapest is gpt-4o-mini")
            col1, col2 = st.columns([1,1], gap="medium")
            with col1:
                st.write("Parameters common to OpenAI and Meta Llama")
                st.slider("Temperature (Llama= 0 to 1, OpenAI= 0 to 2)", min_value=0.0, max_value=2.0, value=temperature, step=0.01, key="temperature", help="Llama=1, OpenAI=1.2")
                st.slider("frequency_penalty (Llama= 0 to +2, OpenAI=-2 to +2)", min_value=-2.0, max_value=2.0, value=frequency_penalty, step=0.01, key="frequency_penalty", help="Llama=0.9, OpenAI=2. Frequency penalty applies a penalty on the next token proportional to how many times that token already appeared in the response and prompt. The higher the frequency penalty, the less likely a word will appear again.")
                st.slider("top_p (Llama= 0 to +1, OpenAI= 0 to +1)", min_value=0.0, max_value=1.0, value=top_p, step=0.01, key="top_p", help="Degree of creativity for words and phrases choosen. Higher value means more adventurous choice of words, but at risk of sounding Off topic or Disjointed")
                st.number_input("max_tokens",min_value = 0, max_value=1000, value=max_tokens, step=1, key="max_tokens", help="Llama=100, OpenAI=100")
                st.slider("presence_penalty (Llama= 0 to +2, OpenAI=-2 to +2)", min_value=-2.0, max_value=2.0, value=presence_penalty, step=0.01, key="presence_penalty", help="The presence penalty also applies a penalty on repeated tokens but, unlike the frequency penalty, the penalty is the same for all repeated tokens. A token that appears twice and a token that appears 10 times are penalized the same.")
            with col2:
                st.write("Parameters only for Meta Llama")
                st.slider("top_k (Llama only)", min_value=0, max_value=100, value=top_k, step=1, key="top_k", help="Llama=80. Top_k influences how random the next token will be generated. Eg with slightly higher value, instead of word Happy, LLM might choose Elated. But high values might result in picking words which don't fit to the situation")
                st.number_input("min_tokens (Llama only)",min_value = 0, max_value=100, value=min_tokens, step=1, key="min_tokens", help="Llama=10")
                st.slider("length_penalty (Llama only)", min_value=0.0, max_value=2.0, value=length_penalty, step=0.01, key="length_penalty", help="Llama=0.1")
                st.slider("repetition_penalty (Llama only)", min_value=0.0, max_value=2.0, value=repetition_penalty, step=0.01, key="repetition_penalty", help="Degree of discouragement for repetitive or redundant output.")
                
        ## Setting LLM Prompt parameters: prompt, response rules, exclusion rules and additional guideline for prompt rule in prompt_tail
        with st.expander("Prompt", expanded=False, icon=":material/edit_note:"):
            col1,col2 = st.columns([9,1])
            with col1:
                st.text_area("Prompt",value=prompt, key="prompt", label_visibility="collapsed", help="The Description for how you want the response to be.")
            with col2:
                with st.popover("?", use_container_width=True):
                    st.caption(reset_prompt_setting())

        with st.expander("Response Rules", expanded=False, icon=":material/rule:"):
            col1,col2 = st.columns([9,1])
            with col1:
                st.text_area("Response Rules",value=response_rules, key="response_rules", label_visibility="collapsed", help="Rules to be followed by AI to have an enganged and human like conversation.")
            with col2:
                with st.popover("?", use_container_width=True):
                    st.caption(reset_response_rules_setting())

        with st.expander("Negative Prompt", expanded=False, icon=":material/backspace:"):
            col1,col2 = st.columns([9,1])
            with col1:
                st.text_area("Negative Prompt",value=negative_prompt, key="negative_prompt", label_visibility="collapsed", help="The Description for how you want the response to be.")
            with col2:
                with st.popover("?", use_container_width=True):
                    st.caption(reset_negative_prompt_setting())

        st.session_state["prompt_tail"] = prompt_tail

        st.divider()
        ## Setting Voice setting 
        with st.expander("Voice settings", expanded=False, icon=":material/settings_voice:"):
            st.write("Voices available in system:")
            st.selectbox("Voice TTS engine", ['elevenlabs','google'], key="voice_tts")
            st.table(data=voice_df.drop(['Voice ID'], axis=1))
            voice_name = st.selectbox("Selected voice", voice_df['Name'].tolist(),index=int(index_voice_name), key="voice_name")
            result = voice_df.loc[voice_df['Name'] == voice_name, 'Voice ID']
            st.session_state['voice_id'] = result.iloc[0]

        with st.expander("Advanced settings for the voice", expanded=False, icon=":material/tune:"):
            col1, col2 = st.columns([1,1], gap="medium")
            with col1:
                st.slider("Stability", min_value=0.0, max_value=1.0, value=voice_stability, step=0.01, key="voice_stability", help="The stability slider determines how consistent the voice is and the level of randomness between each generation. Lower stability introduces a broader emotional range, while higher stability can lead to a more monotonous voice. Setting stability low means a wider range of randomization, often resulting in a more emotive performance, but this is also highly dependent on the voice itself. For a more lively and dramatic performance, it is recommended to set the stability slider lower and generate a few times until you find a performance you like. Default = 0.60")
                st.slider("Similarity Boost", min_value=0.0, max_value=1.0, value=voice_similarity_boost, step=0.01, key="voice_similarity_boost", help="This slider controls how closely the AI adheres to the original voice when attempting to replicate it. Setting it too high may reproduce artifacts or background noise if present in the original recording. Default = 0.18")
            with col2:
                st.slider("Voice Style", min_value=0.0, max_value=1.0, value=voice_style, step=0.01, key="voice_style", help="This setting attempts to amplify the style of the original speaker. It's generally recommended to keep this setting at 0 at all times, as it can make the model slightly less stable as it strives to emphasize and imitate the style of the original voice. Default = 0.0")
                st.toggle("Speaker Boost", value=voice_use_speaker_boost, key="voice_use_speaker_boost", help="This setting boosts the similarity to the original speaker. While it can enhance similarity, it also increases computational load and latency. Mostly differences introduced by this setting are generally rather subtle. Default = Off")

        return st.form_submit_button("Update setting", type="primary")
def setting_pg(setting_action, char_id):
    if "character_setting" not in st.session_state:
        st.session_state["character_setting"] = get_char_setting(char_id)

    v_character_setting = st.session_state["character_setting"]

    col1, col2 = st.columns([2,1])
    with col1:
        if setting_action == "edit_existing_char":
            st.subheader(f"Edit Setting for {v_character_setting['character_name']} ({char_id})")
        else:
            st.subheader(f"Create New Character")
            st.caption(f"Options are pre-loaded with default values. Please review carefully before updating!")
    with col2:
        go_back = st.button("Edit another character")
    if go_back:
        with st.spinner('Loading...'):    
            del st.session_state["character_setting"]
            st.rerun()
        
    update = render_setting_pg(setting_action, v_character_setting)
    with st.spinner('Loading...'):
        if update:
            validate_stat = validate_character_setting()
            # print("******************* Clicked Update Setting. validate_stat:",validate_stat)
            if validate_stat == True:
                # print("******************* Update setting validated!")
                set_character_setting(char_id)
            else:
                # print("******************* Error in update setting")
                st.error(validate_stat)
def get_all_characters():
    users_ref = db.collection('profile')
    docs = users_ref.stream()
    user_data = []
    for doc in docs:
        char_id1 = doc.id
        user_info = doc.to_dict()
        name = user_info.get('name', '<Not given!>')
        character_descr = user_info.get('character_descr', '<Not given!>')
        user_data.append((name, character_descr, char_id1))
    df = pd.DataFrame(user_data, columns=['Character', 'About Me', 'ID'])
    return(df)
def get_all_voices():
    users_ref = db.collection('voice')
    docs = users_ref.stream()
    user_data = []
    for doc in docs:
        char_id1 = doc.id
        user_info = doc.to_dict()
        user_data.append((
            user_info.get('name', '<Not given!>'),
            user_info.get('gender', '<Not given!>'),
            user_info.get('age', '<Not given!>'),
            user_info.get('ethnicity', '<Not given!>'),
            user_info.get('language', '<Not given!>'),
            user_info.get('tags', '<Not given!>'),
            user_info.get('id', '<Not given!>')))
    df = pd.DataFrame(user_data, columns=['Name', 'Gender', 'Age', 'Ethnicity', 'Language', 'Tags', 'Voice ID'])
    return(df)
############# PAGE START #############

if st.session_state.status != "verified":
    login_prompt()
    st.stop()
else:
    # print("********* Session valid, password validated. ")
    if "character_setting" not in st.session_state:
        df = get_all_characters()
        print(f"*********** df:{df}")
        char_name = st.radio("Select existing character to edit", df['Character'].tolist(), index=0, key="character_nm", horizontal=True, label_visibility="visible")
        result = df.loc[df['Character'] == st.session_state.character_nm, 'About Me'].iloc[0]
        with st.expander(result[:30]+" ...", expanded=True):
            st.caption(result)

        edit_existing_char = st.button("Edit")
        if edit_existing_char:
            result = df.loc[df['Character'] == char_name, 'ID']
            char_id = result.iloc[0]
            character_setting = get_char_setting(char_id)
            ## Setting session variables : Voice ID, Voice Name, Voice Settings 
            st.session_state["char_id"] = char_id
            st.session_state["char_name"] = char_name
            st.session_state["character_setting"] = character_setting
            st.session_state["action_setting"] = "edit_existing_char"
            setting_pg("edit_existing_char", st.session_state["char_id"])
            st.rerun()
        st.divider()
        st.write("Or better, create new character")
        create_new_char = st.button("Create")
        if create_new_char:
            with st.spinner('Loading...'):
                st.session_state["char_id"] = "default_char_id"
                st.session_state["action_setting"] = "create_new_char"
                setting_pg("create_new_char", 'default_char_id')
                st.rerun()

    else:
        setting_pg(st.session_state["action_setting"], st.session_state["char_id"])


    # if st.session_state["voice_id_val"] != "":
    #     setting_pg(st.session_state["voice_id_val"])
    # else:
    #     st.text_input("Please enter Voice ID:", value=st.session_state["voice_id_val"], key="voice_id", on_change=validate_voice_id)
    
