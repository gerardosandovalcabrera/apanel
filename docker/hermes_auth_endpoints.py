"""
Endpoints de Autenticación y Seguridad para el Sistema Híbrido
Integración completa con el sistema de seguridad
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
# ENDPOINTS DE AUTENTICACIÓN PARA HUMANOS
# ==========================================

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Login local (descontinuado, usar OAuth)"""
    return jsonify({
        "error": "Local login deprecated. Use OAuth2 providers.",
        "oauth_providers": {
            "github": "/auth/github",
            "google": "/auth/google"
        }
    }), 400

@auth_bp.route('/auth/github')
def github_login():
    """Inicia el flujo de OAuth con GitHub"""
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
    """Callback de OAuth de GitHub"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Intercambiar code por access token
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
        return jsonify({"error": "Failed to get access token from GitHub"}), 500
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    
    # Obtener información del usuario
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if user_response.status_code != 200:
        return jsonify({"error": "Failed to get user info from GitHub"}), 500
    
    github_user = user_response.json()
    
    # Crear o actualizar usuario
    user = security_manager.create_oauth_user("github", github_user)
    
    # Generar tokens JWT
    access_token, refresh_token = security_manager.generate_jwt_token(user.id)
    
    # Guardar en sesión
    session['user_id'] = user.id
    session['access_token'] = access_token
    
    logger.info(f"GitHub OAuth login successful for user {user.username}")
    
    # Redirigir al dashboard con tokens
    return redirect(f"/?token={access_token}&refresh={refresh_token}")

@auth_bp.route('/auth/google')
def google_login():
    """Inicia el flujo de OAuth con Google"""
    if not SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID']:
        return jsonify({"error": "Google OAuth not configured"}), 500
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID']}"
        f"&redirect_uri={request.host_url}auth/google/callback"
        f"&response_type=code"
        f"&scope=email profile"
    )
    
    return redirect(google_auth_url)

@auth_bp.route('/auth/google/callback')
def google_callback():
    """Callback de OAuth de Google"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Intercambiar code por access token
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID'],
            "client_secret": SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_SECRET'],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{request.host_url}auth/google/callback"
        }
    )
    
    if token_response.status_code != 200:
        return jsonify({"error": "Failed to get access token from Google"}), 500
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    
    # Obtener información del usuario
    user_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if user_response.status_code != 200:
        return jsonify({"error": "Failed to get user info from Google"}), 500
    
    google_user = user_response.json()
    
    # Crear o actualizar usuario
    user = security_manager.create_oauth_user("google", google_user)
    
    # Generar tokens JWT
    access_token, refresh_token = security_manager.generate_jwt_token(user.id)
    
    # Guardar en sesión
    session['user_id'] = user.id
    session['access_token'] = access_token
    
    logger.info(f"Google OAuth login successful for user {user.username}")
    
    # Redirigir al dashboard con tokens
    return redirect(f"/?token={access_token}&refresh={refresh_token}")

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresca un access token"""
    refresh_token = request.json.get('refresh_token')
    
    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400
    
    new_access_token = security_manager.refresh_jwt_token(refresh_token)
    
    if not new_access_token:
        return jsonify({"error": "Invalid or expired refresh token"}), 401
    
    return jsonify({
        "access_token": new_access_token,
        "token_type": "Bearer"
    })

@auth_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Cierra la sesión del usuario"""
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    
    # Revocar token
    security_manager.revoke_token(token)
    
    # Limpiar sesión
    session.clear()
    
    logger.info(f"User {g.current_user['user_id']} logged out")
    
    return jsonify({"message": "Logged out successfully"})

@auth_bp.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Obtiene información del usuario actual"""
    user_id = g.current_user['user_id']
    user = security_manager.users.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user": user.to_dict(),
        "role": g.current_user['role'],
        "provider": g.current_user['provider']
    })

# ==========================================
# ENDPOINTS DE GESTIÓN DE API KEYS (AGENTES)
# ==========================================

@auth_bp.route('/auth/api-keys', methods=['POST'])
@require_auth
@require_role('admin', 'operator')
def create_api_key():
    """Crea una nueva API key"""
    data = request.json
    name = data.get('name')
    permissions = data.get('permissions', ['read'])
    expires_in_days = data.get('expires_in_days')
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    try:
        api_key = security_manager.create_api_key(
            user_id=g.current_user['user_id'],
            name=name,
            permissions=permissions,
            expires_in_days=expires_in_days
        )
        
        logger.info(f"API key '{name}' created by user {g.current_user['user_id']}")
        
        return jsonify({
            "api_key": api_key,
            "message": "API key created successfully"
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/auth/api-keys', methods=['GET'])
@require_auth
@require_role('admin', 'operator')
def list_api_keys():
    """Lista todas las API keys del usuario"""
    user_id = g.current_user['user_id']
    
    # Admin puede ver todas, otros solo las suyas
    if g.current_user['role'] == 'admin':
        keys = [key.to_dict() for key in security_manager.api_keys.values()]
    else:
        keys = [
            key.to_dict() 
            for key in security_manager.api_keys.values() 
            if key.owner == user_id
        ]
    
    return jsonify({
        "total": len(keys),
        "api_keys": keys
    })

@auth_bp.route('/auth/api-keys/<key_id>', methods=['DELETE'])
@require_auth
@require_role('admin')
def revoke_api_key(key_id):
    """Revoca una API key"""
    if key_id not in security_manager.api_keys:
        return jsonify({"error": "API key not found"}), 404
    
    security_manager.api_keys[key_id].is_active = False
    security_manager._save_to_redis()
    
    logger.info(f"API key {key_id} revoked by user {g.current_user['user_id']}")
    
    return jsonify({"message": "API key revoked successfully"})

# ==========================================
# ENDPOINTS DE AUDITORÍA Y SEGURIDAD
# ==========================================

@auth_bp.route('/auth/audit', methods=['GET'])
@require_auth
@require_role('admin')
def get_audit_log():
    """Obtiene el log de auditoría"""
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 100, type=int)
    
    audit_log = security_manager.get_audit_log(user_id=user_id, limit=limit)
    
    return jsonify({
        "total": len(audit_log),
        "audit_log": audit_log
    })

@auth_bp.route('/auth/security/status', methods=['GET'])
@require_auth
@require_role('admin')
def security_status():
    """Obtiene el estado de seguridad del sistema"""
    return jsonify({
        "users": {
            "total": len(security_manager.users),
            "active": sum(1 for u in security_manager.users.values() if u.is_active),
            "with_mfa": sum(1 for u in security_manager.users.values() if u.mfa_enabled)
        },
        "api_keys": {
            "total": len(security_manager.api_keys),
            "active": sum(1 for k in security_manager.api_keys.values() if k.is_active),
            "expired": sum(1 for k in security_manager.api_keys.values() 
                          if k.expires_at and 
                          datetime.fromisoformat(k.expires_at) < datetime.now())
        },
        "audit": {
            "total_entries": len(security_manager.audit_log),
            "recent_24h": sum(1 for entry in security_manager.audit_log 
                           if (datetime.now() - datetime.fromisoformat(entry['timestamp'])).total_seconds() < 86400)
        },
        "config": {
            "jwt_algorithm": SECURITY_CONFIG['JWT_ALGORITHM'],
            "rate_limit_per_minute": SECURITY_CONFIG['RATE_LIMIT_PER_MINUTE'],
            "max_login_attempts": SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS'],
            "oauth_providers": {
                "github": SECURITY_CONFIG['OAUTH_GITHUB_CLIENT_ID'] is not None,
                "google": SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID'] is not None
            }
        }
    })

# ==========================================
# ENDPOINTS PÚBLICOS
# ==========================================

@auth_bp.route('/auth/providers', methods=['GET'])
def get_oauth_providers():
    """Obtiene los proveedores OAuth configurados"""
    providers = {}
    
    if SECURITY_CONFIG['OAUTH_GITHUB_CLIENT_ID']:
        providers['github'] = {
            "name": "GitHub",
            "login_url": f"{request.host_url}auth/github",
            "icon": "github"
        }
    
    if SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID']:
        providers['google'] = {
            "name": "Google",
            "login_url": f"{request.host_url}auth/google",
            "icon": "google"
        }
    
    return jsonify({
        "providers": providers,
        "total": len(providers)
    })

@auth_bp.route('/auth/health', methods=['GET'])
def auth_health():
    """Health check del servicio de autenticación"""
    return jsonify({
        "status": "healthy",
        "service": "hermes-auth",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "oauth": bool(SECURITY_CONFIG['OAUTH_GITHUB_CLIENT_ID'] or SECURITY_CONFIG['OAUTH_GOOGLE_CLIENT_ID']),
            "jwt": True,
            "api_keys": True,
            "rate_limiting": True,
            "audit_logging": True
        }
    })

if __name__ == "__main__":
    print("🔐 Endpoints de Autenticación cargados")
    print("📋 Disponibles en /auth/*")
