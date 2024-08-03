import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

XI_API_KEY = os.getenv("ELEVENLABS_API_KEY")
url = "https://api.elevenlabs.io/v1/voices"

headers = {
  "Accept": "application/json",
  "xi-api-key": XI_API_KEY
}

response = requests.get(url, headers=headers)
data = response.json()

for voice in data['voices']:
  print(f"{voice['name']}; {voice['voice_id']}")