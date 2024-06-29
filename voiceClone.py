from elevenlabs.client import ElevenLabs
from elevenlabs import stream, play,  Voice, VoiceSettings, save
from datetime import datetime, timedelta, timezone

client = ElevenLabs(api_key="sk_dc3a7c1e9fe70a079dad72dab79ecfe26d682f319df0154a")

print(f"{datetime.now()} Started cloning voice...")
## Code to clone a voice from sample files
files = ["test_data/Riddhi_2_training.flac"]
voice = client.clone(name="Riddhi_2",description="Trained on voice message sent on Whatsapp, at 27-Jun-2024 2.35pm ",files=files)
print(f"Voice cloned for {voice.name}, with voice id {voice.voice_id}")
