# import requests
import os
import requests
import json

# client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

url = "https://api.elevenlabs.io/v1/voices"
# url = "https://api.elevenlabs.io/v1/shared-voices"
headers = {
"Accept": "application/json",
"xi-api-key": os.getenv("ELEVENLABS_API_KEY")
}
response = requests.get(url, headers=headers)
data = response.json()
print(data)
# for voice in data['voices']:
#     print(f"{voice['name']}; {voice['voice_id']}")