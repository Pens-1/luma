import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")

if not GEMINI_KEY:
    print("GOOGLE_GEMINI_API_KEY not found")
    exit(1)

genai.configure(api_key=GEMINI_KEY)

try:
    print("Listing models...")
    for m in genai.list_models():
        print(f"Found: {m.name}")

    test_model = "models/gemini-1.5-flash"
    print(f"Testing with: {test_model}")
    model = genai.GenerativeModel(test_model)
    response = model.generate_content("Hello")
    print(f"Response: {response.text}")
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
