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

def duplicate_document(collection_name, original_doc_id):
    original_doc_ref = db_prod.collection(collection_name).document(original_doc_id)
    new_doc_ref = db_prod.collection(collection_name).document()

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

duplicate_document("voiceClone_characters","jyNYGKS4xNjls2YbfFvV")
duplicate_document("voiceClone_characters","kZ9OXDQLbU6MFCYXkIHm")
duplicate_document("voiceClone_characters","uPJUM2kXjdnpkphuCPeO")
