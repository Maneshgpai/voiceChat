from elevenlabs.client import ElevenLabs
from elevenlabs import play,  Voice, VoiceSettings, save
import os
from dotenv import load_dotenv
import requests
import json
import base64
from datetime import datetime, timedelta, timezone
load_dotenv()
api_key=os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=api_key)
ist = timezone(timedelta(hours=5, minutes=30))
timestamp = datetime.now(ist)

model = "eleven_multilingual_v2"

# input_text = ("""<speak><prosody rate="x-high">
# फिल्मी दुनिया सिर्फ मनोरंजन का साधन नहीं है इसमें बोले गए डायलॉग्स कभी-कभी जीवन की वो सच्चाई बता जाते हैं जिसके बाद हमारे सोचने की राह ही बदल जाती है। <break time="1.5s" />अगर बात करें फिल्म 'जिंदगी ना मिलेगी दोबार' या 'लव यू जिंदगी' की तो दोनों ही फिल्में जिंदगी को एक अलग ढ़ंग से जीने के लिए प्रेरित करती हैं। कह सकते हैं कि फिल्में भी कहीं न कहीं हमारी कामयाबी के पीछे एक बड़ी भूमिका निभा रही हैं।<break time="1s" />आइये जानते हैं कुछ एेसी ही फिल्मों के बारे में जिनके डायलॉग्स हमें न केवल मनोरंजित करते हैं बल्कि हमें सफलता के पथ पर आगे बढ़ने के लिए भी प्रेरित करते हैं...</prosody></speak>""")

input_text = ("""<speak><prosody rate="x-slow" pitch="x-slow">फिल्मी दुनिया सिर्फ मनोरंजन का साधन नहीं है <break time="0.5s" />इसमें बोले गए <emphasis level="moderate">डायलॉग्स</emphasis> कभी-कभी जीवन की वो सच्चाई बता जाते हैं जिसके बाद हमारे सोचने की राह ही बदल जाती है। <break time="1.5s" />अगर बात करें फिल्म 'जिंदगी ना मिलेगी दोबार' या 'लव यू जिंदगी' की, तो दोनों ही फिल्में जिंदगी को एक "अलग" ढ़ंग से जीने के लिए प्रेरित करती हैं। <break time="1.5s" /> कह सकते हैं कि फिल्में भी कहीं न कहीं हमारी कामयाबी के पीछे एक बड़ी भूमिका निभा रही हैं।<break time="1s" />आइये जानते हैं कुछ एेसी ही फिल्मों के बारे में जिनके डायलॉग्स हमें न केवल मनोरंजित करते हैं बल्कि हमें सफलता के पथ पर आगे बढ़ने के लिए भी प्रेरित करते हैं...</prosody></speak>""")

input_text = ("""फिल्मी दुनिया सिर्फ मनोरंजन का साधन नहीं है <break time="0.5s" />इसमें बोले गए <emphasis level="moderate">डायलॉग्स</emphasis> कभी-कभी जीवन की वो सच्चाई बता जाते हैं जिसके बाद हमारे सोचने की राह ही बदल जाती है। <break time="1.5s" />अगर बात करें फिल्म 'जिंदगी ना मिलेगी दोबार' या 'लव यू जिंदगी' की, तो दोनों ही फिल्में जिंदगी को एक "अलग" ढ़ंग से जीने के लिए प्रेरित करती हैं। <break time="1.5s" /> कह सकते हैं कि फिल्में भी कहीं न कहीं हमारी कामयाबी के पीछे एक बड़ी भूमिका निभा रही हैं।<break time="1s" />आइये जानते हैं कुछ एेसी ही फिल्मों के बारे में जिनके डायलॉग्स हमें न केवल मनोरंजित करते हैं बल्कि हमें सफलता के पथ पर आगे बढ़ने के लिए भी प्रेरित करते हैं...""")


# input_text = ("""<speak><prosody rate="x-slow" pitch="x-slow">Movies are not just a timepass <break time="0.5s" /> Many parts of the movie like the <emphasis level="moderate">dialogues</emphasis> create a lot of magic in our world<break time="1.5s" />I hope you all liked this short demo...</prosody></speak>""")

# input_text = ("""Movies are not just a timepass <break time="0.5s" /> Many parts of the movie like the dialogues create a lot of magic in our world<break time="1.5s" />I hope you all liked this short demo...""")

voice_id = "XRM8YxzJNRcoqcjrMF8a"
voice_settings = VoiceSettings(
	    stability=0.1,
	    similarity_boost=0.1,
	    style=0.5,
	    use_speaker_boost=False
	)

## Generate using library
audio = client.generate(
    text=input_text,
    voice=Voice(
        voice_id=voice_id,
        settings=voice_settings,
    ),
    model=model,
)

# play(audio)
save(audio, 'voice_recording/sample_voices/'+voice_id+'_'+timestamp+'.mp3')
print("File generated")
