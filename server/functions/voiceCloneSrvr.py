from elevenlabs.client import ElevenLabs
from elevenlabs import stream, play,  Voice, VoiceSettings, save
from datetime import datetime, timedelta, timezone
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


print(f"{datetime.now()} Started cloning voice...")
## Code to clone a voice from sample files
files = ["test_data/Riddhi_2_training.flac"]
voice = client.clone(name="Riddhi_2",description="Trained on voice message sent on Whatsapp, at 27-Jun-2024 2.35pm ",files=files)
print(f"Voice cloned for {voice.name}, with voice id {voice.voice_id}")
