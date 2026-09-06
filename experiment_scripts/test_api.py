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
    timeout=60.0,
)

print("\nSending tiny request...")

start = time.time()

try:
    response = client.responses.create(
        model=model,
        input="Reply with exactly: API_TEST_OK",
        max_output_tokens=32,
        store=False,
    )

    elapsed = time.time() - start

    print("\nSUCCESS")
    print("Elapsed:", round(elapsed, 2), "seconds")
    print("Response ID:", getattr(response, "id", None))
    print("Model:", getattr(response, "model", None))
    print("Output:", response.output_text)

    if getattr(response, "usage", None):
        print("Usage:", response.usage)

except Exception as e:
    elapsed = time.time() - start

    print("\nFAILED")
    print("Elapsed:", round(elapsed, 2), "seconds")
    print("Exception type:", type(e).__name__)
    print("Exception:", repr(e))

    raise
