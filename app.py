from dotenv import load_dotenv
load_dotenv(override=True) # Load env vars before anything else

import os
from flask import Flask, request, g
from auth import auth0
from routes import main_bp
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
from models import db, User

load_dotenv(override=True)
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    print(f"DEBUG: Using GEMINI_API_KEY: {api_key[:8]}...{api_key[-4:]}")
    # Explicitly pass api_key to the client
    client = genai.Client(api_key=api_key)
else:
    print("WARNING: GEMINI_API_KEY not found in environment. AI features will be disabled.")
    client = None
class ScholarshipAnalysis(BaseModel):
    match_score: int = Field(description="Score from 0 to 100 on how well the user matches the scholarship")
    key_strengths: list[str] = Field(description="3 bullet points highlighting why they're a good fit")
    essay_outline: list[str] = Field(description="A brief 3-point outline for their application essay")

class ExperienceEntry(BaseModel):
    company: str = Field(description="Company or Organization name")
    role: str = Field(description="Title or Role")
    start_date: str = Field(description="Start date (e.g. June 2022)")
    end_date: str = Field(description="End date (e.g. August 2022) or 'Present'")
    current: bool = Field(description="True if they currently work here")
    description: str = Field(description="Brief summary of responsibilities")

class ResumeProfile(BaseModel):
    institution: str = Field(description="University or College name")
    major: str = Field(description="Field of Study or Major")
    degree: str = Field(description="Degree level (Undergraduate, Master's, PhD, High School)")
    grad_year: int = Field(description="Expected graduation year")
    experiences: list[ExperienceEntry] = Field(description="List of professional or academic experiences")
    interests: list[str] = Field(description="Relevant academic/professional interests (STEM, Arts, etc.)")

def analyze_scholarship_match(user_profile: dict, scholarship_details: str):
    if not client: return '{"error": "API Key missing"}'
    profile_str = "\n".join([f"{k}: {v}" for k, v in user_profile.items() if v])
    prompt = f"Analyze the fit between this student and the following scholarship.\n\nStudent Profile:\n{profile_str}\n\nScholarship Details:\n{scholarship_details}"
    try:
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
    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        return json.dumps({"match_score": 0, "key_strengths": ["Error analyzing match"], "essay_outline": ["Please try again later"]})

def parse_resume(resume_text: str):
    if not client: 
        return {
            "institution": "Unknown", "major": "Unknown", "degree": "Undergraduate",
            "grad_year": 2025, "experiences": [], "interests": []
        }
    
    if not resume_text or len(resume_text.strip()) < 10:
        print("DEBUG: Resume text too short or empty.")
        return {
            "institution": "No text extracted", "major": "Check resume format", "degree": "Undergraduate",
            "grad_year": 2025, "experiences": [], "interests": []
        }
    try:
        prompt = f"Extract professional and academic details from the following resume text:\n\n{resume_text}"
        print(f"DEBUG: Prompt length: {len(prompt)}")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Extract structured data from the resume. If a field is missing, use a sensible default or 'Unknown'.",
                response_mime_type="application/json",
                response_schema=ResumeProfile,
            )
        )
        print(f"DEBUG Gemini Response: {response.text}")
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini Parsing Error: {e}")
        return {
            "institution": "Error Parsing", "major": "Error Parsing", "degree": "Undergraduate",
            "grad_year": 2025, "experiences": [], "interests": []
        }

app = Flask(__name__)
app.secret_key = os.getenv('AUTH0_SECRET')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scholarships.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Configure session for Auth0
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

@app.before_request
def store_request_response():
    """Make request/response available for Auth0 SDK"""
    g.store_options = {"request": request}

# Register the blueprint containing all routes
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True, port=3000)