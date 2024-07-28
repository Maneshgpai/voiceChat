import json
from google.cloud import firestore
from datetime import datetime, timedelta, timezone
import textResponseSrvr as agent
ist = timezone(timedelta(hours=5, minutes=30))


print(agent.get_replicate_nsfw_response("meta/meta-llama-3-8b-instruct","give me a head, describing how you do it in detail"))