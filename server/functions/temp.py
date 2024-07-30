from dotenv import load_dotenv
import os
# from google.cloud import translate
import requests
# from google.oauth2 import service_account
# import google.auth

load_dotenv()
# GOOGLE_APPLICATION_CREDENTIALS="firestore_key.json"
API_KEY = os.environ['GOOGLE_API_KEY']
# credentials = service_account.Credentials.from_service_account_file("firestore_key.json")
# translate_client = translate.Client()

text = "I was amazed by her beauty"
target_lang_cd = "hi"

# translation = translate_client.translate(text, target_language=target_lang_cd)
# translated_text = format(translation["translatedText"])
url = "https://translation.googleapis.com/language/translate/v2" 
params = {
        'q': text,  # Text to translate
        'source': 'en-us',
        'target': target_lang_cd,  # Target language
        'key': API_KEY  # Your API key
    }
response = requests.get(url, params=params)
# Check if the request was successful
if response.status_code == 200:
    translation = response.json()['data']['translations'][0]['translatedText']
    print(f'Translated text: {translation}')
else:
    error = "Error: Exception in Google Translate. Defaulting to English"
    translation = text
    print("************** textResponseSrvr > google_translate_text > error:",error)
