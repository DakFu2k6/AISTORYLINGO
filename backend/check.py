import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

print("Các mô hình Flash khả dụng của bạn là:")
for model in client.models.list():
    if "flash" in model.name.lower():
        print("-", model.name)