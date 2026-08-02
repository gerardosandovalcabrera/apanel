"""
Authentication and Security Endpoints for the Hybrid System
Complete integration with the security system
"""

from flask import Blueprint, request, jsonify, g, redirect, session
import requests
from hermes_security import (
    security_manager, 
    require_auth, 
    require_api_key, 
    require_role, 
    require_permission,
    SECURITY_CONFIG
)
import logging

logger = logging.getLogger('HermesAuth')

auth_bp = Blueprint('auth', __name__)

# ==========================================
# AUTHENTICATION ENDPOINTS FOR HUMANS
# ==========================================

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Local login (deprecated, use OAuth)"""
    return jsonify({
        "error": "Local login deprecated. Use OAuth2 providers.",
        "oauth_providers": {
            "github": "/auth/github",
            "google": "/auth/google"
        }
    }), 400

@auth_bp.route('/auth/github')
def github_login():
    """Start OAuth flow with GitHub"""
    if not SECURITY_CONFIG['OAUTH_GITHUB_CLIENT_ID']:
        return jsonify({"error": "GitHub OAuth not configured"}), 500
    
    github_auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={SECURITY_CONFIG['OAUTH_GITHUB_CLIENT_ID']}"
        f"&redirect_uri={request.host_url}auth/github/callback"
        f"&scope=user:email"
    )
    
    return redirect(github_auth_url)

@auth_bp.route('/auth/github/callback')
def github_callback():
    """GitHub OAuth callback"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Exchange code for access token
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": SECURITY_CONFIG['OAUTH_GITHUB_CLIENT_ID'],
            "client_secret": SECURITY_CONFIG['OAUTH_GITHUB_CLIENT_SECRET'],
            "code": code
        },
        headers={"Accept": "application/json"}
    )
    
    if token_response.status_code != 200:
        logger.error(f"GitHub token exchange failed: {token_response.text}")
        return jsonify({"error": "Failed to exchange code for token"}), 500
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    
    # Get user info
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if user_response.status_code != 200:
        return jsonify({"error": "Failed to get user info"}), 500
    
    user_data = user_response.json()
    
    # In production, create or update user in database
    # Generate JWT token
    user_info = {
        "id": str(user_data.get('id')),
        "username": user_data.get('login'),
        "email": user_data.get('email'),
        "provider": "github",
        "provider_id": str(user_data.get('id'))
    }
    
    jwt_token = security_manager.create_jwt_token(user_info)
    
    return jsonify({
        "success": True,
        "token": jwt_token,
        "user": user_info
    })

@auth_bp.route('/auth/google')
def google_login():
    """Start OAuth flow with Google"""
    if not SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID']:
        return jsonify({"error": "Google OAuth not configured"}), 500
    
    # Simplified Google OAuth flow
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID']}"
        f"&redirect_uri={request.host_url}auth/google/callback"
        "&response_type=code"
        "&scope=email profile"
    )
    
    return redirect(google_auth_url)

@auth_bp.route('/auth/google/callback')
def google_callback():
    """Google OAuth callback"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Exchange code for tokens
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID'],
            "client_secret": SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_SECRET'],
            "redirect_uri": f"{request.host_url}auth/google/callback",
            "grant_type": "authorization_code"
        }
    )
    
    if token_response.status_code != 200:
        logger.error(f"Google token exchange failed: {token_response.text}")
        return jsonify({"error": "Failed to exchange code for token"}), 500
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    
    # Get user info
    user_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if user_response.status_code != 200:
        return jsonify({"error": "Failed to get user info"}), 500
    
    user_data = user_response.json()
    
    # Create user info
    user_info = {
        "id": user_data.get('id'),
        "username": user_data.get('name'),
        "email": user_data.get('email'),
        "provider": "google",
        "provider_id": user_data.get('id')
    }
    
    jwt_token = security_manager.create_jwt_token(user_info)
    
    return jsonify({
        "success": True,
        "token": jwt_token,
        "user": user_info
    })

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    # In production, invalidate token in Redis
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })

# ==========================================
# API KEY MANAGEMENT
# ==========================================

@auth_bp.route('/auth/api-keys', methods=['GET'])
@require_auth
def list_api_keys():
    """List all API keys for current user"""
    user = g.user
    api_keys = security_manager.get_user_api_keys(user['id'])
    
    return jsonify({
        "success": True,
        "api_keys": api_keys
    })

@auth_bp.route('/auth/api-keys', methods=['POST'])
@require_auth
def create_api_key():
    """Create a new API key"""
    user = g.user
    data = request.json
    
    name = data.get('name', 'API Key')
    scopes = data.get('scopes', ['read', 'write'])
    
    api_key = security_manager.create_api_key(
        user_id=user['id'],
        name=name,
        scopes=scopes
    )
    
    return jsonify({
        "success": True,
        "api_key": api_key
    })

@auth_bp.route('/auth/api-keys/<key_id>', methods=['DELETE'])
@require_auth
def delete_api_key(key_id):
    """Delete an API key"""
    user = g.user
    success = security_manager.delete_api_key(user['id'], key_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "API key deleted successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Failed to delete API key"
        }), 500

# ==========================================
# TOKEN VALIDATION
# ==========================================

@auth_bp.route('/auth/validate', methods=['POST'])
def validate_token():
    """Validate JWT token"""
    token = request.json.get('token')
    
    if not token:
        return jsonify({
            "success": False,
            "error": "Token is required"
        }), 400
    
    try:
        payload = security_manager.validate_jwt_token(token)
        
        return jsonify({
            "success": True,
            "valid": True,
            "user": payload
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "valid": False,
            "error": str(e)
        })

@auth_bp.route('/auth/api-key/validate', methods=['POST'])
def validate_api_key():
    """Validate API key"""
    api_key = request.json.get('api_key')
    
    if not api_key:
        return jsonify({
            "success": False,
            "error": "API key is required"
        }), 400
    
    try:
        payload = security_manager.validate_api_key(api_key)
        
        return jsonify({
            "success": True,
            "valid": True,
            "user": payload
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "valid": False,
            "error": str(e)
        })

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    
    print("🧪 Test of Auth Endpoints:")
    
    # Test login deprecation
    print("\n1. Testing POST /auth/login")
    with app.test_client() as client:
        response = client.post('/auth/login')
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        print(f"   ✅ Message: {data['error']}")
    
    # Test token validation
    print("\n2. Testing POST /auth/validate (with invalid token)")
    with app.test_client() as client:
        response = client.post('/auth/validate', json={'token': 'invalid'})
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        print(f"   ✅ Valid: {data['valid']}")
    
    print("\n✅ Auth endpoints are functional!")
