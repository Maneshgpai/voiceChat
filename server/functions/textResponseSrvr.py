from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
voice_api_key = os.getenv("ELEVENLABS_API_KEY")
client = OpenAI(api_key=openai_api_key)
ist = timezone(timedelta(hours=5, minutes=30))


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

def get_agent_response(voice_settings, message_hist):
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

    if model == "gpt-4o" or model == "gpt-3.5-turbo":

        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: OpenAI call started")
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: message_hist:\n{message_hist}")

        voice_settings = [{"role": "assistant", "content": final_prompt}]
        
        response = client.chat.completions.create(
            model=model,
            messages=voice_settings+[
                {"role": m["role"], "content": m["content"]}
                for m in message_hist
            ],
            stream=False,
            temperature=temp
        )
        
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: OpenAI response object \n {response.choices[0].message.content}")
    return response.choices[0].message.content
