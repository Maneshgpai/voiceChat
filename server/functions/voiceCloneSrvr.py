from elevenlabs.client import ElevenLabs
from elevenlabs import stream, play,  Voice, VoiceSettings, save
from datetime import datetime, timedelta, timezone
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

print(f"{datetime.now()} Started cloning voice...")
## Code to clone a voice from sample files
files = ["karabi.flac"]
voice = client.clone(name="R1",description="Trained on internet voice",files=files)
print(f"Voice cloned for {voice.name}, with voice id {voice.voice_id}")
