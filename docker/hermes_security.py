"""
Sistema de Seguridad para Hermes Multi-Agent Management
Implementación completa de autenticación y autorización

Arquitectura de Seguridad:
- OAuth2 para humanos (GitHub/Google)
- JWT con API Keys para agentes
- Múltiples capas de defensa
- Auditoría completa
"""

import os
import json
import time
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from functools import wraps
import jwt
import bcrypt
from flask import request, jsonify, g
import redis

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HermesSecurity')

# Configuración de seguridad
SECURITY_CONFIG = {
    # JWT Configuration
    "JWT_SECRET_KEY": os.getenv('JWT_SECRET_KEY', secrets.token_hex(32)),
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_EXPIRES": 3600,  # 1 hora
    "JWT_REFRESH_TOKEN_EXPIRES": 2592000,  # 30 días
    
    # API Keys
    "API_KEY_LENGTH": 64,
    "API_KEY_PREFIX": "hermes_",
    
    # Rate Limiting
    "RATE_LIMIT_PER_MINUTE": 60,
    "RATE_LIMIT_PER_HOUR": 1000,
    
    # OAuth Providers
    "OAUTH_GITHUB_CLIENT_ID": os.getenv('OAUTH_GITHUB_CLIENT_ID'),
    "OAUTH_GITHUB_CLIENT_SECRET": os.getenv('OAUTH_GITHUB_CLIENT_SECRET'),
    "OAUTH_GOOGLE_CLIENT_ID": os.getenv('OAUTH_GOOGLE_CLIENT_ID'),
    "OAUTH_GOOGLE_CLIENT_SECRET": os.getenv('OAUTH_GOOGLE_CLIENT_SECRET'),
    
    # Security
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOCKOUT_TIME": 900,  # 15 minutos
    "SESSION_TIMEOUT": 3600,  # 1 hora
    
    # Encryption
    "ENCRYPTION_KEY": os.getenv('ENCRYPTION_KEY', secrets.token_hex(32)).encode(),
}

# Redis para rate limiting y sesiones
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

@dataclass
class User:
    """Usuario del sistema (humanos)."""
    id: str
    username: str
    email: str
    role: str  # admin, operator, viewer
    provider: str  # github, google, local
    provider_id: str
    created_at: str
    last_login: Optional[str] = None
    mfa_enabled: bool = False
    is_active: bool = True
    
    def to_dict(self):
        return asdict(self)

@dataclass
class APIKey:
    """API Key para agentes y scripts."""
    id: str
    key: str
    name: str
    owner: str  # User ID
    permissions: List[str]  # read, write, admin
    created_at: str
    expires_at: Optional[str] = None
    last_used: Optional[str] = None
    is_active: bool = True
    rate_limit: int = 60  # por minuto
    
    def to_dict(self):
        data = asdict(self)
        data['key'] = f"{SECURITY_CONFIG['API_KEY_PREFIX']}{data['key'][:8]}..."  # Solo mostrar prefix
        return data

class SecurityManager:
    """Gestor de seguridad del sistema."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.login_attempts: Dict[str, List[datetime]] = {}
        self.audit_log: List[Dict] = []
        
        # Cargar usuarios y keys desde Redis
        self._load_from_redis()
        
        # Crear usuario admin por defecto si no existe
        if not self.users:
            self._create_default_admin()
    
    def _load_from_redis(self):
        """Carga usuarios y API keys desde Redis."""
        try:
            # Cargar usuarios
            users_data = redis_client.hgetall("hermes:users")
            for user_id, user_json in users_data.items():
                user = User(**json.loads(user_json))
                self.users[user_id] = user
            
            # Cargar API keys
            keys_data = redis_client.hgetall("hermes:api_keys")
            for key_id, key_json in keys_data.items():
                key = APIKey(**json.loads(key_json))
                self.api_keys[key_id] = key
                
            logger.info(f"Loaded {len(self.users)} users and {len(self.api_keys)} API keys from Redis")
            
        except Exception as e:
            logger.warning(f"Could not load from Redis: {e}")
    
    def _save_to_redis(self):
        """Guarda usuarios y API keys en Redis."""
        try:
            # Guardar usuarios
            for user_id, user in self.users.items():
                redis_client.hset("hermes:users", user_id, json.dumps(user.to_dict()))
            
            # Guardar API keys
            for key_id, key in self.api_keys.items():
                redis_client.hset("hermes:api_keys", key_id, json.dumps(key.to_dict()))
                
        except Exception as e:
            logger.error(f"Could not save to Redis: {e}")
    
    def _create_default_admin(self):
        """Crea usuario admin por defecto."""
        admin_user = User(
            id="admin_default",
            username="admin",
            email="admin@hermes.local",
            role="admin",
            provider="local",
            provider_id="default",
            created_at=datetime.now().isoformat(),
            mfa_enabled=False,
            is_active=True
        )
        self.users[admin_user.id] = admin_user
        self._save_to_redis()
        
        logger.warning("Default admin user created. Please change password and enable MFA!")
    
    def _log_audit(self, event: str, user_id: str, details: Dict, ip: str):
        """Registra evento en el log de auditoría."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "user_id": user_id,
            "ip": ip,
            "details": details
        }
        
        self.audit_log.append(audit_entry)
        
        # Guardar en Redis
        redis_client.lpush("hermes:audit_log", json.dumps(audit_entry))
        redis_client.ltrim("hermes:audit_log", 0, 9999)  # Mantener últimos 10,000
        
        logger.info(f"AUDIT: {event} by {user_id} from {ip}")
    
    def generate_jwt_token(self, user_id: str, expires_in: int = None) -> tuple:
        """Genera token JWT (access y refresh)."""
        if expires_in is None:
            expires_in = SECURITY_CONFIG['JWT_ACCESS_TOKEN_EXPIRES']
        
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Access token
        access_payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "provider": user.provider,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        access_token = jwt.encode(
            access_payload,
            SECURITY_CONFIG['JWT_SECRET_KEY'],
            algorithm=SECURITY_CONFIG['JWT_ALGORITHM']
        )
        
        # Refresh token
        refresh_payload = {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(seconds=SECURITY_CONFIG['JWT_REFRESH_TOKEN_EXPIRES']),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            SECURITY_CONFIG['JWT_SECRET_KEY'],
            algorithm=SECURITY_CONFIG['JWT_ALGORITHM']
        )
        
        # Guardar refresh token en Redis
        redis_client.setex(
            f"refresh_token:{user_id}",
            SECURITY_CONFIG['JWT_REFRESH_TOKEN_EXPIRES'],
            refresh_token
        )
        
        self._log_audit("jwt_generated", user.id, {"expires_in": expires_in}, request.remote_addr)
        
        return access_token, refresh_token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verifica y decodifica token JWT."""
        try:
            payload = jwt.decode(
                token,
                SECURITY_CONFIG['JWT_SECRET_KEY'],
                algorithms=[SECURITY_CONFIG['JWT_ALGORITHM']]
            )
            
            # Verificar que el usuario existe y está activo
            user = self.users.get(payload.get('user_id'))
            if not user or not user.is_active:
                return None
            
            # Verificar que no esté revocado (en Redis)
            if redis_client.get(f"revoked_token:{token}"):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def refresh_jwt_token(self, refresh_token: str) -> Optional[str]:
        """Refresca un access token usando un refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                SECURITY_CONFIG['JWT_SECRET_KEY'],
                algorithms=[SECURITY_CONFIG['JWT_ALGORITHM']]
            )
            
            if payload.get('type') != 'refresh':
                return None
            
            user_id = payload.get('user_id')
            
            # Verificar que el refresh token es válido (en Redis)
            stored_token = redis_client.get(f"refresh_token:{user_id}")
            if stored_token != refresh_token:
                return None
            
            # Generar nuevo access token
            access_token, _ = self.generate_jwt_token(user_id)
            
            self._log_audit("jwt_refreshed", user_id, {}, request.remote_addr)
            
            return access_token
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def revoke_token(self, token: str):
        """Revoca un token JWT."""
        # Añadir a lista de revocados en Redis
        redis_client.setex(
            f"revoked_token:{token}",
            SECURITY_CONFIG['JWT_ACCESS_TOKEN_EXPIRES'],
            "1"
        )
        
        payload = self.verify_jwt_token(token)
        if payload:
            self._log_audit("token_revoked", payload.get('user_id'), {}, request.remote_addr)
    
    def create_api_key(self, user_id: str, name: str, permissions: List[str], expires_in_days: int = None) -> str:
        """Crea una nueva API key."""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Generar API key
        key = secrets.token_urlsafe(SECURITY_CONFIG['API_KEY_LENGTH'])
        key_id = secrets.token_hex(8)
        
        # Calcular expiración
        expires_at = None
        if expires_in_days:
            expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
        
        api_key = APIKey(
            id=key_id,
            key=key,
            name=name,
            owner=user_id,
            permissions=permissions,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            rate_limit=SECURITY_CONFIG['RATE_LIMIT_PER_MINUTE']
        )
        
        self.api_keys[key_id] = api_key
        self._save_to_redis()
        
        self._log_audit("api_key_created", user_id, {"name": name, "permissions": permissions}, request.remote_addr)
        
        return f"{SECURITY_CONFIG['API_KEY_PREFIX']}{key}"
    
    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verifica una API key."""
        # Remover prefix
        if api_key.startswith(SECURITY_CONFIG['API_KEY_PREFIX']):
            api_key = api_key[len(SECURITY_CONFIG['API_KEY_PREFIX']):]
        
        # Buscar la key
        for key_obj in self.api_keys.values():
            if key_obj.key == api_key and key_obj.is_active:
                # Verificar expiración
                if key_obj.expires_at and datetime.fromisoformat(key_obj.expires_at) < datetime.now():
                    return None
                
                # Actualizar last_used
                key_obj.last_used = datetime.now().isoformat()
                self._save_to_redis()
                
                return key_obj
        
        return None
    
    def check_rate_limit(self, identifier: str, limit: int = None, window: int = 60) -> bool:
        """Verifica rate limiting."""
        if limit is None:
            limit = SECURITY_CONFIG['RATE_LIMIT_PER_MINUTE']
        
        key = f"rate_limit:{identifier}"
        
        # Contar requests en la ventana
        current = redis_client.incr(key)
        
        if current == 1:
            redis_client.expire(key, window)
        
        if current > limit:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        return True
    
    def check_login_attempts(self, identifier: str) -> bool:
        """Verifica si el usuario ha excedido intentos de login."""
        now = datetime.now()
        
        # Limpiar intentos viejos
        if identifier in self.login_attempts:
            self.login_attempts[identifier] = [
                attempt for attempt in self.login_attempts[identifier]
                if (now - attempt).total_seconds() < SECURITY_CONFIG['LOCKOUT_TIME']
            ]
        
        # Verificar si está bloqueado
        if len(self.login_attempts.get(identifier, [])) >= SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS']:
            return False
        
        return True
    
    def record_login_attempt(self, identifier: str, success: bool):
        """Registra un intento de login."""
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        if not success:
            self.login_attempts[identifier].append(datetime.now())
        else:
            # Reset en éxito
            self.login_attempts[identifier] = []
    
    def create_oauth_user(self, provider: str, provider_user_data: Dict) -> User:
        """Crea o actualiza usuario desde OAuth."""
        provider_id = str(provider_user_data['id'])
        email = provider_user_data.get('email')
        username = provider_user_data.get('login') or provider_user_data.get('name')
        
        # Buscar usuario existente
        for user in self.users.values():
            if user.provider == provider and user.provider_id == provider_id:
                # Actualizar usuario
                user.email = email or user.email
                user.last_login = datetime.now().isoformat()
                self._save_to_redis()
                return user
        
        # Crear nuevo usuario
        new_user = User(
            id=secrets.token_hex(16),
            username=username,
            email=email,
            role="operator",  # Rol por defecto
            provider=provider,
            provider_id=provider_id,
            created_at=datetime.now().isoformat(),
            last_login=datetime.now().isoformat(),
            mfa_enabled=False,
            is_active=True
        )
        
        self.users[new_user.id] = new_user
        self._save_to_redis()
        
        self._log_audit("oauth_user_created", new_user.id, {"provider": provider}, request.remote_addr)
        
        return new_user
    
    def get_audit_log(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Obtiene log de auditoría."""
        if user_id:
            return [entry for entry in self.audit_log if entry['user_id'] == user_id][-limit:]
        return self.audit_log[-limit:]

# Instancia global del gestor de seguridad
security_manager = SecurityManager()

# Decoradores para protección de rutas
def require_auth(f):
    """Decorador para requerir autenticación JWT."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        payload = security_manager.verify_jwt_token(token)
        
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        g.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function

def require_api_key(f):
    """Decorador para requerir API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({"error": "Missing API key"}), 401
        
        key_obj = security_manager.verify_api_key(api_key)
        
        if not key_obj:
            return jsonify({"error": "Invalid or expired API key"}), 401
        
        # Verificar rate limit
        if not security_manager.check_rate_limit(f"api_key:{key_obj.id}", key_obj.rate_limit):
            return jsonify({"error": "Rate limit exceeded"}), 429
        
        g.current_api_key = key_obj
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(*allowed_roles):
    """Decorador para requerir roles específicos."""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_role = g.current_user.get('role')
            
            if user_role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_permission(*required_permissions):
    """Decorador para requerir permisos específicos."""
    def decorator(f):
        @wraps(f)
        @require_api_key
        def decorated_function(*args, **kwargs):
            key_permissions = g.current_api_key.permissions
            
            for perm in required_permissions:
                if perm not in key_permissions:
                    return jsonify({"error": f"Missing permission: {perm}"}, 403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

if __name__ == "__main__":
    # Pruebas del sistema de seguridad
    print("🔐 Sistema de Seguridad Iniciado")
    print(f"👥 Usuarios cargados: {len(security_manager.users)}")
    print(f"🔑 API Keys cargadas: {len(security_manager.api_keys)}")
    print(f"📝 Logs de auditoría: {len(security_manager.audit_log)}")
