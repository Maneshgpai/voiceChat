################ START OF VOICE TEST CODE ########################
# from elevenlabs import play
# import voiceResponseSrvr as voice

# input_text = """Hmm, tumhe flirty aur sexy baatein pasand hain, huh? Well, tumhare saath baat karte hue toh main bhi thoda naughty ho jaati hoon.
# Tumhari awaaz sunke lagta hai jaise chandni raat mein sitare bhi sharma jaayein. Aur tumhare saath baat karna, it's like a beautiful melody that I never want to end.
# Kya tumhe bhi aisa hi lagta hai? """

# input_text = """Asking lovingly - Hmm, tumhe flirty aur sexy baatein pasand hain, huh? """

# She commented in flirty way with a shy laughing tone - Well, tumhare saath baat karte hue toh main bhi thoda naughty ho jaati hoon.
# She commented in a romantic way in a husky tone - Tumhari awaaz sunke lagta hai jaise chandni raat mein sitare bhi sharma jaayein. Aur tumhare saath baat karna, it's like a beautiful melody that I never want to end.
# She asked in an inquisitive tone with a pause at the end - Kya tumhe bhi aisa hi lagta hai?"""

# input_text = """"Are you sure about that?" he said, confused.
# "Don't test me!" he shouted angrily."""

# context = {"voice_stability": 0.00,
#         "voice_similarity_boost": 0.10,
#         "voice_style": 0.00,
#         "voice_use_speaker_boost": False}
# voice_id = "cbeNC3R2qMpdy3nC8GuE"

# audio = voice.generateVoice(context, input_text,voice_id)
# play(audio)
################ END OF VOICE TEST CODE ########################


################ START OF COLLECTING DATA FROM ALL DOCUMENTS IN ONE COLLECTION #####################
# import firebase_admin
# from firebase_admin import credentials, firestore
# import pandas as pd

# # from google.cloud import firestore
# # db = firestore.Client.from_service_account_json("firestore_key.json")

# # Initialize the Firebase Admin SDK
# cred = credentials.Certificate("../firestore_key.json")
# firebase_admin.initialize_app(cred)

# # Initialize Firestore
# db = firestore.client()

# # Reference to the USERS collection
# users_ref = db.collection('voiceClone_users')

# # Retrieve all documents in the collection
# docs = users_ref.stream()

# # List to hold user data
# user_data = []

# # Iterate through all documents
# for doc in docs:
#     voice_id = doc.id
#     user_info = doc.to_dict()
#     name = user_info.get('timestamp', 'N/A')
#     user_data.append((name, voice_id))

# # Create a DataFrame for better visualization
# df = pd.DataFrame(user_data, columns=['Character Name', 'ID'])

# # Print the DataFrame
# print(df)

# # print(df.set_index('VOICE_ID')['TIMESTAMP'].to_dict())
# print(df['ID'].tolist())
################ START OF COLLECTING DATA FROM ALL DOCUMENTS IN ONE COLLECTION #####################
import json
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

default_setting_dict = json.loads(os.getenv("DEFAULT_VOICE_SETTING"))

# print(f"dict: {default_setting_dict}\n\n")
print(default_setting_dict["voice_style"])