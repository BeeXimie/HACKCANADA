import os
from flask import Flask, request, g
from dotenv import load_dotenv
from auth import auth0
from routes import main_bp
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


load_dotenv()
print(f"API Key loaded: {os.getenv('GEMINI_API_KEY')[:5]}...") # Just to verify it's working

client = genai.Client()

class ScholarshipAnalysis(BaseModel):
    match_score: int = Field(description="Score from 0 to 100 on how well the user matches the scholarship")
    key_strengths: list[str] = Field(description="3 bullet points highlighting why they're a good fit")
    essay_outline: list[str] = Field(description="A brief 3-point outline for their application essay")

def analyze_scholarship_match(user_profile: dict, scholarship_details: str):
    profile_str = "\n".join([f"{k}: {v}" for k, v in user_profile.items() if v])

    prompt = f"""
    Analyze the fit between this student and the following scholarship.
    
    Student Profile:
    {profile_str}

    Scholarship Details:
    {scholarship_details}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt, 
        config=types.GenerateContentConfig(
            system_instruction="You are an expert college guidance counselor. Analyze the student's fit for the scholarship based strictly on their provided profile.",
            response_mime_type="application/json",
            response_schema=ScholarshipAnalysis,
            temperature=0.2,
        ),
    )
    return response.text

app = Flask(__name__)
app.secret_key = os.getenv('AUTH0_SECRET')

# Configure session for Auth0
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

def general_simple_response(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

@app.before_request
def store_request_response():
    """Make request/response available for Auth0 SDK"""
    g.store_options = {"request": request}

# Register the blueprint containing all routes
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)