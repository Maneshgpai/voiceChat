from elevenlabs.client import ElevenLabs
from elevenlabs import stream, play,  Voice, VoiceSettings, save
from datetime import datetime

client = ElevenLabs(api_key="sk_dc3a7c1e9fe70a079dad72dab79ecfe26d682f319df0154a")

# print(client.voices.get_all())

def generateVoice(input_text,voice_id):
    ## Code to create from an existing voice id
    audio = client.generate(
        text=input_text,
        voice=Voice(
            voice_id=voice_id,
            settings=client.voices.get_settings(voice_id)
            # settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
        ),
        model="eleven_multilingual_v2"
    )
    # save(audio, "Riddhi_clone.mp3")
    play(audio)

def generateVoiceStream(input_text,voice_id):
    print(input_text)
    audio_stream = client.generate(text=input_text,
        voice=Voice(
            voice_id=voice_id,
            settings=client.voices.get_settings(voice_id)),
        model="eleven_multilingual_v2"
        , stream=True)  
    stream(audio_stream)
    # return audio
