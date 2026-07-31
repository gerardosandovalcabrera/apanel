"""
🔌 Billing API Endpoints - APanel
API REST para el sistema de billing integrado
"""

from flask import Blueprint, request, jsonify, g
from decimal import Decimal
from datetime import datetime

billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')

# Importar el sistema de billing (en producción, desde un módulo real)
# Por ahora usamos el demo
from demo_billing_simple import BillingIntegrationDemo

# Singleton instance
_billing_instance = None

def get_billing_system():
    """Obtener instancia del sistema de billing"""
    global _billing_instance
    if _billing_instance is None:
        _billing_instance = BillingIntegrationDemo()
    return _billing_instance


@billing_bp.route('/summary', methods=['GET'])
def get_billing_summary():
    """
    Obtener resumen completo de billing
    
    Response:
    {
        "cost_summary": {...},
        "budget_status": {...},
        "alerts": [...],
        "optimizations": [...],
        "generated_at": "2025-07-31T12:00:00"
    }
    """
    try:
        billing = get_billing_system()
        
        # En producción, organization_id vendría del JWT token
        organization_id = g.get('organization_id', 'demo-org-billing')
        
        summary = billing.get_billing_summary(organization_id)
        
        return jsonify({
            "success": True,
            "data": summary
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@billing_bp.route('/record-call', methods=['POST'])
def record_api_call():
    """
    Registrar una llamada a la API
    
    Request:
    {
        "provider_model_id": "openai/gpt-4o",
        "prompt_tokens": 1000,
        "completion_tokens": 500
    }
    
    Response:
    {
        "success": true,
        "cost": 0.0125,
        "tokens": 1500,
        "within_limits": true
    }
    """
    try:
        data = request.get_json()
        
        provider_model_id = data.get('provider_model_id')
        prompt_tokens = data.get('prompt_tokens', 0)
        completion_tokens = data.get('completion_tokens', 0)
        
        if not provider_model_id:
            return jsonify({
                "success": False,
                "error": "provider_model_id es requerido"
            }), 400
        
        billing = get_billing_system()
        organization_id = g.get('organization_id', 'demo-org-billing')
        
        call_record = billing.record_api_call(
            organization_id=organization_id,
            provider_model_id=provider_model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        return jsonify({
            "success": True,
            "cost": float(call_record['cost']),
            "tokens": call_record['tokens'],
            "provider_model_id": call_record['provider_model_id'],
            "within_limits": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@billing_bp.route('/create-budget', methods=['POST'])
def create_budget():
    """
    Crear un presupuesto
    
    Request:
    {
        "name": "Monthly Budget",
        "monthly_budget": 100.00,
        "alert_thresholds": [0.5, 0.8, 1.0]
    }
    """
    try:
        data = request.get_json()
        
        name = data.get('name')
        monthly_budget = data.get('monthly_budget')
        alert_thresholds = data.get('alert_thresholds', [0.5, 0.8, 1.0])
        
        if not name or monthly_budget is None:
            return jsonify({
                "success": False,
                "error": "name y monthly_budget son requeridos"
            }), 400
        
        billing = get_billing_system()
        organization_id = g.get('organization_id', 'demo-org-billing')
        
        billing.create_budget(
            organization_id=organization_id,
            name=name,
            monthly_budget=Decimal(str(monthly_budget))
        )
        
        return jsonify({
            "success": True,
            "message": f"Presupuesto '{name}' creado exitosamente"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@billing_bp.route('/cost-estimate', methods=['POST'])
def estimate_cost():
    """
    Estimar costo antes de hacer una llamada
    
    Request:
    {
        "provider_model_id": "openai/gpt-4o",
        "prompt_tokens": 1000,
        "completion_tokens": 500
    }
    
    Response:
    {
        "success": true,
        "estimated_cost": 0.0125,
        "cost_breakdown": {...}
    }
    """
    try:
        from apanel_cost_tracking import ModelUsage, get_calculator
        
        data = request.get_json()
        
        provider_model_id = data.get('provider_model_id')
        prompt_tokens = data.get('prompt_tokens', 0)
        completion_tokens = data.get('completion_tokens', 0)
        
        if not provider_model_id:
            return jsonify({
                "success": False,
                "error": "provider_model_id es requerido"
            }), 400
        
        calculator = get_calculator()
        
        usage = ModelUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        cost_breakdown = calculator.calculate_cost(provider_model_id, usage)
        
        if not cost_breakdown:
            return jsonify({
                "success": False,
                "error": "Modelo no encontrado"
            }), 404
        
        return jsonify({
            "success": True,
            "estimated_cost": float(cost_breakdown.total_cost),
            "cost_breakdown": cost_breakdown.to_dict()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def register_billing_blueprint(app):
    """Registrar el blueprint de billing en la app Flask"""
    app.register_blueprint(billing_bp)
    
    # Middleware para inyectar organization_id
    @app.before_request
    def inject_org_id():
        g.organization_id = 'demo-org-billing'  # En producción, del JWT


if __name__ == "__main__":
    # Test de los endpoints
    from flask import Flask
    app = Flask(__name__)
    register_billing_blueprint(app)
    
    with app.test_client() as client:
        print("🧪 Test de Billing API:")
        
        # Test 1: Crear presupuesto
        print("\n1. Creando presupuesto...")
        response = client.post('/api/billing/create-budget', json={
            "name": "Test Budget",
            "monthly_budget": 100.00
        })
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            print(f"   ✅ {data['message']}")
        
        # Test 2: Estimar costo
        print("\n2. Estimando costo...")
        response = client.post('/api/billing/cost-estimate', json={
            "provider_model_id": "openai/gpt-4o",
            "prompt_tokens": 1000,
            "completion_tokens": 500
        })
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            print(f"   ✅ Costo estimado: ${data['estimated_cost']:.6f}")
        
        # Test 3: Registrar llamada
        print("\n3. Registrando llamada...")
        response = client.post('/api/billing/record-call', json={
            "provider_model_id": "openai/gpt-4o",
            "prompt_tokens": 1000,
            "completion_tokens": 500
        })
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            print(f"   ✅ Costo: ${data['cost']:.6f}, Tokens: {data['tokens']}")
        
        # Test 4: Obtener resumen
        print("\n4. Obteniendo resumen de billing...")
        response = client.get('/api/billing/summary')
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            summary = data['data']
            cost_summary = summary['cost_summary']
            print(f"   ✅ Costo total: ${cost_summary['total_cost']:.6f}")
            print(f"   ✅ Tokens: {cost_summary['total_tokens']:,}")
            print(f"   ✅ Llamadas: {cost_summary['calls_count']}")
            
            if summary['budget_status']:
                budget = summary['budget_status']
                print(f"   💵 Presupuesto: ${budget['current_spent']:.2f} / ${budget['monthly_budget']:.2f}")
                print(f"   💵 Porcentaje: {budget['percentage_used']:.1f}%")
        
        print("\n✅ Tests completados exitosamente!")
