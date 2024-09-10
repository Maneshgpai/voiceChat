from elevenlabs.client import ElevenLabs
from elevenlabs import play,  Voice, VoiceSettings, save
from datetime import datetime, timedelta, timezone
from datetime import datetime
from functions import functionSrvr as func
import subprocess
ist = timezone(timedelta(hours=5, minutes=30))
import os
from dotenv import load_dotenv
load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def generateVoice(context, input_text,voice_id):
    # print(f"{datetime.now(ist)} Voice generation started")    
    voice_settings = VoiceSettings(
        stability=context['voice_stability'],
        similarity_boost=context['voice_similarity_boost'],
        style=context['voice_style'],
        use_speaker_boost=context['voice_use_speaker_boost']
    )

    audio = client.generate(
        text=input_text,
        voice=Voice(
            voice_id=voice_id,
            # settings=client.voices.get_settings(voice_id),
            settings=voice_settings,
        ),
        model="eleven_multilingual_v2"
    )
    return audio
# def play_audio_stream(audio_stream):
#     # Start ffplay process
#     ffplay_process = subprocess.Popen(
#         ['ffplay', '-'],
#         stdin=subprocess.PIPE,
#         stdout=subprocess.DEVNULL,
#         stderr=subprocess.DEVNULL
#     )

#     # Write audio data to ffplay's stdin
#     for chunk in audio_stream:
#         ffplay_process.stdin.write(chunk)
    
#     # Close stdin to signal end of stream
#     ffplay_process.stdin.close()
    
#     # Wait for ffplay to finish
#     ffplay_process.wait()
# def generateVoiceStream(input_text,voice_id):
#     print(input_text)
#     audio_stream = client.generate(text=input_text,
#         voice=Voice(
#             voice_id=voice_id,
#             settings=client.voices.get_settings(voice_id)),
#         model="eleven_multilingual_v2"
#         , stream=True)
#     # stream(audio_stream)
#     # play_audio_stream(audio_stream)
#     return audio_stream
def get_voice_response(voice_setting, full_response,filename, db, db_document_name, msg_id):
    # print(f"{datetime.now(ist)} voiceResponseSrvr > get_voice_response: Started generating voice...")
    try:
        audio = generateVoice(voice_setting,full_response,voice_setting['voice_id'])
        # print(f"{datetime.now(ist)} voiceResponseSrvr > get_voice_response: Successfully generated voice.")
    except Exception as e:
        error = "Error: {}".format(str(e))
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":"get_voice_response.generateVoice", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)

    # print(f"{datetime.now(ist)} voiceResponseSrvr > get_voice_response: Saving audio file...")
    try:
        save(audio, filename)
        print(f"{datetime.now(ist)} voiceResponseSrvr > get_voice_response: Successfully saved audio file in ",filename)
    except Exception as e:
        error = "Error: {}".format(str(e))
        # print("*** ERROR *** TG_Bot/voiceResponseSrvr/get_voice_response > Error in saving Audio file",error)
        log_response = {str(msg_id)+"_"+str(datetime.now()): {"status": "error","status_cd":400,"message":error, "origin":"get_voice_response.save_audio", "message_id": msg_id, "timestamp":datetime.now(ist)}}
        log_ref = db.collection('log').document(db_document_name)
        func.createLog(log_ref, log_response)
        return False
    return True
