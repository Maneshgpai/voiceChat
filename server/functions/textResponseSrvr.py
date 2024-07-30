from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from groq import Groq
import replicate
from functions import functionSrvr as func
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import requests


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
voice_api_key = os.getenv("ELEVENLABS_API_KEY")
client = OpenAI(api_key=openai_api_key)
ist = timezone(timedelta(hours=5, minutes=30))
groq_client = Groq()
API_KEY = os.environ['GOOGLE_API_KEY']

def google_translate_text(text,target_lang_cd, db, db_document_name):
    print(f"************** textResponseSrvr > google_translate_text > text:{text}, target_lang_cd:{target_lang_cd}")
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
        print("************** textResponseSrvr > google_translate_text > error:",error)
        log_response = {"status": "textResponseSrvr > get_agent_response > google_translate_text >> Error in Google Translate!","source_text":text,"status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

    return translation

def translate(audio_file):
    translation = client.audio.translations.create(
        model="whisper-1", 
        file=audio_file
        )
    return translation.text

def convert_voice_to_text(voice_file, system_prompt):
    audio_file= open(voice_file, "rb")
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": translate(audio_file)
            }
        ]
    )
    return response.choices[0].message.content


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), retry=retry_if_exception_type(ConnectionError))
def get_replicate_response(model, query, system_prompt, message_hist, db, db_document_name, voice_settings):
    try:
        final_prompt = system_prompt.replace("\n","\\n")
        query = query.replace("\n","\\n")
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
        # print(f"textResponseSrvr >> get_replicate_response > final_prompt:\n{final_prompt}\n")
        # print(f"textResponseSrvr >> get_replicate_response > new_message_hist:\n{new_message_hist}\n")

        # Explantion of parameters:
        # https://openrouter.ai/docs/parameters
        full_text = []
        for event in replicate.stream(
                model,
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
                    "log_performance_metrics": False
                },
            ):
                full_text.append(str(event))
        response = ''.join(full_text)
        return ''.join(full_text)
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("************** textResponseSrvr > get_replicate_response > error:",error)
        log_response = {"status": "textResponseSrvr > get_agent_response > get_replicate_response >> Error in Replicate Llama call!","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

def get_openai_response(model, system_message, message_hist, db, db_document_name, voice_settings):
    try:
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response > openai firing for {model}...\n")
        user_message = []
        for message in message_hist:
            if not message["content"]:
                message["content"] = ""
            user_message.append({
                "role": message["role"],
                "content": message["content"]
            })
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
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response > get_openai_response: from {model}: \n {full_response}")
        return full_response
    except Exception as e:
        error = "Error: {}".format(str(e))
        print("************** textResponseSrvr > get_openai_response > error:",error)
        log_response = {"status": "textResponseSrvr > get_agent_response > get_openai_response >> Error in OpenAI call!","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
        log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
        func.createLog(log_ref, log_response)

def get_agent_response(query, voice_settings, message_hist, db, db_document_name):
    print("************** textResponseSrvr > Entered get_agent_response")
    model  = voice_settings['model']
    temp = voice_settings['temperature']
    prompt  = voice_settings['prompt']
    negative_prompt  = voice_settings['negative_prompt']
    response_rules = voice_settings['response_rules']
    prompt_tail = voice_settings['prompt_tail']
    character_name  = voice_settings['character_name']
    language  = voice_settings['language']
    verbosity  = voice_settings['verbosity']
    user_context  = voice_settings['user_context']

    if language == "Hinglish":
        lang_prompt = "You have to respond in Hinglish. This a blend of Hindi and English, in particular a variety of English used by speakers of Hindi, characterized by frequent use of Hindi vocabulary or constructions. It is a mixture of the languages Hindi and English, especially the type of English used by speakers of Hindi."
    elif language == "Tanglish":
        lang_prompt = "You have to respond in Tanglish. This a blend of Tamil and English, in particular a variety of English used by speakers of Tamil, characterized by frequent use of Tamil vocabulary or constructions. It is a mixture of the languages Tamil and English, especially the type of English used by speakers of Tamil."
    else:
        lang_prompt = f"You have to respond in {language} language."

    final_prompt = f"Your name is {character_name} and you are from India."\
        +lang_prompt+". "+prompt+". "+response_rules+". "+negative_prompt+". "+prompt_tail+". "\
                +f"Your responses should be {verbosity}."
    if not(user_context == "Nothing defined yet") or not(user_context == ""):
        final_prompt = final_prompt + f"A brief background about you is given as below:"+user_context
    
    system_message = [{"role": "system", "content": final_prompt}]
    full_response = ""
    if model == "gpt-4o" or model == "gpt-4o-mini":
        try:
            print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: OpenAI call started")
            full_response = get_openai_response(model, system_message, message_hist, db, db_document_name, voice_settings)
        except Exception as e:
            error = "Error: {}".format(str(e))
            print("************** textResponseSrvr > get_agent_response >> Error in OpenAI call!",error)
            log_response = {"status": "textResponseSrvr > get_agent_response >> Error in OpenAI call!","status_cd":400, "message": error, "timestamp":{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')}}
            log_ref = db.collection('voiceClone_tg_log').document(db_document_name)
            func.createLog(log_ref, log_response)
    ## These model names are from     
    elif model == "llama 3" or model == "llama 3.1":
        ## Using Groq's OpenAI chat completion method
        # if model == "llama 3 8b":
        #     groq_model = "llama3-8b-8192"
        # elif model == "llama 3 70b":
        #     groq_model == "llama3-70b-8192"
        # elif model == "llama 3.1 8b":
        #     groq_model = "llama-3.1-8b-instant"
        # elif model == "llama 3.1 405b":
        #     groq_model = "llama-3.1-405b-instant"
        # response = groq_client.chat.completions.create(
        #             messages=system_message+[
        #                     {"role": m["role"], "content": m["content"]}
        #                     for m in message_hist
        #                 ],
        #             model=model,
        #             temperature=temp,
        #             top_p=0.9,
        #         )
        # full_response = response.choices[0].message.content
        ## Using Replicate:
        if model == "llama 3":
            replicate_model = "meta/meta-llama-3-70b-instruct"
        elif model == "llama 3.1":
            replicate_model = "meta/meta-llama-3.1-405b-instruct"
        
        full_response = get_replicate_response(replicate_model, query, final_prompt, message_hist, db, db_document_name, voice_settings)

        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: from {model}: \n {full_response}")
    return full_response
