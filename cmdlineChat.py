from openai import OpenAI
import os
from datetime import datetime
import voiceResponse as voiceresponse
from elevenlabs.client import ElevenLabs
from elevenlabs import play

os.environ["OPENAI_API_KEY"] = "sk-proj-LiZSI1OKw7YHB4WJEQ1BT3BlbkFJHlzqnlKXW0UkkSCLcd0U"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),)

def chat_with_openai(prompt, history):

    history.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=history
        )

    llm_response = response.choices[0].message.content
    
    # Append the LLM response to the chat history
    history.append({"role": "assistant", "content": llm_response})

    return llm_response#, history

def chat_with_openai_2(prompt, history):

    history.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=history
        )

    llm_response = response.choices[0].message.content
    
    # Append the LLM response to the chat history
    history.append({"role": "assistant", "content": llm_response})

    return llm_response, history

def main():
    chat_history = [{"role": "system", "content": "You are a celebrity influencer. YOu are to speak only in Hindi. You have to keep chats to a minimal, without explaining too much. If you have doubts, you are allowed to ask. You are expected to answer only when asked. Otherwise, you can behave like a human and reply accordingly. You take offence at wiered questions or inappropriate comments/statements/questions. You will not ask a question after your response, unless that question is to help answer some user statement. Add a question only if you need to clarify any response."}]

    print("Welcome to the Meri Awaaz - Talk to your idol! Type 'exit' to quit.")
    while True:
        # Take user input
        user_input = input("You: ")

        # Exit the chat loop if the user types 'exit'
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        # Get the LLM response and updated chat history
        response, chat_history = chat_with_openai_2(user_input, chat_history)

        # voice_id = 'NZMDP4cQP5D9xHhE3olG' #riddhi's voice
        voice_id = 'cbeNC3R2qMpdy3nC8GuE' #Riddhi_2's voice
        # print(f"{datetime.now()} Generating Voice")
        voice_response = voiceresponse.generateVoiceStream(response,voice_id)
        # print(f"{datetime.now()} Playing Voice")
        play(voice_response)

if __name__ == "__main__":
    main()