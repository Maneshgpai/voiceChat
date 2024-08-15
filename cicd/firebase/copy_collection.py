import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from pytz import timezone


# Initialize the Dev environment
cred_dev = credentials.Certificate("./cred_cert/dev_serviceAccountKey.json")
firebase_admin.initialize_app(cred_dev, name='dev')
db_dev = firestore.client(app=firebase_admin.get_app('dev'))

# Initialize the Prod environment
cred_prod = credentials.Certificate("./cred_cert/prod_serviceAccountKey.json")
firebase_admin.initialize_app(cred_prod, name='prod')
db_prod = firestore.client(app=firebase_admin.get_app('prod'))

def copyCollectionWithDocuments(collection_name):
    docs = db_dev.collection(collection_name).stream()
    for doc in docs:
        db_prod.collection(collection_name).document(doc.id).set(doc.to_dict())
    print(collection_name," copied from Dev successfully.")

def createCollection(collection_name):
    db_prod.collection(collection_name).document().set({})
    print(collection_name," created successfully.")

# copyCollectionWithDocuments("voiceClone_characters")
# copyCollectionWithDocuments("voiceClone_voices")
# createCollection("voiceClone_tg_users")
# createCollection("voiceClone_tg_reachout")
# createCollection("voiceClone_tg_logs")
# createCollection("voiceClone_tg_chats")