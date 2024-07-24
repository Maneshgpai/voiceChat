import firebase_admin
from firebase_admin import credentials, firestore

# Initialize the Firebase Admin SDK
cred = credentials.Certificate("firestore_key.json")
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

## MOVE DOCUMENT ##
# source_collection = 'voiceClone_users'
# target_collection = 'voiceClone_characters'
# document_id = '1qEiC6qsybMkmnNdVMbK'
# move_document(source_collection, target_collection, document_id)

## DUPLICATE DOCUMENT ##
collection_name = 'voiceClone_voices'
original_doc_id = '0Ue9uqhhblwZNr8OFpCU'
duplicate_document(collection_name, original_doc_id)


