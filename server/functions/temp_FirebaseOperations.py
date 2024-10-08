import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from pytz import timezone

# Initialize the Firebase Admin SDK
cred = credentials.Certificate("firestore_key_agent.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Function to move a document from one collection to another
def move_document(source_collection, target_collection, document_id):
    # Reference to the source document
    source_doc_ref = db.collection(source_collection).document(document_id)
    
    # Retrieve the source document
    source_doc = source_doc_ref.get()
    if not source_doc.exists:
        print(f"Document {document_id} does not exist in the source collection {source_collection}.")
        return
    
    # Get the document data
    doc_data = source_doc.to_dict()
    
    # Reference to the target document
    target_doc_ref = db.collection(target_collection).document(document_id)
    
    # Set the document data in the target collection
    target_doc_ref.set(doc_data)
    
    # Delete the document from the source collection
    # source_doc_ref.delete()
    
    print(f"Document {document_id} has been moved from {source_collection} to {target_collection}.")
## MOVE DOCUMENT ##
# source_collection = 'user'
# target_collection = 'profile'
# document_id = '1qEiC6qsybMkmnNdVMbK'
# move_document(source_collection, target_collection, document_id)

def duplicate_collection(source_collection_name,target_collection_name):
    source_collection_ref = db.collection(source_collection_name)
    target_collection_ref = db.collection(target_collection_name)

    # Retrieve all documents from the source collection
    docs = source_collection_ref.stream()

    # Copy each document to the target collection
    for doc in docs:
        doc_dict = doc.to_dict()
        target_doc_ref = target_collection_ref.document(doc.id)
        target_doc_ref.set(doc_dict)
# duplicate_collection('voiceClone_tg_logs','voiceClone_tg_log_bkp')

def duplicate_document(collection_name, original_doc_id):
    original_doc_ref = db.collection(collection_name).document(original_doc_id)
    # new_doc_ref = db.collection(collection_name).document(new_doc_id)
    new_doc_ref = db.collection(collection_name).document()

    try:
        doc_snapshot = original_doc_ref.get()
        
        if not doc_snapshot.exists:
            print(f'Original document {original_doc_id} does not exist!')
            return
        
        original_data = doc_snapshot.to_dict()
        new_doc_ref.set(original_data)
        print(f'Document duplicated successfully: {new_doc_ref.id}')
        
    except Exception as e:
        print(f'Error duplicating document: {e}')

def update_timestamps(collection_name):
    local_timezone = timezone("Asia/Kolkata")
    collection_ref = db.collection(collection_name)
    docs = collection_ref.stream()

    # Iterate through all documents
    for doc in docs:
        doc_id = doc.id
        doc_data = doc.to_dict()
        messages = doc_data.get('messages', [])

        # Check each message for the timestamp field
        for i, message in enumerate(messages):
            if isinstance(message, dict) and 'timestamp' in message:
                timestamp_value = message['timestamp']
                if isinstance(timestamp_value, str):
                    try:
                        # new_timestamp = datetime.datetime.strptime(timestamp_value, "%Y-%m-%d %H:%M:%S")
                        naive_datetime = datetime.datetime.strptime(timestamp_value, "%Y-%m-%d %H:%M:%S")
                        new_timestamp = local_timezone.localize(naive_datetime)
                        messages[i]['timestamp'] = new_timestamp
                    except ValueError as e:
                        print(f"Error converting timestamp for document {doc_id}: {e}")

        # Update the document with the new messages array
        doc_ref = collection_ref.document(doc_id)
        doc_ref.update({'messages': messages})
    print("Finished updating all documents!")
# update_timestamps('voiceClone_chats')
# duplicate_collection('chat','chat_bkp20240809')


def get_character_dtls():
    print("Downloading Character data...")
    collection_ref = db.collection('voiceClone_characters')
    docs = collection_ref.stream()
    charid_bottoken = []
    charid_prompt = []
    for doc in docs:
        doc_id = doc.id
        charid_bottoken_doc = {}
        charid_prompt_doc = {}
        settings = doc.to_dict().pop('setting', {})
        for key, value in settings.items():
            if key == "bot_token":
                charid_bottoken_doc[doc_id] = value
            if key == "reachout_prompt":
                charid_prompt_doc[doc_id] = value
        charid_bottoken.append(charid_bottoken_doc)
        charid_prompt.append(charid_prompt_doc)

    return charid_bottoken, charid_prompt

def get_collection_count():
    collection_ref = db.collection('voiceClone_tg_users')
    docs = collection_ref.stream()
    print("\n\n\nDownloading USERS from Firebase")


# charid_bottoken, charid_prompt = get_character_dtls()
# # charid_bottoken = json.loads(os.getenv("REACHOUT_CHARID_BOT_TOKEN")) #{"uPJUM2kXjdnpkphuCPeO":"6936690207:AAFibJC2nm1xgPk0JOC6Ag9BJ10KZHuVcMM"}
# # charid_prompt = json.loads(os.getenv("REACHOUT_CHARID_BOT_TOKEN"))#{"uPJUM2kXjdnpkphuCPeO":"Reachout prompt..."}
# print(f"charid_bottoken:{charid_bottoken}")
# print(f"charid_prompt:{charid_prompt}")


# for key, value in enumerate(charid_bottoken):
#     for k, v in value.items():
#         if k == '1EfPNzsBf9c6L3FE96m2':
#             bot_token = v

# for key, value in enumerate(charid_prompt):
#     for k, v in value.items():
#         if k == '1EfPNzsBf9c6L3FE96m2':
#             reachout_prompt = v

# print(bot_token, reachout_prompt)
# move_document('voiceClone_tg_chats', 'voiceClone_tg_chats_test_reachout', '6697940905_A8pNNpS9S5ytKTs7XsZY')

# move_document('chat', 'chat_test_reachout', '6733334932_A8pNNpS9S5ytKTs7XsZY')
# move_document('chat', 'chat_test_reachout', '6733334932_KojdgNzrBNJO8CyQgr5g')
# move_document('chat', 'chat_test_reachout', '6733334932_bPm741abegxqm3t7rfeB')
# move_document('chat', 'chat_test_reachout', '6733334932_jyNYGKS4xNjls2YbfFvV')
# move_document('chat', 'chat_test_reachout', '6733334932_kZ9OXDQLbU6MFCYXkIHm')
# move_document('chat', 'chat_test_reachout', '6733334932_uPJUM2kXjdnpkphuCPeO')
# move_document('chat', 'chat_test_reachout', '7142807432_bPm741abegxqm3t7rfeB')
# move_document('chat', 'chat_test_reachout', '7142807432_jyNYGKS4xNjls2YbfFvV')
# move_document('chat', 'chat_test_reachout', '7142807432_kZ9OXDQLbU6MFCYXkIHm')
# move_document('chat', 'chat_test_reachout', '7142807432_uPJUM2kXjdnpkphuCPeO')
