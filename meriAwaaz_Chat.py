import streamlit as st # type: ignore
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
# import agent2_TavilySearch as agent
import myCoachAi_AgentChat as agent
import myCoachAi_AgentSupportFunc as agent_func

db = firestore.Client.from_service_account_json("firestore_key.json")

# Function to get user data by phone number
def get_user_data(phone_number):
    # Fetch user profile from DB
    user_ref = db.collection('users').document(phone_number)
    doc = user_ref.get()
    user_data = doc.to_dict()
    for k, v in user_data.items():
        if k == 'profile':
           user_profile = v 
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = user_profile

    # Fetch user's preferred language
    lang = agent_func.pick_language(user_profile)
    if "language" not in st.session_state:
        st.session_state["language"] = lang
    
    # Fetch user workout plan from DB
    workoutplan_ref = db.collection('workoutplan').document(phone_number)
    doc1 = workoutplan_ref.get()
    workoutplan_data = doc1.to_dict()
    for k, v in workoutplan_data.items():
        if k == 'plan':
           workoutplan = v 
    if "workoutplan" not in st.session_state:
        st.session_state["workoutplan"] = workoutplan

    if doc.exists:
        return user_data
    else:
        return None

# Function to create a new chat document if it doesn't exist
def create_chat(phone_number):
    chat_ref = db.collection('chats').document(phone_number)
    if not chat_ref.get().exists:
        chat_ref.set({'messages': [], 'session_timestamps': []})

# Function to send a message
def send_message(messages, message, sender="user"):
    ist = timezone(timedelta(hours=5, minutes=30))
    timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
    messages.append({"text": message, "sender": sender, "timestamp": timestamp})

# Function for bot response
def bot_response(phone_number, latest_user_message, language,hist_user_bot_conversation,workoutplan):
    print(f"Phone:{phone_number},Ques:{latest_user_message}, chat history:{hist_user_bot_conversation}, workoutplan:{workoutplan}")
    bot_response = agent.bot_response(phone_number, latest_user_message, language, hist_user_bot_conversation, workoutplan)
    send_message(hist_user_bot_conversation, bot_response, sender="bot")

# Function to get chat messages from Firebase
def get_chat_messages(phone_number):
    chat_ref = db.collection('chats').document(phone_number)
    doc = chat_ref.get()
    if doc.exists:
        return doc.to_dict().get('messages', [])
    else:
        return []

# Function to save chat history to Firebase
def save_chat_history(phone_number, messages):
    chat_ref = db.collection('chats').document(phone_number)
    ist = timezone(timedelta(hours=5, minutes=30))
    timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
    chat_ref.update({"messages": firestore.ArrayUnion(messages),
                     "session_timestamps": firestore.ArrayUnion([timestamp])})

# Main application
st.title("WhatsApp / Telegram Simulation")

# Custom CSS for chat bubbles
st.markdown("""
    <style>
    .user-bubble {
        background-color: #d1e7dd;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 80%;
        align-self: flex-end;
        position: relative;
    }
    .bot-bubble {
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 80%;
        align-self: flex-start;
        position: relative;
    }
    .timestamp {
        font-size: 0.7em;
        color: gray;
        position: absolute;
        bottom: 5px;
        right: 10px;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    </style>
    """, unsafe_allow_html=True)

# Step 1: Enter phone number to start chat session
phone_number = st.text_input("Enter your phone number")

if phone_number:
    user_data = get_user_data(phone_number)
    if user_data:
        # Ensure chat document exists
        create_chat(phone_number)
        
        # Load existing chat messages from Firebase
        if "messages" not in st.session_state:
            st.session_state["messages"] = get_chat_messages(phone_number)
           
        # If no previous messages, send welcome message and save it
        if not st.session_state["messages"]:
            ist = timezone(timedelta(hours=5, minutes=30))
            timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
            # welcome_message = f"Coach: Hey there! How can I help? 😊"
            # send_message(st.session_state["messages"], welcome_message, sender="bot")
            bot_response(phone_number, "initial_message", st.session_state["language"], st.session_state["messages"], st.session_state["workoutplan"])
            save_chat_history(phone_number, st.session_state["messages"])

        # Display chat messages
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state["messages"]:
            if message["sender"] == "user":
                st.markdown(
                    f'<div class="user-bubble">{user_data.get("Full Name")}: {message["text"]}'
                    f'<div class="timestamp">{message["timestamp"]}</div></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="bot-bubble">Coach: {message["text"]}'
                    f'<div class="timestamp">{message["timestamp"]}</div></div>',
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input
        message = st.text_input("Type a message", key="message")

        # Send button
        if st.button("Send"):
            if message:
                send_message(st.session_state["messages"], message, sender="user")
                bot_response(phone_number, message, st.session_state["language"], st.session_state["messages"], st.session_state["workoutplan"])
                st.rerun()
            else:
                st.error("Message cannot be empty.")
        
        # Save chat history button
        if st.button("Save Chat History"):
            save_chat_history(phone_number, st.session_state["messages"])
            st.success("Chat history saved successfully.")
            st.session_state["messages"] = []  # Clear session state after saving
    else:
        st.error("User not found. Please check the phone number and try again.")
