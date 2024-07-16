from elevenlabs.client import ElevenLabs
from elevenlabs import play,  Voice, VoiceSettings, save
from datetime import datetime, timedelta, timezone
from datetime import datetime
import subprocess
ist = timezone(timedelta(hours=5, minutes=30))
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def generateVoice(context, input_text,voice_id):
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Voice generation started")
    
    voice_settings = VoiceSettings(
        stability=context['voice_stability'],
        similarity_boost=context['voice_similarity_boost'],
        style=context['voice_style'],
        use_speaker_boost=context['voice_use_speaker_boost']
    )

    print("Default setting for the voice id:",client.voices.get_settings(voice_id))

    audio = client.generate(
        text=input_text,
        voice=Voice(
            voice_id=voice_id,
            settings=client.voices.get_settings(voice_id),
            # settings=voice_settings,
        ),
        model="eleven_multilingual_v2"
    )
    print(f"{datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')} Voice generation finished")
    return audio

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
