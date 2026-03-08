import os
from dotenv import load_dotenv

load_dotenv()
print(f"AUTH0_REDIRECT_URI: {os.getenv('AUTH0_REDIRECT_URI')}")
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:5]}...")
