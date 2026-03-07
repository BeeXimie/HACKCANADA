from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from auth import auth0
import os

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
    logout_url = await auth0.logout(g.store_options)
    return redirect(logout_url)

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
    """
    Placeholder for Gemini API integration.
    Later, this API will take user data (e.g., expenses, profile)
    and use the Gemini model to generate insights or scholarship matches.
    """
    user = await auth0.get_user(g.store_options)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    
    # TODO: Implement Gemini API call here using google-generativeai package
    
    mock_response = {
        "status": "success",
        "message": "This is a placeholder for the Gemini response",
        "insights": [
            "Based on your profile, you could save $200 more per semester."
        ]
    }
    return jsonify(mock_response)
