from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify, session
from auth import auth0, run_async
from models import db, User
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

from pypdf import PdfReader
import io

# --- Onboarding Route ---

@main_bp.route('/onboarding', methods=['GET', 'POST'])
async def onboarding():
    """Step 1: Basic Info & Resume Upload"""
    from app import parse_resume # Local import to avoid circular dependency
    
    user = await auth0.get_user(g.store_options)
    if not user:
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        location = request.form.get('location')
        gpa = request.form.get('gpa')
        gender = request.form.get('gender')
        ethnicity = request.form.get('ethnicity')
        citizenship = request.form.get('citizenship')
        year_of_study = request.form.get('year_of_study')
        resume = request.files.get('resume')
        transcript = request.files.get('transcript')
        
        profile = session.get('scholarship_profile', {})
        # Initialize defaults so Step 2 always has values
        profile.update({
            'location': location,
            'gpa': gpa,
            'gender': gender,
            'ethnicity': ethnicity,
            'citizenship': citizenship,
            'year_of_study': year_of_study,
            'income_bracket': request.form.get('income_bracket', ''),
            'first_gen': request.form.get('first_gen', ''),
            'fafsa': request.form.get('fafsa', ''),
            'enrollment': request.form.get('enrollment', ''),
            'disability': request.form.get('disability', ''),
            'veteran': request.form.get('veteran', ''),
            "institution": "", 
            "major": "", 
            "degree": "Undergraduate",
            "grad_year": 2025, 
            "experiences": [], 
            "interests": [], 
            "career_goals": "",
            "aid_amount": 0,
            "resume_uploaded": False,
            "resume_filename": "",
            "transcript_uploaded": False,
            "transcript_filename": ""
        })
        
        # AI Extraction from Resume (Optional)
        if resume and resume.filename.endswith('.pdf'):
            try:
                reader = PdfReader(io.BytesIO(resume.read()))
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                
                print(f"DEBUG: Extracted {len(text)} characters from resume PDF.")
                
                # Call Gemini to parse the extracted text
                ai_data = parse_resume(text)
                profile.update(ai_data) # Overwrite defaults with AI data
                profile['resume_uploaded'] = True
                profile['resume_filename'] = resume.filename
            except Exception as e:
                print(f"Resume parsing error: {e}")
                
        # Handle Transcript (Simple upload for now)
        if transcript and transcript.filename != '':
            profile['transcript_uploaded'] = True
            profile['transcript_filename'] = transcript.filename
            # Future: save file to disk/cloud
        # Update or Create User in DB
        db_user = User.query.filter_by(auth0_sub=user['sub']).first()
        if not db_user:
            db_user = User(auth0_sub=user['sub'])
            db.session.add(db_user)
            
        # Handle Step 2 fields if present
        if 'institution' in request.form:
            profile['institution'] = request.form.get('institution')
            profile['major'] = request.form.get('major')
            profile['degree'] = request.form.get('degree')
            profile['gpa'] = request.form.get('gpa_confirm')
            
            grad_year_str = request.form.get('grad_year')
            profile['grad_year'] = int(grad_year_str) if grad_year_str else 2025
            
            profile['interests'] = request.form.getlist('interests')
            
            aid_amount_str = request.form.get('aid_amount')
            profile['aid_amount'] = float(aid_amount_str) if aid_amount_str else 0.0
            
            # Consolidate dynamic experiences
            companies = request.form.getlist('exp_company[]')
            roles = request.form.getlist('exp_role[]')
            starts = request.form.getlist('exp_start[]')
            ends = request.form.getlist('exp_end[]')
            currents = request.form.getlist('exp_current[]')
            vols = request.form.getlist('exp_volunteer[]')
            hours = request.form.getlist('exp_hours[]')
            descs = request.form.getlist('exp_desc[]')
            
            experiences = []
            for i in range(len(companies)):
                exp = {
                    'company': companies[i],
                    'role': roles[i] if i < len(roles) else "",
                    'start_date': starts[i] if i < len(starts) else "",
                    'end_date': ends[i] if i < len(ends) else "",
                    'current': currents[i] == 'true' if i < len(currents) else False,
                    'volunteer': vols[i] == 'true' if i < len(vols) else False,
                    'hours': hours[i] if i < len(hours) and hours[i] else None,
                    'description': descs[i] if i < len(descs) else ""
                }
                experiences.append(exp)
            profile['experiences'] = experiences
            
            # Save to DB and mark complete
            db_user.from_dict(profile)
            db.session.commit()
            session['scholarship_profile'] = profile
            session['onboarding_complete'] = True
            return redirect(url_for('main.profile'))

        # Sync Step 1 data to DB
        db_user.from_dict(profile)
        db.session.commit()
        
        session['scholarship_profile'] = profile
        
        # If AJAX request, return JSON for the frontend to handle navigation
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"status": "ok", "profile": profile})
            
        return redirect(url_for('main.profile'))
        
    return render_template('onboarding.html', user=user)


# --- Feature Routes ---

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
    'extracurriculars', 'interests', 'year_of_study', 'experiences',
    'resume_uploaded', 'resume_filename', 'transcript_uploaded', 'transcript_filename'
]

@main_bp.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Return saved scholarship profile data for the current user."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    if db_user:
        return jsonify({"profile": db_user.to_dict()})
        
    # Fallback to session if no DB record yet
    profile = session.get('scholarship_profile', {})
    return jsonify({"profile": profile})


@main_bp.route('/api/user/profile', methods=['POST'])
async def save_user_profile():
    """Save scholarship profile data for the current user (handles multipart for files)."""
    user = await auth0.get_user(g.store_options)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # Check if multipart (for file uploads) or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        files = request.files
    else:
        data = request.get_json()
        files = {}

    if not data and not files:
        return jsonify({"error": "No data provided"}), 400

    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    if not db_user:
        db_user = User(auth0_sub=user['sub'])
        db.session.add(db_user)

    # Update fields from data and handle files
    # Exclude delete_resume and delete_transcript from normal field update
    profile_data = {k: v for k, v in data.items() if k not in ['delete_resume', 'delete_transcript']}
    
    # Consolidate dynamic experiences if present in multipart form
    if 'exp_company[]' in data:
        companies = request.form.getlist('exp_company[]')
        roles = request.form.getlist('exp_role[]')
        starts = request.form.getlist('exp_start[]')
        ends = request.form.getlist('exp_end[]')
        currents = request.form.getlist('exp_current[]')
        vols = request.form.getlist('exp_volunteer[]')
        hours = request.form.getlist('exp_hours[]')
        descs = request.form.getlist('exp_desc[]')
        
        experiences = []
        for i in range(len(companies)):
            exp = {
                'company': companies[i],
                'role': roles[i] if i < len(roles) else "",
                'start_date': starts[i] if i < len(starts) else "",
                'end_date': ends[i] if i < len(ends) else "",
                'current': currents[i] == 'true' if i < len(currents) else False,
                'volunteer': vols[i] == 'true' if i < len(vols) else False,
                'hours': hours[i] if i < len(hours) and hours[i] else None,
                'description': descs[i] if i < len(descs) else ""
            }
            experiences.append(exp)
        profile_data['experiences'] = experiences

    db_user.from_dict(profile_data)

    # Handle file deletion
    if data.get('delete_resume') == 'true':
        db_user.resume_uploaded = False
        db_user.resume_filename = None
        
    if data.get('delete_transcript') == 'true':
        db_user.transcript_uploaded = False
        db_user.transcript_filename = None

    # Handle file uploads
    if 'resume' in files:
        resume = files['resume']
        if resume and resume.filename != '':
            db_user.resume_uploaded = True
            db_user.resume_filename = resume.filename
            # Future: save to Cloudinary/Disk
    
    if 'transcript' in files:
        transcript = files['transcript']
        if transcript and transcript.filename != '':
            db_user.transcript_uploaded = True
            db_user.transcript_filename = transcript.filename
            # Future: save to Cloudinary/Disk

    db.session.commit()
    profile = db_user.to_dict()
>>>>>>> a01d58e (Refine onboarding flow and profile experience UI sync)
    session['scholarship_profile'] = profile
    return jsonify({"status": "ok", "profile": profile})
