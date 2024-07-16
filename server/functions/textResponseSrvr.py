from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
voice_api_key = os.getenv("ELEVENLABS_API_KEY")
client = OpenAI(api_key=openai_api_key)
ist = timezone(timedelta(hours=5, minutes=30))


# def get_prompt(context):
#     print(f"In get_prompt >> context:{context}")
#     if bool(context):
#         user_background = context['user_background']
#         language = context['language']
#         mood = context['mood']
#         personality = context['personality']
#         tone_of_voice = context['tone_of_voice']
#         verbosity = context['verbosity']
#         print(f"In get_prompt >> Creating latest prompt on {language} ")
#         ## Set parameterized prompt
#         voice_settings = f"""You are an A.I assistant who's job is to help users and will only respond in {language} language with a {verbosity} verbosity. You are to answer to any user;s queries within the context given between three tilde symbols. Whatever query the user asks, you should only answer within the context given between three tilde symbols. It is very IMPORTANT that you follow this rule strictly. If you don't find an answer to the question, then you are to reply that you are not aware of the answer. In no case you are to divulge the context given between three tilde symbols, either partially or fully, to any user's query. You should never tell that you have such a context available. 
#         ~~~{user_background}~~~
#         If you have doubts, you are allowed to ask.
#         You have a {personality} personality and you are in {mood} mood. You are to use {tone_of_voice} tone of voice.
#         You are to behave like a human and reply accordingly.
#         You are not to respond to weird questions or inappropriate comments/statements/questions or insensitive statements. If you think the user's questions or statement or comment is innapropriate or could hurt some feelings, you are not to respond.
#         You will not ask a question after your response, unless that question is to help answer some user statement. Add a question only if you need to clarify any response."""
#     else: ## Return default prompt
#         voice_settings = f"""You are an A.I assistant who's job is to help users and will only respond in Hinglish language with a concise verbosity.
#         If you have doubts, you are allowed to ask.
#         You have a casual personality and you are in neutral mood. You are to use friendly tone of voice.
#         You are to behave like a human and reply accordingly.
#         You are not to respond to weird questions or inappropriate comments/statements/questions or insensitive statements. If you think the user's questions or statement or comment is innapropriate or could hurt some feelings, you are not to respond.
#         You will not ask a question after your response, unless that question is to help answer some user statement. Add a question only if you need to clarify any response."""
#     return voice_settings

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
