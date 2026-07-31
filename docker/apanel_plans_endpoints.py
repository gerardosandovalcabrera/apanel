"""
📊 Endpoints de Planes y Límites para APanel
Integración del módulo de planes con el sistema híbrido

Endpoints:
- GET /plans - Listar todos los planes
- GET /plans/current - Obtener plan actual del usuario
- GET /limits/status - Obtener estado de límites
- POST /limits/check - Verificar un límite específico
- GET /billing/usage - Obtener estadísticas de uso
- POST /billing/upgrade - Solicitar upgrade de plan
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

from apanel_plans_limits import (
    PlanTier,
    PlansManager,
    get_plans_manager
)

logger = logging.getLogger(__name__)

plans_bp = Blueprint('plans', __name__, url_prefix='/api/plans')


def get_organization_id() -> str:
    """Obtener el ID de la organización del usuario actual"""
    # En producción, esto vendría del JWT token o sesión
    return g.get('organization_id', 'default-org')


def get_current_plan_tier() -> PlanTier:
    """Obtener el tier del plan actual de la organización"""
    # En producción, esto vendría de la base de datos
    # Por defecto, usamos FREE
    return g.get('plan_tier', PlanTier.FREE)


@plans_bp.route('/', methods=['GET'])
def list_plans():
    """
    Listar todos los planes disponibles
    
    Response:
    {
        "success": true,
        "plans": [
            {
                "id": "plan-free",
                "name": "Free Tier",
                "tier": "free",
                "price_monthly": 0.0,
                "price_yearly": 0.0,
                "limits": {
                    "concurrent_agents": 3,
                    "monthly_tokens": 100000,
                    ...
                },
                "features": [...],
                "is_active": true
            },
            ...
        ]
    }
    """
    try:
        manager = get_plans_manager()
        plans = manager.get_all_plans()
        
        return jsonify({
            "success": True,
            "plans": [plan.to_dict() for plan in plans]
        })
    except Exception as e:
        logger.error(f"Error listando planes: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/current', methods=['GET'])
def get_current_plan():
    """
    Obtener el plan actual de la organización
    
    Response:
    {
        "success": true,
        "plan": {
            "id": "plan-pro",
            "name": "Pro Tier",
            "tier": "pro",
            ...
        }
    }
    """
    try:
        manager = get_plans_manager()
        current_tier = get_current_plan_tier()
        plan = manager.get_plan(current_tier)
        
        if not plan:
            return jsonify({
                "success": False,
                "error": "Plan no encontrado"
            }), 404
        
        return jsonify({
            "success": True,
            "plan": plan.to_dict()
        })
    except Exception as e:
        logger.error(f"Error obteniendo plan actual: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/limits/status', methods=['GET'])
def get_limits_status():
    """
    Obtener estado completo de límites con alertas y sugerencias
    
    Response:
    {
        "success": true,
        "status": {
            "plan_id": "plan-pro",
            "plan_name": "Pro Tier",
            "tier": "pro",
            "limits": {...},
            "usage": {
                "current_concurrent_agents": 5,
                "monthly_tokens_used": 125000,
                ...
            },
            "is_over_limit": false,
            "limits_exceeded": [],
            "warnings": ["Tokens cerca del límite mensual..."],
            "suggestions": ["Considera hacer upgrade a Team Tier..."],
            "next_billing_date": "2025-08-31T00:00:00"
        }
    }
    """
    try:
        manager = get_plans_manager()
        organization_id = get_organization_id()
        current_tier = get_current_plan_tier()
        
        # Calcular fecha de próximo billing (asumimos 30 días)
        next_billing = datetime.now() + timedelta(days=30)
        
        status = manager.get_limit_status(
            organization_id,
            current_tier,
            next_billing_date=next_billing
        )
        
        return jsonify({
            "success": True,
            "status": status.to_dict()
        })
    except Exception as e:
        logger.error(f"Error obteniendo estado de límites: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/limits/check', methods=['POST'])
def check_limit():
    """
    Verificar un límite específico antes de ejecutar una acción
    
    Request:
    {
        "limit_type": "concurrent_agents" | "monthly_tokens" | "daily_calls" | "api_rate",
        "tokens_to_add": 1000  // Opcional, para monthly_tokens
    }
    
    Response:
    {
        "success": true,
        "allowed": true,
        "message": "Agentes concurrentes: 5/20",
        "limit_type": "concurrent_agents",
        "current": 5,
        "limit": 20
    }
    """
    try:
        data = request.get_json()
        limit_type = data.get('limit_type')
        tokens_to_add = data.get('tokens_to_add', 0)
        
        if not limit_type:
            return jsonify({
                "success": False,
                "error": "limit_type es requerido"
            }), 400
        
        manager = get_plans_manager()
        organization_id = get_organization_id()
        current_tier = get_current_plan_tier()
        
        allowed = False
        message = ""
        current = 0
        limit = 0
        
        if limit_type == "concurrent_agents":
            allowed, message = manager.check_concurrent_limit(organization_id, current_tier)
            plan = manager.get_plan(current_tier)
            current = int(message.split("/")[0].split(": ")[1])
            limit = plan.limits.concurrent_agents
            
        elif limit_type == "monthly_tokens":
            allowed, message = manager.check_monthly_token_limit(
                organization_id, current_tier, tokens_to_add
            )
            plan = manager.get_plan(current_tier)
            current = int(message.split("/")[0].split(": ")[1].replace(",", ""))
            limit = plan.limits.monthly_tokens
            
        elif limit_type == "daily_calls":
            allowed, message = manager.check_daily_call_limit(organization_id, current_tier)
            plan = manager.get_plan(current_tier)
            current = int(message.split("/")[0].split(": ")[1].replace(",", ""))
            limit = plan.limits.daily_calls
            
        elif limit_type == "api_rate":
            allowed, message = manager.check_api_rate_limit(organization_id, current_tier)
            plan = manager.get_plan(current_tier)
            if allowed:
                current = int(message.split("/")[0].split(": ")[1])
                limit = plan.limits.api_calls_per_minute
            else:
                current = int(message.split("/")[0].split(": ")[1])
                limit = plan.limits.api_calls_per_minute
        else:
            return jsonify({
                "success": False,
                "error": f"limit_type no válido: {limit_type}"
            }), 400
        
        return jsonify({
            "success": True,
            "allowed": allowed,
            "message": message,
            "limit_type": limit_type,
            "current": current,
            "limit": limit
        })
        
    except Exception as e:
        logger.error(f"Error verificando límite: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/billing/usage', methods=['GET'])
def get_billing_usage():
    """
    Obtener estadísticas de uso para billing
    
    Response:
    {
        "success": true,
        "usage": {
            "current_month": "2025-07",
            "tokens_used": 125000,
            "tokens_limit": 500000,
            "tokens_percentage": 25.0,
            "calls_today": 450,
            "calls_limit": 50000,
            "calls_percentage": 0.9,
            "concurrent_agents": 5,
            "concurrent_limit": 20,
            "concurrent_percentage": 25.0,
            "estimated_monthly_cost": 49.0,
            "overage_tokens": 0,
            "overage_cost": 0.0
        }
    }
    """
    try:
        manager = get_plans_manager()
        organization_id = get_organization_id()
        current_tier = get_current_plan_tier()
        
        usage = manager.get_usage_stats(organization_id, current_tier)
        plan = manager.get_plan(current_tier)
        
        # Calcular porcentajes
        tokens_pct = (usage.monthly_tokens_used / plan.limits.monthly_tokens) * 100 if plan.limits.monthly_tokens > 0 else 0
        calls_pct = (usage.daily_calls / plan.limits.daily_calls) * 100 if plan.limits.daily_calls > 0 else 0
        concurrent_pct = (usage.current_concurrent_agents / plan.limits.concurrent_agents) * 100 if plan.limits.concurrent_agents > 0 else 0
        
        # Calcular overage (exceso)
        overage_tokens = max(0, usage.monthly_tokens_used - plan.limits.monthly_tokens)
        # Asumimos $0.00002 por token de overage
        overage_cost = overage_tokens * 0.00002
        
        current_month = datetime.now().strftime("%Y-%m")
        
        return jsonify({
            "success": True,
            "usage": {
                "current_month": current_month,
                "tokens_used": usage.monthly_tokens_used,
                "tokens_limit": plan.limits.monthly_tokens,
                "tokens_percentage": round(tokens_pct, 1),
                "calls_today": usage.daily_calls,
                "calls_limit": plan.limits.daily_calls,
                "calls_percentage": round(calls_pct, 1),
                "concurrent_agents": usage.current_concurrent_agents,
                "concurrent_limit": plan.limits.concurrent_agents,
                "concurrent_percentage": round(concurrent_pct, 1),
                "estimated_monthly_cost": plan.price_monthly or 0,
                "overage_tokens": overage_tokens,
                "overage_cost": round(overage_cost, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo uso para billing: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/billing/upgrade', methods=['POST'])
def request_upgrade():
    """
    Solicitar upgrade de plan
    
    Request:
    {
        "target_tier": "team" | "enterprise",
        "billing_cycle": "monthly" | "yearly"
    }
    
    Response:
    {
        "success": true,
        "message": "Solicitud de upgrade enviada",
        "target_plan": {
            "name": "Team Tier",
            "price_monthly": 249.0,
            "price_yearly": 2490.0
        },
        "savings": 249.0  // Si selecciona yearly
    }
    """
    try:
        data = request.get_json()
        target_tier_str = data.get('target_tier')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not target_tier_str:
            return jsonify({
                "success": False,
                "error": "target_tier es requerido"
            }), 400
        
        # Validar tier
        try:
            target_tier = PlanTier(target_tier_str)
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"Tier no válido: {target_tier_str}"
            }), 400
        
        # Obtener plan target
        manager = get_plans_manager()
        target_plan = manager.get_plan(target_tier)
        
        if not target_plan:
            return jsonify({
                "success": False,
                "error": "Plan target no encontrado"
            }), 404
        
        # Calcular ahorros si es yearly
        savings = 0.0
        if billing_cycle == "yearly" and target_plan.price_yearly:
            monthly_cost = target_plan.price_monthly or 0
            yearly_cost = target_plan.price_yearly
            savings = (monthly_cost * 12) - yearly_cost
        
        # En producción, aquí se crearía la orden en Stripe/Billing
        # Por ahora, solo simulamos
        
        return jsonify({
            "success": True,
            "message": f"Solicitud de upgrade a {target_plan.name} enviada",
            "target_plan": {
                "name": target_plan.name,
                "price_monthly": target_plan.price_monthly,
                "price_yearly": target_plan.price_yearly
            },
            "billing_cycle": billing_cycle,
            "savings": round(savings, 2) if savings > 0 else 0
        })
        
    except Exception as e:
        logger.error(f"Error solicitando upgrade: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Middleware para inyectar organización y plan en g
def inject_plan_context():
    """Inyectar contexto de plan en cada request"""
    from flask import g
    
    # En producción, esto vendría del JWT token
    # Por ahora, simulamos con valores por defecto
    g.organization_id = "demo-org"
    g.plan_tier = PlanTier.PRO  # Demo con plan Pro


# Función para registrar el blueprint en la app
def register_plans_blueprint(app):
    """Registrar el blueprint de planes en la app Flask"""
    app.register_blueprint(plans_bp)
    
    # Registrar middleware
    app.before_request(inject_plan_context)
    
    logger.info("Blueprint de planes registrado")


if __name__ == "__main__":
    # Test de los endpoints
    from flask import Flask
    app = Flask(__name__)
    register_plans_blueprint(app)
    
    with app.test_client() as client:
        print("\n🧪 Test de Endpoints de Planes:")
        
        # Test listar planes
        print("\n1. Listar planes:")
        response = client.get('/api/plans/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Planes: {len(data['plans'])}")
        
        # Test plan actual
        print("\n2. Plan actual:")
        response = client.get('/api/plans/current')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Plan: {data['plan']['name']}")
        
        # Test estado de límites
        print("\n3. Estado de límites:")
        response = client.get('/api/plans/limits/status')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            status = data['status']
            print(f"   Sobre límite: {status['is_over_limit']}")
            print(f"   Alertas: {len(status['warnings'])}")
            print(f"   Sugerencias: {len(status['suggestions'])}")
        
        # Test verificar límite
        print("\n4. Verificar límite de concurrencia:")
        response = client.post('/api/plans/limits/check', 
                              json={"limit_type": "concurrent_agents"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Permitido: {data['allowed']}")
            print(f"   Mensaje: {data['message']}")
        
        # Test usage
        print("\n5. Estadísticas de uso:")
        response = client.get('/api/plans/billing/usage')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            usage = data['usage']
            print(f"   Tokens: {usage['tokens_used']:,}/{usage['tokens_limit']:,} ({usage['tokens_percentage']}%)")
            print(f"   Llamadas hoy: {usage['calls_today']:,}/{usage['calls_limit']:,}")
