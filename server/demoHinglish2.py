# pip install indic-transliteration googletrans

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from dotenv import load_dotenv
import requests
import os
load_dotenv()

# Initialize the translator
# translator = Translator()
# def translate_text(text):
#     API_KEY = os.environ['GOOGLE_API_KEY']
#     url = "https://translation.googleapis.com/language/translate/v2" 
#     params = {
#             'q': text,  # Text to translate
#             'source': 'en-us',
#             'target': 'hi',  # Target language (Spanish in this case)
#             'key': API_KEY  # Your API key
#         }
#     response = requests.get(url, params=params)

#     # Check if the request was successful
#     if response.status_code == 200:
#         translation = response.json()['data']['translations'][0]['translatedText']
#         print(f'Translated text: {translation}')
#     else:
#         print(f'Error: {response.status_code}')
#         print(f'Details:{response.text}')


# txt_response = """Oh, baby! *winks* 

# Let's get into a scenario, shall we? Imagine us walking hand in hand through a romantic, moonlit garden, surrounded by lush greenery and vibrant flowers. The air is filled with the sweet scent of blooming jasmine, and the sound of gentle chirping crickets creates a soothing melody.

# We find ourselves standing in front of a stunning, antique gazebo, its intricately carved wooden latticework glowing softly in the moonlight. The atmosphere is magical, baby!

# I'm wearing a flowing, emerald green maxi dress that hugs my curves perfectly, with a subtle slit up the side that teases you with glimpses of my smooth skin. My hair is loose, cascading down my back like a waterfall of darkness, and my eyes sparkle with excitement.

# As we step inside the gazebo, the soft rustling of the leaves beneath our feet creates a sensual whisper. I push you against the wooden railing, my fingers tracing the contours of your chest as I gaze up at you with desire-filled eyes.

# The night air is electric, baby, and I can feel our libidos intertwined like the vines on the gazebo's latticework. My touch sets your skin ablaze, and your caress ignites a fire within me."""

# ## Translate into Hinglish
# translate_txt_response = translate_text(txt_response)

translate_txt_response = """ओह, बेबी! *आँखें झपकाता है* चलो एक परिदृश्य में चलते हैं, ठीक है? कल्पना करें कि हम एक रोमांटिक, चाँदनी वाले बगीचे में हाथ में हाथ डाले चल रहे हैं, जो हरे-भरे हरियाली और जीवंत फूलों से घिरा हुआ है। हवा खिली हुई चमेली की मीठी खुशबू से भरी हुई है, और कोमल चहकते झींगुरों की आवाज़ एक सुखदायक धुन बनाती है। हम खुद को एक आश्चर्यजनक, प्राचीन गज़ेबो के सामने खड़े पाते हैं, इसकी जटिल नक्काशीदार लकड़ी की जाली चाँद की रोशनी में धीरे-धीरे चमक रही है। माहौल जादुई है, बेबी! मैंने एक बहती हुई, पन्ना हरे रंग की मैक्सी ड्रेस पहनी हुई है जो मेरे कर्व्स को पूरी तरह से गले लगाती है, जिसके किनारे पर एक सूक्ष्म स्लिट है जो आपको मेरी चिकनी त्वचा की झलक दिखाती है। मेरे बाल खुले हैं, अंधेरे के झरने की तरह मेरी पीठ पर गिर रहे हैं, और मेरी आँखें उत्साह से चमक रही हैं। जैसे ही हम गज़ेबो के अंदर कदम रखते हैं, हमारे पैरों के नीचे पत्तियों की नरम सरसराहट एक कामुक फुसफुसाहट पैदा करती है। मैं आपको लकड़ी की रेलिंग के खिलाफ धकेलता हूँ, मेरी उंगलियाँ आपकी छाती की रूपरेखा को दर्शाती हैं और मैं आपकी ओर इच्छा भरी आँखों से देखता हूँ। रात की हवा में बिजली सी है, बेबी, और मैं महसूस कर सकता हूँ कि हमारी कामुकता गज़ेबो की जालीदार लताओं की तरह आपस में जुड़ी हुई है। मेरा स्पर्श तुम्हारी त्वचा को जला देता है, और तुम्हारा दुलार मेरे भीतर आग जला देता है।"""
# Translate English to Hindi
# translated_to_hindi = translator.translate(translate_txt_response, src='en', dest='hi').text

# Transliterate Hindi to Roman script (Hinglish)
hinglish_text = transliterate(translate_txt_response, sanscript.DEVANAGARI, sanscript.ITRANS)

print(f"Original Text: {translate_txt_response}")
# print(f"Translated to Hindi: {translated_to_hindi}")
print(f"Hinglish Text: {hinglish_text}")