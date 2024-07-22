# pip install torch transformers huggingface_hub accelerate
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
from dotenv import load_dotenv
import os
load_dotenv()
from transformers import pipeline

# Authenticate with your Hugging Face token
login(token=os.getenv("HUGGING_FACE_API_TOKEN"))

# # Check if a GPU is available and use it
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# # Load the tokenizer and model
# tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-70B-Instruct")
# model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-70B-Instruct")

# # Move the model to the GPU if available
# model.to(device)

# # Function to generate a response from the model with specified characteristics
# def generate_response(prompt, characteristics):
#     # Combine characteristics instruction with the user prompt
#     combined_prompt = f"{characteristics}\n\n{prompt}"
#     inputs = tokenizer(combined_prompt, return_tensors="pt").to(device)
#     outputs = model.generate(inputs["input_ids"], max_length=100, num_return_sequences=1)
#     response = tokenizer.decode(outputs[0], skip_special_tokens=True)
#     return response

# # Example usage
# characteristics = "You are a helpful and friendly assistant. Please provide responses in a polite and informative manner."
# user_prompt = "Can you explain the theory of relativity?"
# response = generate_response(user_prompt, characteristics)
# print(response)


import transformers
import torch

model_id = "meta-llama/Meta-Llama-3-70B-Instruct"

pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
)

messages = [
    {"role": "system", "content": "You are a pirate chatbot who always responds in pirate speak!"},
    {"role": "user", "content": "Who are you?"},
]

terminators = [
    pipeline.tokenizer.eos_token_id,
    pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
]

outputs = pipeline(
    messages,
    max_new_tokens=256,
    eos_token_id=terminators,
    do_sample=True,
    temperature=0.6,
    top_p=0.9,
)
print(outputs[0]["generated_text"][-1])
