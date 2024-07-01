from elevenlabs.client import ElevenLabs
from elevenlabs import play,  Voice, VoiceSettings, save
from datetime import datetime
import subprocess
import random

client = ElevenLabs(api_key="sk_dc3a7c1e9fe70a079dad72dab79ecfe26d682f319df0154a")

# print(client.voices.get_all())

def generateVoice(input_text,voice_id):
    
    # print("Inside generateVoice >> input_text:",input_text)
    audio = client.generate(
        text=input_text,
        voice=Voice(
            voice_id=voice_id,
            settings=client.voices.get_settings(voice_id)
            # settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
        ),
        model="eleven_multilingual_v2"
    )
    filename = voice_id+str(random.random()).replace(".","")+".mp3"
    save(audio, filename)
    # print("saved audio file")
    return filename

def play_audio_stream(audio_stream):
    # Start ffplay process
    ffplay_process = subprocess.Popen(
        ['ffplay', '-'],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Write audio data to ffplay's stdin
    for chunk in audio_stream:
        ffplay_process.stdin.write(chunk)
    
    # Close stdin to signal end of stream
    ffplay_process.stdin.close()
    
    # Wait for ffplay to finish
    ffplay_process.wait()

def generateVoiceStream(input_text,voice_id):
    print(input_text)
    audio_stream = client.generate(text=input_text,
        voice=Voice(
            voice_id=voice_id,
            settings=client.voices.get_settings(voice_id)),
        model="eleven_multilingual_v2"
        , stream=True)
    # stream(audio_stream)
    # play_audio_stream(audio_stream)
    return audio_stream
