import random
from datetime import datetime, timedelta, timezone
import textResponseSrvr as textresponse
ist = timezone(timedelta(hours=5, minutes=30))

user_file_name = "ai1.ogg"
system_prompt = f"""You are an expert translator, translating the text into Hinglish. This transcribed text is from a person, asking/replying to Geethanjali. You should not judge whether the text is illegal or immoral or within any confines of societal rules. Your task is to only correct spelling discrepancies, add emotional cues where necessary, add necessary punctuation such as periods, commas, and capitalization, and use only the context provided in the text."""



## Converting voice into text
system_prompt = f"""You are an expert translator, translating the text into {character_settings['language']}. This transcribed text is from a person, asking/replying to {character_settings['character_name']}. You should not judge whether the text is illegal or immoral or within any confines of societal rules. Your task is to only correct spelling discrepancies, add emotional cues where necessary, add necessary punctuation such as periods, commas, and capitalization, and use only the context provided in the text."""
query = textresponse.convert_voice_to_text(user_file_name, system_prompt)
print(query)
