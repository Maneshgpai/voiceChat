# pip install transformers torch sentencepiece

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Load pre-trained transformer model
# model_name = "ai4bharat/indictrans"
model_name = "ai4bharat/indictrans2-indic-en-1B"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)

# def translate_and_transliterate(input_text, src_lang="en", tgt_lang="hi_Latn"):
#     tokenized_input = tokenizer(input_text, return_tensors="pt")
#     result = model.generate(**tokenized_input, forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang])
#     translated_text = tokenizer.decode(result[0], skip_special_tokens=True)
#     return translated_text

# # Define your input text
# input_text = "Hello, how are you?"

# # Translate and transliterate to Hinglish (Hindi Roman script)
# hinglish_text = translate_and_transliterate(input_text)

# print(f"Original Text: {input_text}")
# print(f"Hinglish Text: {hinglish_text}")



ip = IndicProcessor(inference=True)

input_sentences = [
    "When I was young, I used to go to the park every day.",
    "We watched a new movie last week, which was very inspiring.",
    "If you had met me at that time, we would have gone out to eat.",
    "My friend has invited me to his birthday party, and I will give him a gift.",
]

src_lang, tgt_lang = "eng_Latn", "hin_Deva"

batch = ip.preprocess_batch(
    input_sentences,
    src_lang=src_lang,
    tgt_lang=tgt_lang,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Tokenize the sentences and generate input encodings
inputs = tokenizer(
    batch,
    truncation=True,
    padding="longest",
    return_tensors="pt",
    return_attention_mask=True,
).to(DEVICE)

# Generate translations using the model
with torch.no_grad():
    generated_tokens = model.generate(
        **inputs,
        use_cache=True,
        min_length=0,
        max_length=256,
        num_beams=5,
        num_return_sequences=1,
    )

# Decode the generated tokens into text
with tokenizer.as_target_tokenizer():
    generated_tokens = tokenizer.batch_decode(
        generated_tokens.detach().cpu().tolist(),
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )

# Postprocess the translations, including entity replacement
translations = ip.postprocess_batch(generated_tokens, lang=tgt_lang)

for input_sentence, translation in zip(input_sentences, translations):
    print(f"{src_lang}: {input_sentence}")
    print(f"{tgt_lang}: {translation}")