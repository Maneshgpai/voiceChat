from openai import OpenAI
import streamlit as st
import voiceResponse as voiceresponse
import requests
from elevenlabs import play
from dotenv import load_dotenv
import os

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
voice_api_key = os.getenv("ELEVENLABS_API_KEY")
client = OpenAI(api_key=openai_api_key)

def validate_voice_id(voice_id):
    url = f"https://api.elevenlabs.io/v1/voices/{voice_id}"
    headers = {
        "Accept": "application/json",
        "xi-api-key": voice_api_key
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        voice_data = response.json()
        voice_name = voice_data.get("name")
        if "voice_name" not in st.session_state:
            st.session_state["voice_name"] = voice_name
        return True
    else:
        return False

# Function to get and display voice_id input
def get_voice_id():
    # st.subheader("Enter Voice ID")
    voice_id = st.text_input("Enter Voice ID:")
    submit = st.button("Submit")
    if submit:
        if voice_id:
            if validate_voice_id(voice_id):
                st.session_state.voice_id = voice_id
                st.rerun()  # Rerun the script to load the chat interface
            else:
                st.error("Invalid Voice ID. Please try again.")

def voice_response(text,voice_id):
    voice_response = voiceresponse.generateVoiceStream(text,voice_id)
    play(voice_response)

def get_parameters():
    st.sidebar.header("Voice Settings")

    # Language selection
    language = st.sidebar.selectbox("Language", ["Hindi", "English", "Tamil"], index=0)

    # Mood selection
    mood = st.sidebar.selectbox("Mood", ["Neutral", "Happy", "Sad", "Angry"], index=0)

    # Tone of voice selection
    tone_of_voice = st.sidebar.selectbox("Tone of Voice", ["Friendly", "Formal", "Informal", "Serious"], index=0)

    # Additional parameters
    personality = st.sidebar.selectbox("Personality", ["Casual", "Professional", "Witty", "Empathetic"], index=0)
    verbosity = st.sidebar.selectbox("Verbosity Level", ["Concise", "Detailed"], index=0)

    # Text area for additional input
    additional_input = st.sidebar.text_area("Any additional characteristics", "")

    # Collect all parameters into a dictionary
    parameters = {
        "language": language,
        "mood": mood,
        "tone_of_voice": tone_of_voice,
        "personality": personality,
        "verbosity": verbosity,
        "additional_input": additional_input
    }
    return parameters

# Function to display the chat interface
def chat_interface():
    st.title("Chat with "+st.session_state["voice_name"])

    # Get parameters from sidebar
    parameters = get_parameters()

    # Setting voice characteristics
    voice_setting = f"You are a celebrity influencer with an {parameters.get('personality')} personality. You are to speak only in {parameters.get('language')}. You have to keep verbosity of chats {parameters.get('verbosity')}. You are to speak in {parameters.get('mood')} mood with a {parameters.get('tone_of_voice')} of voice. If you have doubts, you are allowed to ask. You are expected to answer only when asked. Otherwise, you can behave like a human and reply accordingly. You are not to respond to weird questions or inappropriate comments/statements/questions or insensitive statements. If you think the user's questions or statement or comment is innapropriate or could hurt some feelings, you are not to respond. You will not ask a question after your response, unless that question is to help answer some user statement. Add a question only if you need to clarify any response."

    # Display the voice_id as un-editable
    st.text_input("Voice ID:", value=st.session_state.voice_id, disabled=True)

    # Initialize OpenAI model and messages if not already done
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input for new message
    if prompt := st.chat_input(""):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message(st.session_state["voice_name"]):
            system_message = [{"role": "assistant", "content": voice_setting}]

            response = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=system_message+[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True, ## For streaming text
                temperature=0
            )
            
            response = st.write_stream(response) ## For printing streaming text
            # full_response = response.choices[0].message.content ## For printing full output
            # st.write(full_response) ## For printing full output

            full_response = ""
            # Iterate over the streamed responses
            for chunk in response:
                if 'choices' in chunk:
                    for choice in chunk['choices']:
                        if 'delta' in choice and 'content' in choice['delta']:
                            # Append the content to the full response text
                            full_response += choice['delta']['content']
                            
            voiceresponse.generateVoiceStream(full_response,st.session_state.voice_id)
            
        st.session_state.messages.append({"role": "assistant", "content": response})

# Main function to control the flow
def main():
    if "voice_id" not in st.session_state:
        get_voice_id()
    else:
        chat_interface()

if __name__ == "__main__":
    main()
