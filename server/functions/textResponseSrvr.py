from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from groq import Groq
import replicate


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
voice_api_key = os.getenv("ELEVENLABS_API_KEY")
client = OpenAI(api_key=openai_api_key)
ist = timezone(timedelta(hours=5, minutes=30))
groq_client = Groq()


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
def get_replicate_response(model, query, system_prompt, message_hist):
    # print(f"textResponseSrvr >> get_replicate_response > message_hist:\n{message_hist}\n")
    final_prompt = system_prompt.replace("\n","\\n")
    query = query.replace("\n","\\n")
    new_message_hist = ""
    for item in message_hist:
        if item.get('role') == 'user':
            u_msg = item.get('content', '')
            new_message_hist += "<|start_header_id|>user<|end_header_id|>"+u_msg.strip().replace("\n","\\n")+"<|eot_id|>"
        elif item.get('role') == 'assistant':
            a_msg = item.get('content', '')
            new_message_hist += "<|start_header_id|>assistant<|end_header_id|>"+a_msg.strip().replace("\n","\\n")+"<|eot_id|>"
    # print(f"textResponseSrvr >> get_replicate_response > new_message_hist for Llama3.1:\n{new_message_hist}\n")

    full_text = []
    for event in replicate.stream(
            model,
            input={
                "top_k": 0,
                "top_p": 0.9,
                "prompt": new_message_hist,
                "max_tokens": 2000,
                "min_tokens": 0,
                "temperature": 1.31,
                "system_prompt": final_prompt,
                "length_penalty": 1.35,
                "stop_sequences": "<|end_of_text|>,<|eot_id|>",
                # "prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>",
                "prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_prompt}<|eot_id|>{prompt}<|start_header_id|>assistant<|end_header_id|>",
                "presence_penalty": 1.15,
                "log_performance_metrics": False
            },
        ):
            full_text.append(str(event))
    return ''.join(full_text)
def get_agent_response(query, voice_settings, message_hist):
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
    if model == "gpt-4o" or model == "gpt-3.5-turbo":
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: OpenAI call started")
        response = client.chat.completions.create(
            model=model,
            messages=system_message+[
                {"role": m["role"], "content": m["content"]}
                for m in message_hist
            ],
            stream=False,
            temperature=temp
        )
        full_response = response.choices[0].message.content
        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: from {model}: \n {full_response}")

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
        
        full_response = get_replicate_response(replicate_model, query, final_prompt, message_hist)

        print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} textResponseSrvr > get_agent_response: from {model}: \n {full_response}")
    return full_response
