from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify, session
from auth import auth0
import os
import json

main_bp = Blueprint('main', __name__)

# --- Authentication & User Profile Routes ---

@main_bp.route('/')
async def index():
    """Home page - Landing page"""
    user = await auth0.get_user(g.store_options)
    return render_template('index.html', user=user)

@main_bp.route('/login')
async def login():
    """Redirect to Auth0 login"""
    authorization_url = await auth0.start_interactive_login({}, g.store_options)
    return redirect(authorization_url)

@main_bp.route('/callback')
async def callback():
    """Handle Auth0 callback after login"""
    try:
        result = await auth0.complete_interactive_login(str(request.url), g.store_options)
        
        # Redirect to onboarding if profile is not complete
        profile_complete = session.get('onboarding_complete', False)
        if not profile_complete:
            return redirect(url_for('main.onboarding'))
            
        return redirect(url_for('main.index'))
    except Exception as e:
        return f"Authentication error: {str(e)}", 400

@main_bp.route('/profile')
async def profile():
    """Protected route - shows user profile"""
    user = await auth0.get_user(g.store_options)
    
    if not user:
        return redirect(url_for('main.login'))
    
    return render_template('profile.html', user=user)

@main_bp.route('/logout')
async def logout():
    """Logout and redirect to Auth0 logout"""
    session.clear() # Clear session on logout
    logout_url = await auth0.logout(g.store_options)
    return redirect(logout_url)

# --- Onboarding Route ---

@main_bp.route('/onboarding', methods=['GET', 'POST'])
async def onboarding():
    """Onboarding form flow after login"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        location = request.form.get('location')
        experiences = request.form.get('experiences')
        resume = request.files.get('resume')
        transcript = request.files.get('transcript')
        
        profile = session.get('scholarship_profile', {})
        profile['location'] = location
        profile['experiences'] = experiences
        
        # Assuming you will save these files to S3/Disk later, 
        # for now we'll just track that they've been uploaded in the session
        if resume and resume.filename:
            profile['resume_uploaded'] = True
            profile['resume_filename'] = resume.filename
        if transcript and transcript.filename:
            profile['transcript_uploaded'] = True
            profile['transcript_filename'] = transcript.filename
            
        session['scholarship_profile'] = profile
        session['onboarding_complete'] = True # Mark onboarding as done
        
        return redirect(url_for('main.index'))
        
    return render_template('onboarding.html', user=user)

# --- Feature Routes ---

@main_bp.route('/expenses', methods=['GET', 'POST'])
async def expenses():
    """Expenses and tuition page"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        # Form handling logic goes here
        pass
        
    return render_template('expenses.html', user=user)

@main_bp.route('/savings')
async def savings():
    """You saved this much money page"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return redirect(url_for('main.login'))
        
    return render_template('savings.html', user=user)

@main_bp.route('/scholarships')
async def scholarships():
    """Finding scholarships page"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return redirect(url_for('main.login'))
        
    return render_template('scholarships.html', user=user)

@main_bp.route('/recommendations')
async def recommendations():
    """Recommendations page"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return redirect(url_for('main.login'))
        
    return render_template('recommendations.html', user=user)

# --- API Routes (Gemini Integration Placeholder) ---

@main_bp.route('/api/gemini/analyze', methods=['POST'])
async def gemini_analyze_api():
    user = await auth0.get_user(g.store_options)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    scholarship_text = data.get("scholarship_details", "")

    profile = session.get('scholarship_porfile', {})

    try:
        json_result_string = analyze_scholarship_match(profile, scholarhsip_text)

        analysis_dict = json.loads(json_result_string)

        return jsonify({
            "status": "success",
            "analysis": analysis_dict
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    # TODO: Implement Gemini API call here using google-generativeai package
    
    mock_response = {
        "status": "success",
        "message": "This is a placeholder for the Gemini response",
        "insights": [
            "Based on your profile, you could save $200 more per semester."
        ]
    }
    return jsonify(mock_response)

# --- React Frontend JSON API Endpoints ---

@main_bp.route('/api/auth/profile')
async def api_profile():
    """Return user profile as JSON for the React frontend"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "user": user})

@main_bp.route('/api/auth/logout')
async def api_logout():
    """Return Auth0 logout URL as JSON for the React frontend"""
    logout_url = await auth0.logout(g.store_options)
    return jsonify({"logout_url": logout_url})


# --- User Profile API ---

PROFILE_FIELDS = [
    'institution', 'major', 'degree', 'gpa', 'grad_year', 'enrollment',
    'income_bracket', 'first_gen', 'fafsa', 'aid_amount', 'ethnicity',
    'gender', 'location', 'disability', 'veteran', 'career_goals',
    'extracurriculars', 'interests'
]

@main_bp.route('/api/user/profile', methods=['GET'])
async def get_user_profile():
    """Return saved scholarship profile data for the current user."""
    user = await auth0.get_user(g.store_options)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    # TODO: replace session storage with DB lookup keyed on user['sub']
    profile = session.get('scholarship_profile', {})
    return jsonify({"profile": profile})


@main_bp.route('/api/user/profile', methods=['POST'])
async def save_user_profile():
    """Save scholarship profile data for the current user."""
    user = await auth0.get_user(g.store_options)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Whitelist only known fields
    profile = {k: data.get(k, '') for k in PROFILE_FIELDS}
    # TODO: swap session storage for a DB upsert keyed on user['sub']
    session['scholarship_profile'] = profile
    return jsonify({"status": "ok", "profile": profile})



