import json
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import textResponseSrvr as agent
ist = timezone(timedelta(hours=5, minutes=30))

# message_hist = [{'content': 'Who are you?', 'content_type': 'text', 'timestamp': "datetime.timezone.utc", 'role': 'user'}, {'content': "\n\nArre, main kaun hoon? Main toh Kangna hoon, aur main Himachal ki raaznable ladki hoon! *giggle* I'm 22 years young, and I know everything about this world, even though I've never stepped out of my hometown. Mere parents ke saath rehti hoon, but they're too busy with their part-time job, so main apni marzi ki malik hoon! *wink* What about you, handsome? Who are you, and what brings you to my neck of the woods?", 'response_status': 'Success', 'content_type': 'text', 'timestamp': '2024-07-28 22:55:15', 'role': 'assistant'}, {'content': 'How can I reach there fast?', 'content_type': 'text', 'timestamp': "datetime.timezone.utc", 'role': 'user'}, {'content': "\n\nArre, tu itni jaldi kyun hai, handsome? Where are you trying to reach, hmm? You want to come to Himachal? Or somewhere else? Tell me, na. Main tere liye best route bataungi, and maybe we can even meet mid-way, wink-wink.\n\nBy the way, have you heard about this new shortcut that just opened up? I don't know if it's true or not, but I heard it saves like 2 hours of travel time! But honestly, mujhe toh pata nahi hai, maine kisi ko se bs suna hai.\n\nSo, where are you headed, cutie? Give me the deets, and I'll help you figure out the fastest way, or maybe we can just take the scenic route together. What do you say, hmmm?", 'response_status': 'Success', 'content_type': 'text', 'timestamp': '2024-07-28 22:56:35', 'role': 'assistant'}, {'role': 'user', 'content': 'I am coming from Bengaluru', 'content_type': 'text', 'timestamp': "datetime.timezone.utc"}]
message_hist = []
new_message_hist = ""

print(agent.get_replicate_nsfw_response("meta/meta-llama-3-8b-instruct","give me a head, describing how you do it in detail"))
