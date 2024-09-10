from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from groq import Groq
import replicate
from functions import functionSrvr as func
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import requests
import pandas as pd


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
voice_api_key = os.getenv("ELEVENLABS_API_KEY")
client = OpenAI(api_key=openai_api_key)
ist = timezone(timedelta(hours=5, minutes=30))
replicate_models = {"llama 3":"meta/meta-llama-3-70b-instruct", "llama 3.1":"meta/meta-llama-3.1-405b-instruct"}
groq_models = {"llama 3":"llama3-70b-8192", "llama 3.1":"llama-3.1-70b-versatile"}

def get_datetime():
    return (str(datetime.now())).replace('.','').replace(':','').replace(' ','').replace('-','')

def log(msg_id,status,status_cd,message,origin,db,db_document_name):
    log_response = {str(msg_id)+"_"+get_datetime(): {"status": status,"status_cd":status_cd,"message":message, "origin":origin, "message_id": msg_id, "timestamp":datetime.now(ist)}}
    log_ref = db.collection('log').document(db_document_name)
    func.createLog(log_ref, log_response)

def fetch_optimized_chat_hist_for_openai(message_hist):
    user_message = []
    for message in message_hist:
        if not message["content"]:
            message["content"] = ""
        user_message.append({
            "role": message["role"],
            "content": message["content"]
        })
    return user_message

def fetch_optimized_chat_hist_for_llama(message_hist):
    new_message_hist = ""
    for item in message_hist:
        if item.get('role') == 'user':
            u_msg = item.get('content', '')
            if u_msg is None:
                u_msg = ""
            new_message_hist += "<|start_header_id|>user<|end_header_id|>"+u_msg.strip().replace("\n","\\n")+"<|eot_id|>"
        elif item.get('role') == 'assistant':
            a_msg = item.get('content', '')
            if a_msg is None:
                a_msg = ""
            new_message_hist += "<|start_header_id|>assistant<|end_header_id|>"+a_msg.strip().replace("\n","\\n")+"<|eot_id|>"
    return new_message_hist

def fn_reduce_message_hist(ideal_size,curr_size,message_hist):
    ## Calculate by how much the size should be reduced 
    reduce_msg_hist_by =round((ideal_size/curr_size),2)
    print(f"{datetime.now(ist)} textResponseSrvr > fn_reduce_message_hist: % of size to be reduced from msg history: ",reduce_msg_hist_by)

    ## Convert into Panda dataframe for easier and quicker manipulation
    df = pd.DataFrame(message_hist)
    print(f"{datetime.now(ist)} textResponseSrvr > fn_reduce_message_hist: Total # of msg from history: ",len(df))

    smaller_message_hist_size = round(len(df) * reduce_msg_hist_by)
    print(f"{datetime.now(ist)} textResponseSrvr > fn_reduce_message_hist: # msg to consider: ",smaller_message_hist_size)
    
    ## Sort by time in desc order, to pick the latest messages
    df_sorted = df.sort_values(by='timestamp', ascending=False)

    ################ HARDCODING TO PICK ONLY LAST 31 messages ################
    smaller_message_hist_size = 31

    ## Pick the smaller number of latest messages
    smaller_message_hist_df = df_sorted.head(smaller_message_hist_size)

    ## Sorting to original order
    smaller_message_hist_df = smaller_message_hist_df.sort_values(by='timestamp', ascending=True)

    ## Convert type of return object, from dataframe to List of Dict 
    smaller_message_hist = smaller_message_hist_df.to_dict(orient='records')

    ## Return smaller message history
    return smaller_message_hist

def google_translate_text(text,target_lang_cd, db, db_document_name, msg_id):
    # print(f"************** textResponseSrvr > google_translate_text > text:{text}, target_lang_cd:{target_lang_cd}")
    API_KEY = os.environ['GOOGLE_API_KEY']
    url = "https://translation.googleapis.com/language/translate/v2" 
    params = {
            'q': text,
            # 'source': 'en-us',
            'target': target_lang_cd,
            'key': API_KEY
        }
    response = requests.get(url, params=params)
    # Check if the request was successful
    if response.status_code == 200:
        translation = response.json()['data']['translations'][0]['translatedText']
        print(f'Translated text: {translation}')
    else:
        error = "Error: Exception in Google Translate. Defaulting to English"
        translation = text
        # print("************** textResponseSrvr > google_translate_text > error:",error)
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":"google_translate_text", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)

    return translation
def translate(audio_file,msg_id, db_document_name, db):
    try:
        translation = client.audio.translations.create(
            model="whisper-1", 
            file=audio_file
            )
        return translation.text
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":"translate_whisper-1", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)

def convert_voice_to_text(voice_file, system_prompt, db_document_name, db, msg_id):
    try:
        audio_file= open(voice_file, "rb")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": translate(audio_file, msg_id, db_document_name, db)
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":"convert_voice_to_text", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)

# @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), retry=retry_if_exception_type(ConnectionError))
# def get_huggingface_response(model, query, system_prompt, message_hist, db, db_document_name, voice_settings):
#     try:
#         final_prompt = system_prompt.replace("\n","\\n")
#         for item in message_hist:
#             chat_history += ' '.join(f"{item.get('role')}: {item.get('content', '')}")

#         input_text = final_prompt + ' ' + chat_history + ' user: ' + query
#         parameters = {
#             "top_k": voice_settings['top_k'], #1,
#             "top_p": voice_settings['top_p'], #0.8,
#             "max_length": voice_settings['max_tokens'], #100,
#             "min_length": voice_settings['min_tokens'], #10,
#             "temperature": voice_settings['temperature'], #1,
#             "repetition_penalty": voice_settings['frequency_penalty'], 
#             "max_time": 120
#             # "prompt": new_message_hist,
#             # "system_prompt": final_prompt,
#             # "length_penalty": voice_settings['length_penalty'], #0.1,
#             # "stop_sequences": "<|end_of_text|>,<|eot_id|>",
#             # "prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_prompt}<|eot_id|>{prompt}<|start_header_id|>assistant<|end_header_id|>",
#             # "presence_penalty": voice_settings['presence_penalty'], #0.1,
#             # "frequency_penalty": voice_settings['frequency_penalty'], #0.9,
#             # "log_performance_metrics": False

#         }

#         # api_key = "your_huggingface_api_key"
#         # model = "your_model/llama3"  # Replace with the exact model name or repository ID
#         # api = InferenceApi(repo_id=model, token=api_key)
#         # response = api(inputs=input_text, parameters=parameters)

#         if model == "llama 3":
#             replicate_model = "meta/meta-llama-3-70b-instruct"
#         elif model == "llama 3.1":
#             replicate_model = "meta/meta-llama-3.1-405b-instruct"

#         API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B"
#         API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3.1-8B"
#         headers = {"Authorization": "Bearer hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}

#         payload = {
#             "inputs": input_text,
#             "parameters": parameters
#         }
#         response = requests.post(API_URL, headers=headers, json=payload)
#         assistant_reply = response.get("generated_text", ":)")

#         print("textResponseSrvr > get_huggingface_response > response.json():",response.json())
#         print("textResponseSrvr > get_huggingface_response > assistant_reply:",assistant_reply)
#         # return response.json()
#         # return assistant_reply

#     except Exception as e:
#         error = "Error: {}".format(str(e))
#         print("textResponseSrvr > get_huggingface_response > error:",error)
#         log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":"get_huggingface_response", "message_id": msg_id, "timestamp":datetime.now(ist)}}
#         log_ref = db.collection('log').document(db_document_name)
#         func.createLog(log_ref, log_response)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), retry=retry_if_exception_type(ConnectionError))
def get_groq_response(system_prompt, message_hist, db, db_document_name, voice_settings, msg_id, voice_or_text):
    try:
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        groq_model = groq_models.get(voice_settings['model'].lower(), "llama 3")
        system_message = [{"role": "system", "content": system_prompt}]

        user_message = fetch_optimized_chat_hist_for_openai(message_hist)

        chat_completion = groq_client.chat.completions.create(messages=system_message+user_message,
            model=groq_model,
            temperature=voice_settings['temperature'],
            max_tokens=1024,
            top_p=0.2,
            stop=None,
            stream=False,)
        print(f"COST: Text response for Llama via Groq:\n{chat_completion}\n")
        return chat_completion.choices[0].message.content

    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":voice_or_text+".get_groq_response", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), retry=retry_if_exception_type(ConnectionError))
def get_replicate_response(model, query, system_prompt, message_hist, db, db_document_name, voice_settings, msg_id, voice_or_text):
    try:
        replicate_model = replicate_models.get(model, "llama 3")
        final_prompt = system_prompt.replace("\n","\\n")
        query = query.replace("\n","\\n")
        
        new_message_hist = fetch_optimized_chat_hist_for_llama(message_hist)
        
        ## For Llama3 calls, the total context window is 8k tokens. 
        ## So we add logic to pick only the latest chats from the message history, which fit within this context size.
        llama3_max_context_size = 7000 ##Size for Llama3. Taking 10% lesser than max allowed for contingency
        if model == "llama 3":
            ## Calculate size of message history
            new_message_hist_size = func.calculate_tokens(model, new_message_hist, db, db_document_name, msg_id)
            log_msg = f"COST: Text response for Llama via Replicate> Token size of msg_hist BEFORE: {new_message_hist_size}"
            log(msg_id,"logging",200,log_msg,voice_or_text+".get_replicate_response",db,db_document_name)

            ## Considering the size of max context window of Llama further gets reduced with user query & system prompt. 
            # So dynamically calculating remaining size available message history
            ideal_message_hist_size = llama3_max_context_size - (func.calculate_tokens(model, query, db, db_document_name, msg_id)+func.calculate_tokens(model, final_prompt, db, db_document_name, msg_id))
            log_msg = f"COST: Text response for Llama via Replicate> Token size of msg_hist IDEAL SIZE per availablity: {ideal_message_hist_size}"
            log(msg_id,"logging",200,log_msg,voice_or_text+".get_replicate_response",db,db_document_name)
            
            ## If message history size exceeds the available window size, then reduce the msg history size by taking only latest messages
            if new_message_hist_size > ideal_message_hist_size:
                shorter_message_hist = fn_reduce_message_hist(ideal_message_hist_size,new_message_hist_size,message_hist)
                log_msg = f"COST: Text response for Llama via Replicate> Token size of msg_hist AFTER shortening, before adding headers: {func.calculate_tokens(model, str(shorter_message_hist), db, db_document_name, msg_id)}"
                log(msg_id,"logging",200,log_msg,voice_or_text+".get_replicate_response",db,db_document_name)
                new_message_hist = fetch_optimized_chat_hist_for_llama(shorter_message_hist)

        log_msg = f"COST: Text response for Llama via Replicate> Token size of msg_hist AFTER: ",func.calculate_tokens(model, new_message_hist, db, db_document_name, msg_id)
        log(msg_id,"logging",200,log_msg,voice_or_text+".get_replicate_response",db,db_document_name)

        full_text = []
        for event in replicate.stream(
                replicate_model,
                input={
                    "top_k": voice_settings['top_k'], #1,
                    "top_p": voice_settings['top_p'], #0.8,
                    "prompt": new_message_hist,
                    "max_tokens": voice_settings['max_tokens'], #100,
                    "min_tokens": voice_settings['min_tokens'], #10,
                    "temperature": voice_settings['temperature'], #1,
                    "system_prompt": final_prompt,
                    "length_penalty": voice_settings['length_penalty'], #0.1,
                    "stop_sequences": "<|end_of_text|>,<|eot_id|>",
                    "prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_prompt}<|eot_id|>{prompt}<|start_header_id|>assistant<|end_header_id|>",
                    "presence_penalty": voice_settings['presence_penalty'], #0.1,
                    "frequency_penalty": voice_settings['frequency_penalty'], #0.9,
                    "repetition_penalty": voice_settings['repetition_penalty'],
                    "log_performance_metrics": False
                },
            ):
                full_text.append(str(event))
        response = ''.join(full_text)
        response_tot_token = func.calculate_tokens(model, response, db, db_document_name, msg_id)

        log_msg = f"COST: Text response for Llama via Replicate> response_tot_token:{response_tot_token}"
        log(msg_id,"logging",200,log_msg,voice_or_text+".get_replicate_response",db,db_document_name)


    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":voice_or_text+".get_replicate_response", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)
        response = get_groq_response(system_prompt, message_hist, db, db_document_name, voice_settings,msg_id,voice_or_text)

    return response
def get_openai_response(model, system_message, message_hist, db, db_document_name, voice_settings,msg_id, voice_or_text):
    try:
        user_message = fetch_optimized_chat_hist_for_openai(message_hist)
        response = client.chat.completions.create(
            model=model,
            messages=system_message+user_message,
            stream=False,
            frequency_penalty = voice_settings['frequency_penalty'], #2, # Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
            max_tokens = voice_settings['max_tokens'],
            top_p = voice_settings['top_p'], # 0.8, # An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both.
            presence_penalty = voice_settings['presence_penalty'], #1.5, # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
            temperature=voice_settings['temperature'], #1.2 # What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
        )
        full_response = response.choices[0].message.content
        print(f"COST: Text response for Llama via OpenAI> number_of_tokens: {response.usage.total_tokens}")
        return full_response
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":voice_or_text+".get_openai_response","message_id":msg_id,"timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)
def get_system_prompt(voice_settings, voice_or_text):
    prompt  = voice_settings['prompt']
    negative_prompt  = voice_settings['negative_prompt']
    response_rules = voice_settings['response_rules']
    prompt_tail = voice_settings['prompt_tail']
    character_name  = voice_settings['character_name']
    language  = voice_settings['language']
    verbosity  = voice_settings['verbosity']
    user_context  = voice_settings['user_context']

    if language == "Hinglish":
        if voice_or_text == "voice":
            lang_prompt = "You have to respond in Hindi language."
        else:
            lang_prompt = "You have to respond in Hinglish. This a blend of Hindi and English, in particular a variety of English used by speakers of Hindi, characterized by frequent use of Hindi vocabulary or constructions. It is a mixture of the languages Hindi and English, especially the type of English used by speakers of Hindi."
    elif language == "Tanglish":
        if voice_or_text == "voice":
            lang_prompt = "You have to respond in Tamil language."
        else:
            lang_prompt = "You have to respond in Tanglish. This a blend of Tamil and English, in particular a variety of English used by speakers of Tamil, characterized by frequent use of Tamil vocabulary or constructions. It is a mixture of the languages Tamil and English, especially the type of English used by speakers of Tamil."
    else:
        lang_prompt = f"You have to respond in {language} language."

    final_prompt = f"Your name is {character_name} and you are from India. It is {datetime.now(ist)} now in India. Always be aware of the time with respect to your context, while replying."\
        +lang_prompt+". "+prompt+". "+response_rules+". "+negative_prompt+". "+prompt_tail+". "\
                +f"Your responses should be {verbosity}."
    if not(user_context == "Nothing defined yet") or not(user_context == ""):
        final_prompt = final_prompt + f"A brief background about you is given as below:"+user_context
    return final_prompt

def get_agent_response(query, voice_settings, message_hist, db, db_document_name,msg_id, voice_or_text):
    final_prompt = get_system_prompt(voice_settings, voice_or_text)
    model  = voice_settings['model']

    full_response = ""
    if model == "gpt-4o" or model == "gpt-4o-mini":
        system_message = [{"role": "system", "content": final_prompt}]
        try:
            full_response = get_openai_response(model, system_message, message_hist, db, db_document_name, voice_settings, msg_id, voice_or_text)
        except Exception as e:
            error = "Error: {}".format(str(e))
            log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":voice_or_text+".get_agent_response", "message_id": msg_id, "timestamp":datetime.now(ist)}}
            log_ref = db.collection('log').document(db_document_name)
            func.createLog(log_ref, log_response)
    elif model == "llama 3" or model == "llama 3.1":
        full_response = get_replicate_response(voice_settings['model'], query, final_prompt, message_hist, db, db_document_name, voice_settings, msg_id, voice_or_text)

    print(f"{datetime.now(ist)} textResponseSrvr > get_agent_response: from {model}: {full_response}")
    return full_response
