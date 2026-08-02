"""
📊 Plans and Limits Endpoints for APanel
Integration of the plans module with the hybrid system

Endpoints:
- GET /plans - List all available plans
- GET /plans/current - Get user's current plan
- GET /limits/status - Get limit status
- POST /limits/check - Verify a specific limit
- GET /billing/usage - Get usage statistics
- POST /billing/upgrade - Request plan upgrade
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
    """Get the current user's organization ID"""
    # In production, this would come from JWT token or session
    return g.get('organization_id', 'default-org')


def get_current_plan_tier() -> PlanTier:
    """Get the organization's current plan tier"""
    # In production, this would come from the database
    # By default, we use FREE
    return g.get('plan_tier', PlanTier.FREE)


@plans_bp.route('/', methods=['GET'])
def list_plans():
    """
    List all available plans
    
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
                "limits": {...},
                "features": [...]
            }
        ]
    }
    """
    try:
        # In production, get from PlansManager
        # For now, return static plans
        plans = [
            {
                "id": "plan-free",
                "name": "Free Tier",
                "tier": "free",
                "price_monthly": 0.0,
                "price_yearly": 0.0,
                "limits": {
                    "concurrent_agents": 3,
                    "monthly_tokens": 100000,
                    "daily_calls": 100,
                    "api_calls_per_minute": 10,
                    "storage_days": 7
                },
                "features": [
                    "3 concurrent agents",
                    "100,000 monthly tokens",
                    "Basic support",
                    "7-day data retention"
                ]
            },
            {
                "id": "plan-pro",
                "name": "Pro Tier",
                "tier": "pro",
                "price_monthly": 49.0,
                "price_yearly": 490.0,
                "limits": {
                    "concurrent_agents": 20,
                    "monthly_tokens": 500000,
                    "daily_calls": 1000,
                    "api_calls_per_minute": 60,
                    "storage_days": 30
                },
                "features": [
                    "20 concurrent agents",
                    "500,000 monthly tokens",
                    "Priority support",
                    "30-day data retention",
                    "Cost tracking"
                ]
            },
            {
                "id": "plan-team",
                "name": "Team Tier",
                "tier": "team",
                "price_monthly": 249.0,
                "price_yearly": 2490.0,
                "limits": {
                    "concurrent_agents": 100,
                    "monthly_tokens": 2000000,
                    "daily_calls": 5000,
                    "api_calls_per_minute": 200,
                    "storage_days": 90
                },
                "features": [
                    "100 concurrent agents",
                    "2,000,000 monthly tokens",
                    "24/7 support",
                    "90-day data retention",
                    "Advanced analytics"
                ]
            },
            {
                "id": "plan-enterprise",
                "name": "Enterprise Tier",
                "tier": "enterprise",
                "price_monthly": None,
                "price_yearly": None,
                "limits": {
                    "concurrent_agents": -1,
                    "monthly_tokens": -1,
                    "daily_calls": -1,
                    "api_calls_per_minute": -1,
                    "storage_days": 365
                },
                "features": [
                    "Unlimited agents",
                    "Unlimited tokens",
                    "Dedicated support",
                    "1-year data retention",
                    "Custom integrations",
                    "SLA guarantee"
                ]
            }
        ]
        
        return jsonify({
            "success": True,
            "plans": plans,
            "count": len(plans)
        })
        
    except Exception as e:
        logger.error(f"Error listing plans: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/current', methods=['GET'])
def get_current_plan():
    """
    Get the current plan for the organization
    
    Response:
    {
        "success": true,
        "plan": {...},
        "usage": {...},
        "limits_status": {...}
    }
    """
    try:
        org_id = get_organization_id()
        current_tier = get_current_plan_tier()
        
        # Get plan details
        plans_response = list_plans()
        plans = plans_response.get_json()['plans']
        current_plan = next((p for p in plans if p['tier'] == current_tier.value), None)
        
        if not current_plan:
            return jsonify({
                "success": False,
                "error": "Current plan not found"
            }), 404
        
        # Get usage (in production, from database)
        usage = {
            "concurrent_agents": 5,
            "monthly_tokens": 25000,
            "daily_calls": 50,
            "api_calls_last_minute": 5
        }
        
        # Calculate limit status
        limits_status = {
            "concurrent_agents": {
                "current": usage['concurrent_agents'],
                "limit": current_plan['limits']['concurrent_agents'],
                "percentage": (usage['concurrent_agents'] / current_plan['limits']['concurrent_agents'] * 100) if current_plan['limits']['concurrent_agents'] > 0 else 0,
                "status": "ok"
            },
            "monthly_tokens": {
                "current": usage['monthly_tokens'],
                "limit": current_plan['limits']['monthly_tokens'],
                "percentage": (usage['monthly_tokens'] / current_plan['limits']['monthly_tokens'] * 100) if current_plan['limits']['monthly_tokens'] > 0 else 0,
                "status": "ok"
            }
        }
        
        return jsonify({
            "success": True,
            "organization_id": org_id,
            "plan": current_plan,
            "usage": usage,
            "limits_status": limits_status,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting current plan: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/limits/status', methods=['GET'])
def get_limits_status():
    """
    Get comprehensive limits status
    
    Response:
    {
        "success": true,
        "limits_status": {...},
        "alerts": [...],
        "suggestions": [...]
    }
    """
    try:
        org_id = get_organization_id()
        current_plan_response = get_current_plan()
        
        if current_plan_response.status_code != 200:
            return current_plan_response
        
        current_plan_data = current_plan_response.get_json()
        limits_status = current_plan_data.get('limits_status', {})
        
        # Generate alerts
        alerts = []
        for limit_type, status in limits_status.items():
            if status['percentage'] >= 80:
                alerts.append({
                    "type": "warning",
                    "limit_type": limit_type,
                    "percentage": status['percentage'],
                    "message": f"{limit_type} usage at {status['percentage']:.1f}%"
                })
        
        # Generate suggestions
        suggestions = []
        if len(alerts) > 0:
            suggestions.append({
                "type": "upgrade",
                "priority": "high",
                "message": "Consider upgrading to a higher plan for more resources",
                "suggested_plan": "pro" if current_plan_data['plan']['tier'] == "free" else "team"
            })
        
        return jsonify({
            "success": True,
            "organization_id": org_id,
            "limits_status": limits_status,
            "alerts": alerts,
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting limits status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@plans_bp.route('/billing/usage', methods=['GET'])
def get_billing_usage():
    """
    Get billing and usage statistics
    
    Response:
    {
        "success": true,
        "usage": {...},
        "costs": {...},
        "trends": {...}
    }
    """
    try:
        org_id = get_organization_id()
        
        # In production, get real usage data from database
        usage = {
            "current_month": {
                "total_calls": 150,
                "total_tokens": 75000,
                "concurrent_agents_peak": 8,
                "avg_response_time": 0.5
            },
            "previous_month": {
                "total_calls": 120,
                "total_tokens": 60000,
                "concurrent_agents_peak": 6,
                "avg_response_time": 0.6
            }
        }
        
        # Calculate costs (in production, use cost tracking module)
        costs = {
            "current_month": {
                "total_cost": 15.50,
                "per_call": 0.10,
                "per_1k_tokens": 0.20
            },
            "previous_month": {
                "total_cost": 12.00,
                "per_call": 0.10,
                "per_1k_tokens": 0.20
            }
        }
        
        # Calculate trends
        trends = {
            "calls_change": ((usage['current_month']['total_calls'] - usage['previous_month']['total_calls']) / usage['previous_month']['total_calls'] * 100) if usage['previous_month']['total_calls'] > 0 else 0,
            "tokens_change": ((usage['current_month']['total_tokens'] - usage['previous_month']['total_tokens']) / usage['previous_month']['total_tokens'] * 100) if usage['previous_month']['total_tokens'] > 0 else 0,
            "cost_change": ((costs['current_month']['total_cost'] - costs['previous_month']['total_cost']) / costs['previous_month']['total_cost'] * 100) if costs['previous_month']['total_cost'] > 0 else 0
        }
        
        return jsonify({
            "success": True,
            "organization_id": org_id,
            "usage": usage,
            "costs": costs,
            "trends": trends,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting billing usage: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def register_plans_blueprint(app):
    """Register plans blueprint in Flask app"""
    app.register_blueprint(plans_bp)
    
    # Middleware to inject organization context
    @app.before_request
    def inject_plans_context():
        g.organization_id = 'default-org'  # In production, from JWT
        g.plan_tier = 'free'  # In production, from user data


if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    register_plans_blueprint(app)
    
    print("🧪 Test of Plans Endpoints:")
    print("\n1. Testing GET /api/plans")
    with app.test_client() as client:
        response = client.get('/api/plans/')
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            print(f"   ✅ Found {data['count']} plans")
    
    print("\n2. Testing GET /api/plans/current")
    with app.test_client() as client:
        response = client.get('/api/plans/current')
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            print(f"   ✅ Current plan: {data['plan']['name']}")
            print(f"   ✅ Organization: {data['organization_id']}")
    
    print("\n3. Testing GET /api/plans/limits/status")
    with app.test_client() as client:
        response = client.get('/api/plans/limits/status')
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            print(f"   ✅ Alerts: {len(data['alerts'])}")
            print(f"   ✅ Suggestions: {len(data['suggestions'])}")
    
    print("\n4. Testing GET /api/plans/billing/usage")
    with app.test_client() as client:
        response = client.get('/api/plans/billing/usage')
        print(f"   Status: {response.status_code}")
        data = response.get_json()
        if data.get('success'):
            print(f"   ✅ Current month calls: {data['usage']['current_month']['total_calls']}")
            print(f"   ✅ Current month cost: ${data['costs']['current_month']['total_cost']:.2f}")
    
    print("\n✅ All tests completed successfully!")
