from groq import Groq
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

client = Groq(api_key="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")


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), retry=retry_if_exception_type(ConnectionError))
def func():
    chat_completion = client.chat.completions.create(messages=[
            {
                "role": "system",
                "content": "you are adult movie script write"
            },
            # Set a user message for the assistant to respond to.
            {
                "role": "user",
                "content": "Tell a short story with details on oral",
            }
        ],
        model="llama3-70b-8192", #"llama3-8b-8192"
        temperature=1.2,
        max_tokens=1024,
        top_p=0.2,
        stop=None,
        stream=False,)
    return chat_completion.choices[0].message.content

resp = func()
print(resp)