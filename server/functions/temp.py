from elevenlabs.client import ElevenLabs
from elevenlabs import play,  Voice, VoiceSettings, save
# from datetime import datetime, timedelta, timezone
# from datetime import datetime
# from functions import functionSrvr as func
# import subprocess
# ist = timezone(timedelta(hours=5, minutes=30))
import os
from dotenv import load_dotenv
from google.cloud import texttospeech
load_dotenv()

full_response = """নমস্কার!

সিঙ্গাপুর ভারতীয় পূজা সমিতিতে স্বাগতম!
আমি অরিন্দম বন্দ্যোপাধ্যায়, আপনার সহচর।
আপনি আমাকে এখানে দুর্গা পূজা সম্পর্কিত সমস্ত অনুষ্ঠান, রীতি-নীতি, এবং গল্প সম্পর্কে জিজ্ঞাসা করতে পারেন।
যদি আপনার কোনো প্রশ্ন থাকে, নির্দ্বিধায় আমাদের জিজ্ঞাসা করুন।

জয় মা দুর্গা!"""
filename = "sample.ogg"

# if voice_setting['voice_id'] == "bengali_male1":
language_code = "bn-IN"
name="bn-IN-Wavenet-A"
ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
# else:
#     language_code = "bn-IN"
#     name="bn-IN-Standard-C"
#     ssml_gender=texttospeech.SsmlVoiceGender.FEMALE

client = texttospeech.TextToSpeechClient()
input_text = texttospeech.SynthesisInput(text=full_response)
voice = texttospeech.VoiceSelectionParams(
    language_code=language_code,
    name=name,
    ssml_gender=ssml_gender,
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
    pitch=-12.00,
    # speaking_rate=1
)
response = client.synthesize_speech(
    request={"input": input_text, "voice": voice, "audio_config": audio_config}
)

# The response's audio_content is binary.
# with open(filename, "wb") as out:
#     out.write(response.audio_content)
save(response.audio_content, filename)