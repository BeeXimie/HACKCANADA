from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify, session
from auth import auth0, run_async
import json
import sqlite3
from sqlalchemy import text
from models import db, User, UserScholarshipScore

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
        
        # Dynamic redirect back to the app home
        return redirect(url_for('main.index'))
    except Exception as e:
        return f"Authentication error: {str(e)}", 400

@main_bp.route('/profile')
def profile():
    """Protected route - shows user profile"""
    user = session.get("user")
    if not user:
        return redirect(url_for('main.login'))
    
    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    if not db_user:
        # Create user if doesn't exist (though onboarding should have created it)
        db_user = User(auth0_sub=user['sub'])
        db.session.add(db_user)
        db.session.commit()
        
    return render_template('profile.html', user=user, db_user=db_user)

@main_bp.route('/logout')
def logout():
    """Logout and redirect to Auth0 logout"""
    session.clear()
    logout_url = run_async(auth0.logout(g.store_options))
    # Return JSON for React if requested
    if request.headers.get('Accept') == 'application/json' or request.args.get('json'):
        return jsonify({"logout_url": logout_url})
    return redirect(logout_url)

@main_bp.route('/api/user/profile', methods=['GET', 'POST', 'PUT'])
async def api_user_profile():
    """Returns or updates the current user profile as JSON"""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    if not db_user:
        db_user = User(auth0_sub=user['sub'])
        db.session.add(db_user)
        db.session.commit()

    if request.method in ['POST', 'PUT']:
        # Support both JSON and Form data
        if request.is_json:
            data = request.get_json()
        else:
            # Convert ImmutableMultiDict to a plain dict
            data = request.form.to_dict()
            
            # Special handling for arrays like interests or experiences if sent via form
            if 'interests' in request.form:
                data['interests'] = request.form.getlist('interests')
        
        # Experiences handling if sent as individual arrays (profile.html style)
        if 'exp_company[]' in request.form:
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
            data['experiences'] = experiences

        db_user.from_dict(data)
        
        # Handle file deletions
        if data.get('delete_resume') == 'true':
            db_user.resume_uploaded = False
            db_user.resume_filename = None
        if data.get('delete_transcript') == 'true':
            db_user.transcript_uploaded = False
            db_user.transcript_filename = None

        # Handle file upload flags if files are in request
        if request.files:
            if 'resume' in request.files:
                res = request.files['resume']
                if res and res.filename != '':
                    db_user.resume_uploaded = True
                    db_user.resume_filename = res.filename
            if 'transcript' in request.files:
                trans = request.files['transcript']
                if trans and trans.filename != '':
                    db_user.transcript_uploaded = True
                    db_user.transcript_filename = trans.filename

        db.session.commit()
        return jsonify({"status": "ok", "profile": db_user.to_dict()})
        
    return jsonify({"user": user, "profile": db_user.to_dict()})

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
            'citizenship': request.form.get('citizenship', ''),
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
            
        session['scholarship_profile'] = profile
        print(f"DEBUG: Saved profile to session. Keys: {list(profile.keys())}")
        if profile.get('experiences'):
            print(f"DEBUG: Found {len(profile['experiences'])} experiences in profile.")
        
        # Sync Step 1 data to DB
        db_user.from_dict(profile)
        db.session.commit()
        
        # Redirect to Step 2 confirm page
        return redirect(url_for('main.onboarding_confirm'))
        
    return render_template('onboarding.html', user=user)


@main_bp.route('/onboarding_confirm', methods=['GET', 'POST'])
async def onboarding_confirm():
    """Step 2: Review AI-autofilled profile and save"""
    user = await auth0.get_user(g.store_options)
    if not user:
        return redirect(url_for('main.login'))
    
    profile = session.get('scholarship_profile', {})
    if not profile:
        return redirect(url_for('main.onboarding'))
    
    if request.method == 'POST':
        profile['institution'] = request.form.get('institution', '')
        profile['major'] = request.form.get('major', '')
        profile['degree'] = request.form.get('degree', '')
        profile['gpa'] = request.form.get('gpa_confirm', '')
        profile['gender'] = request.form.get('gender', '')
        profile['ethnicity'] = request.form.get('ethnicity', '')
        profile['enrollment'] = request.form.get('enrollment', '')
        profile['first_gen'] = request.form.get('first_gen', profile.get('first_gen', ''))
        profile['citizenship'] = request.form.get('citizenship', profile.get('citizenship', ''))
        
        grad_year_str = request.form.get('grad_year')
        profile['grad_year'] = int(grad_year_str) if grad_year_str and grad_year_str.isdigit() else 2025
        
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
        
        # Save to DB and mark onboarding complete
        db_user = User.query.filter_by(auth0_sub=user['sub']).first()
        if not db_user:
            db_user = User(auth0_sub=user['sub'])
            db.session.add(db_user)
            
        db_user.from_dict(profile)
        
        # Ensure db_user.id is populated then reset AI scores on profile update
        db.session.flush()
        from models import UserScholarshipScore
        UserScholarshipScore.query.filter_by(user_id=db_user.id).delete()
        
        db.session.commit()
        session['scholarship_profile'] = profile
        session['onboarding_complete'] = True
        return redirect(url_for('main.index'))
    
    return render_template('onboarding_confirm.html', user=user, profile=profile)


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
        
    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    # Allow viewing even if not fully onboarded (no profile)
    user_id = db_user.id if db_user else 0

    # Join scholarships with scores if they exist
    from sqlalchemy import text
    institution = db_user.institution if db_user else ""
    query = text("""
        SELECT s.*, us.score as match_score, us.reasoning as match_reasoning
        FROM ouinfo_scholarships s
        LEFT JOIN user_scholarship_scores us ON s.id = us.scholarship_id AND us.user_id = :user_id
        WHERE :institution = '' 
           OR s.university = 'External/Various' 
           OR s.university = 'Unknown'
           OR :institution LIKE '%' || s.university || '%'
           OR s.university LIKE '%' || :institution || '%'
        ORDER BY CASE WHEN us.score IS NULL THEN 0 ELSE 1 END DESC, us.score DESC, s.title ASC
    """)
    
    result = db.session.execute(query, {"user_id": user_id, "institution": institution})
    scholarships_data = [dict(row._mapping) for row in result]
    
    return render_template('scholarships.html', user=user, scholarships=scholarships_data)

@main_bp.route('/api/scholarships/score', methods=['POST'])
def api_score_scholarships():
    print("DEBUG: Received scoring request")
    """Batch score a set of scholarships for the current user."""
    from app import batch_analyze_scholarships
    
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    if not db_user:
        return jsonify({"error": "User not found"}), 404
        
    # Get scholarships to score (limit to 10 for safety/speed per call)
    data = request.get_json(silent=True) or {}
    scholarship_ids = data.get('ids', [])
    
    if not scholarship_ids:
        # If no IDs provided, find the top 10 un-scored scholarships that match user's university
        institution = db_user.institution or ""
        query = text("""
            SELECT id, title, description, eligibility 
            FROM ouinfo_scholarships 
            WHERE id NOT IN (SELECT scholarship_id FROM user_scholarship_scores WHERE user_id = :user_id)
              AND (
                  :institution = '' 
                  OR university = 'External/Various' 
                  OR university = 'Unknown'
                  OR :institution LIKE '%' || university || '%'
                  OR university LIKE '%' || :institution || '%'
              )
            LIMIT 10
        """)
        scholarships_to_score = [dict(row._mapping) for row in db.session.execute(query, {"user_id": db_user.id, "institution": institution})]
    else:
        # Find specific scholarships
        query = text("SELECT id, title, description, eligibility FROM ouinfo_scholarships WHERE id IN :ids")
        scholarships_to_score = [dict(row._mapping) for row in db.session.execute(query, {"ids": tuple(scholarship_ids)})]

    if not scholarships_to_score:
        return jsonify({"status": "no_more", "message": "All scholarships are already scored."})

    # Call Gemini
    profile = db_user.to_dict()
    print(f"DEBUG: Scoring {len(scholarships_to_score)} scholarships for user {db_user.id}")
    ai_response_json = batch_analyze_scholarships(profile, scholarships_to_score)
    print(f"DEBUG: Gemini response: {ai_response_json[:200]}...")
    ai_data = json.loads(ai_response_json)
    
    matches = ai_data.get('matches', [])
    for match in matches:
        sid = match['scholarship_id']
        # Update or Create score
        existing = UserScholarshipScore.query.filter_by(user_id=db_user.id, scholarship_id=sid).first()
        if existing:
            existing.score = match['match_score']
            existing.reasoning = match['reasoning']
        else:
            new_score = UserScholarshipScore(
                user_id=db_user.id,
                scholarship_id=sid,
                score=match['match_score'],
                reasoning=match['reasoning']
            )
            db.session.add(new_score)
            
    print(f"DEBUG: Saving {len(matches)} scores to database")
    db.session.commit()
    
    return jsonify({
        "status": "ok", 
        "scored_count": len(matches),
        "matches": matches
    })

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

    # Delete existing scores to force a re-evaluation on next "Match"
    db.session.flush() # Ensure db_user.id exists
    UserScholarshipScore.query.filter_by(user_id=db_user.id).delete()

    db.session.commit()
    profile = db_user.to_dict()
    session['scholarship_profile'] = profile
    return jsonify({"status": "ok", "profile": profile})

# --- Magic Bookmarklet API Endpoints ---

@main_bp.route('/api/user/autofill-data', methods=['GET'])
def get_autofill_data():
    """Return user profile data formatted for bookmarklet autofill."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized. Please log into ScholarSync first."}), 401
    
    # Query the live database for this user's profile
    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    if db_user:
        profile = db_user.to_dict()
    else:
        profile = session.get('scholarship_profile', {})
    
    # Extract names from Auth0 user object reliably
    full_name = user.get('name', '')
    first_name = full_name.split(' ')[0] if full_name else ''
    last_name = ' '.join(full_name.split(' ')[1:]) if len(full_name.split(' ')) > 1 else ''

    # We format this specifically for the JS bookmarklet to consume easily
    autofill_data = {
        "firstName": first_name,
        "lastName": last_name,
        "email": user.get('email', ''),
        "gpa": profile.get('gpa', ''),
        "major": profile.get('major', ''),
        "institution": profile.get('institution', ''),
        "location": profile.get('location', '')
    }
    
    return jsonify(autofill_data)

@main_bp.route('/api/ai/draft-essay', methods=['POST'])
def draft_essay_real():
    """Live endpoint for Gemini AI essay drafting using the Chrome Extension."""
    from app import client # Import Gemini client from main app
    
    user = session.get("user")
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "No prompt provided"}), 400
        
    scholarship_prompt = data.get('prompt')
    
    # Fetch from SQLite database
    db_user = User.query.filter_by(auth0_sub=user['sub']).first()
    if db_user:
        profile = db_user.to_dict()
    else:
        # Fallback to session if no db record yet
        profile = session.get('scholarship_profile', {})
        
    profile_str = "\n".join([f"{k}: {v}" for k, v in profile.items() if v and k != 'experiences'])
    
    # Append experiences context
    experiences = profile.get('experiences', [])
    if experiences:
        profile_str += "\nExperiences:\n"
        for exp in experiences:
            profile_str += f"- {exp.get('role')} at {exp.get('company')}: {exp.get('description')}\n"

    # Construct Prompt
    ai_prompt = (
        f"You are an expert college guidance counselor. "
        f"A student is applying for a scholarship. "
        f"Based on their profile below, write a compelling, tailored 3-bullet-point "
        f"response addressing the following scholarship prompt:\n\n"
        f"Scholarship Prompt: '{scholarship_prompt}'\n\n"
        f"Student Profile:\n{profile_str}\n\n"
        f"Output exactly 3 bullet points, each starting with '• '."
    )
    
    try:
        from google import genai
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=ai_prompt
        )
        return jsonify({"draft": response.text})
    except Exception as e:
        print(f"Gemini API Error in Chrome Extension: {e}")
        return jsonify({"draft": "• AI Error: Failed to generate response.\n• Please check API key status.\n• Ensure the backend is connected to the internet."})
    


