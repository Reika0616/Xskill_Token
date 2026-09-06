import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(".env")

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL")

print("Base URL:", base_url)
print("Model:", model)

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=30.0,
    max_retries=0,
)

print("\nSending tiny Chat Completions request...")

start = time.time()

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: CHAT_API_OK",
            }
        ],
        max_tokens=32,
    )

    elapsed = time.time() - start

    print("\nSUCCESS")
    print("Elapsed:", round(elapsed, 2), "seconds")
    print("Output:", response.choices[0].message.content)
    print("Model:", response.model)
    print("Usage:", response.usage)

except Exception as e:
    elapsed = time.time() - start

    print("\nFAILED")
    print("Elapsed:", round(elapsed, 2), "seconds")
    print("Type:", type(e).__name__)
    print("Error:", repr(e))
    raise
