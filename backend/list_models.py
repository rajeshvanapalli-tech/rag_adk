
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    print("Listing available embedding models...")
    for m in client.models.list(config={"page_size": 100}):
        if "embedding" in m.name:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
