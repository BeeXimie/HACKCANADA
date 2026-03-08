import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv('GEMINI_API_KEY')
print(f"Testing with API Key starting with: {api_key[:8]}")
client = genai.Client(api_key=api_key)

try:
    print("Listing ALL available models...")
    models = list(client.models.list())
    all_names = []
    for model in models:
        print(f"Model ID: {model.name}")
        all_names.append(model.name)
    
    print("\nTesting connectivity with top candidates...")
    candidates = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    
    # Process the list to find names
    for name in all_names:
        base_name = name.split('/')[-1]
        if base_name not in candidates and "flash" in base_name:
            candidates.append(base_name)

    for m in candidates:
        try:
            print(f"Trying '{m}'...", end=" ", flush=True)
            response = client.models.generate_content(model=m, contents="Say 'OK'")
            print(f" SUCCESS: {response.text.strip()}")
            print(f"--- RECOMMENDED MODEL: {m} ---")
            break
        except Exception as e:
            print(f" FAILED: {str(e)[:100]}...")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
