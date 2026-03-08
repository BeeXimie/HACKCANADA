from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify, session
from auth import auth0, run_async
import os
import json
import sqlite3

main_bp = Blueprint('main', __name__)

# --- Authentication & User Profile Routes ---

@main_bp.route('/')
def index():
    """Home page - Landing page"""
    user = session.get("user")
    return render_template('index.html', user=user)

@main_bp.route('/login')
def login():
    """Redirect to Auth0 login"""
    authorization_url = run_async(auth0.start_interactive_login({}, g.store_options))
    return redirect(authorization_url)

@main_bp.route('/callback')
def callback():
    """Handle Auth0 callback after login"""
    try:
        # Complete the login handshake
        run_async(auth0.complete_interactive_login(str(request.url), g.store_options))
        
        # Explicitly fetch the user profile now that the handshake is done
        user = run_async(auth0.get_user(g.store_options))
        session["user"] = user
        
        return redirect("http://localhost:3000/")
    except Exception as e:
        return f"Authentication error: {str(e)}", 400

@main_bp.route('/profile')
def profile():
    """Protected route - shows user profile"""
    user = session.get("user")
    if not user:
        return redirect(url_for('main.login'))
    return render_template('profile.html', user=user)

@main_bp.route('/logout')
def logout():
    """Logout and redirect to Auth0 logout"""
    session.clear()
    logout_url = run_async(auth0.logout(g.store_options))
    return redirect(logout_url)

# --- Onboarding Route ---

@main_bp.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    """Onboarding form flow after login"""
    user = session.get("user")
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
        
        if resume and resume.filename:
            profile['resume_uploaded'] = True
            profile['resume_filename'] = resume.filename
        if transcript and transcript.filename:
            profile['transcript_uploaded'] = True
            profile['transcript_filename'] = transcript.filename
            
        session['scholarship_profile'] = profile
        session['onboarding_complete'] = True 
        
        return redirect("http://localhost:3000/")
        
    return render_template('onboarding.html', user=user)

# --- Feature Routes ---

@main_bp.route('/essay', methods=['GET', 'POST'])
def essay():
    """Essay Vault page"""
    user = session.get("user")
    if not user:
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        q1 = request.form.get('vault_q1', '')
        q2 = request.form.get('vault_q2', '')
        q3 = request.form.get('vault_q3', '')
        q4 = request.form.get('vault_q4', '')
        
        session['essay_vault'] = {
            'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4
        }
        return redirect(url_for('main.essay'))
        
    vault_data = session.get('essay_vault', {})
    return render_template('essay_vault.html', user=user, vault=vault_data)


@main_bp.route('/applied')
def applied():
    """Applied Tracker Kanban page"""
    user = session.get("user")
    if not user:
        return redirect(url_for('main.login'))
    return render_template('applied_tracker.html', user=user)

@main_bp.route('/scholarships')
def scholarships():
    """Finding scholarships page"""
    user = session.get("user")
    if not user:
        return redirect(url_for('main.login'))
        
    scholarships_data = []
    
    return render_template('scholarships.html', user=user, scholarships=scholarships_data)

@main_bp.route('/recommendations')
def recommendations():
    """Recommendations page"""
    user = session.get("user")
    if not user:
        return redirect(url_for('main.login'))
        
    return render_template('recommendations.html', user=user)

# --- API Routes (Gemini Integration Placeholder) ---

@main_bp.route('/api/gemini/analyze', methods=['POST'])
def gemini_analyze_api():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    scholarship_text = data.get("scholarship_details", "")
    profile = session.get('scholarship_profile', {})

    try:
        from app import analyze_scholarship_match
        json_result_string = analyze_scholarship_match(profile, scholarship_text)
        analysis_dict = json.loads(json_result_string)

        return jsonify({
            "status": "success",
            "analysis": analysis_dict
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- React Frontend JSON API Endpoints ---

@main_bp.route('/api/auth/profile')
def api_profile():
    """Return user profile as JSON for the React frontend"""
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "user": user})

@main_bp.route('/api/auth/logout')
def api_logout():
    """Return Auth0 logout URL as JSON for the React frontend"""
    logout_url = run_async(auth0.logout(g.store_options))
    return jsonify({"logout_url": logout_url})

# --- User Profile API ---

PROFILE_FIELDS = [
    'institution', 'major', 'degree', 'gpa', 'grad_year', 'enrollment',
    'income_bracket', 'first_gen', 'fafsa', 'aid_amount', 'ethnicity',
    'gender', 'location', 'disability', 'veteran', 'career_goals',
    'extracurriculars', 'interests'
]

@main_bp.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Return saved scholarship profile data for the current user."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    profile = session.get('scholarship_profile', {})
    return jsonify({"profile": profile})


@main_bp.route('/api/user/profile', methods=['POST'])
def save_user_profile():
    """Save scholarship profile data for the current user."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    profile = {k: data.get(k, '') for k in PROFILE_FIELDS}
    session['scholarship_profile'] = profile
    return jsonify({"status": "ok", "profile": profile})
