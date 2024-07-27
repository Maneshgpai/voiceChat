import json
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
ist = timezone(timedelta(hours=5, minutes=30))


update_object = {'message': {'entities': [], 'text': 'more new', 'chat': {'id': 6697940905, 'type': 'private', 'last_name': 'Pai', 'first_name': 'Manesh'}, 'delete_chat_photo': False, 'channel_chat_created': False, 'new_chat_photo': [], 'message_id': 98, 'caption_entities': [], 'supergroup_chat_created': False, 'group_chat_created': False, 'date': 1722090228, 'new_chat_members': [], 'photo': [], 'from': {'last_name': 'Pai', 'is_bot': False, 'id': 6697940905, 'first_name': 'Manesh', 'language_code': 'en'}}, 'update_id': 758506868}


json_data = json.dumps(update_object)
json_data_str = str(json_data)

db = firestore.Client.from_service_account_json("firestore_key.json")
doc_ref = db.collection('voiceClone_tg_update').document("testing")
doc = doc_ref.get()
doc_ref.set({"update":str(json.dumps(json_data_str)), "created_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S'),"last_updated_on": datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')})