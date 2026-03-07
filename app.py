import os
from flask import Flask, request, g
from dotenv import load_dotenv
from auth import auth0
from routes import main_bp
from dotenv import load_dotenv
import os

load_dotenv()
print(f"API Key loaded: {os.getenv('GEMINI_API_KEY')[:5]}...") # Just to verify it's working


app = Flask(__name__)
app.secret_key = os.getenv('AUTH0_SECRET')

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
    app.run(debug=True, port=5000)