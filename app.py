import os
from flask import Flask, redirect, render_template, request, url_for, g
from auth import auth0
from dotenv import load_dotenv

load_dotenv()

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

from flask import jsonify, send_from_directory

@app.route('/')
async def index():
    """Serve the React app in production, or JSON API status in dev"""
    return jsonify({"status": "API is running. Frontend dev server handles UI on port 3000."})

@app.route('/api/auth/profile')
async def profile():
    """Return user profile as JSON"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return jsonify({"authenticated": False}), 401
    
    return jsonify({
        "authenticated": True,
        "user": user
    })

@app.route('/login')
async def login():
    """Redirect to Auth0 login"""
    authorization_url = await auth0.start_interactive_login({}, g.store_options)
    return redirect(authorization_url)

@app.route('/callback')
async def callback():
    """Handle Auth0 callback after login"""
    try:
        result = await auth0.complete_interactive_login(str(request.url), g.store_options)
        # Redirect back to the React frontend running on port 3000 or production build
        return redirect("http://localhost:3000/")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/auth/logout')
async def logout():
    """Logout and redirect to Auth0 logout"""
    logout_url = await auth0.logout(g.store_options)
    return jsonify({"logout_url": logout_url})

if __name__ == '__main__':
    app.run(debug=True, port=5000)