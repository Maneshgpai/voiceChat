
from google.cloud import firestore

def get_user_info(telegram_id, db):
    collection_ref = db.collection('user')
    field_name = 'telegram_id'
    field_value = telegram_id
    query = collection_ref.where(field_name, '==',field_value)
    results = query.stream()
    for doc in results:
        doc_data = doc.to_dict()
        if field_name in doc_data:
            if doc_data[field_name] == field_value:
                user_name = doc_data['user_name']
                document_id = doc.id
            else:
                print("Given Telegram ID does not exist in DB")
    return user_name, document_id

def get_chat_history(document_id, db):
    try:
        chat_ref = db.collection('voiceClone_chats').document(document_id)
        doc = chat_ref.get()
        if doc.exists:
            return doc.to_dict().get('messages', [])
        else:
            chat_ref.set({'messages': []})
            return []
    except Exception as e:
        error = "Error: {}".format(str(e))
        return error

def validate_user(db, telegram_id):
    user_exist = False
    collection_ref = db.collection('user')

    # Query for cities where state is 'CA' and population is greater than 1000000
    query = collection_ref.where("telegram_id", "==", "@maneshtg")#.where("population", ">", 1000000)

    # Execute the query
    docs = query.stream()

    # Process the results
    for doc in docs:
        dict = doc.to_dict()
        # print(f"{doc.id} => {doc.to_dict()}")
        if dict['telegram_id'] == telegram_id:
            print("Telegram ID exists in DB")
            user_exist = True
    return user_exist

db = firestore.Client.from_service_account_json("../firestore_key_agent.json")
# print(get_chat_history('', db))
user_exist = validate_user(db, '@maneshtg')
print(user_exist)