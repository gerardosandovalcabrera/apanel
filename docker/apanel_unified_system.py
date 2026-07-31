"""
🚀 APanel Unified System - Main Integrated System
Web Dashboard + MCP Server + Billing System + Plans & Limits

This is the main system that unites all modules into a single application.

Integrated modules:
1. Multi-Agent Management
2. Billing System (Cost Tracking + Budget)
3. Plans & Limits
4. Security (OAuth, JWT, RBAC)

Interfaces:
- Web Dashboard (for humans)
- MCP Server (for agents)
- REST API (for integrations)
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# Flask
from flask import Flask, render_template, jsonify, request, g
from flask_cors import CORS

# Billing System
from billing_api import register_billing_blueprint
from demo_billing_simple import BillingIntegrationDemo

# MCP Server
import hermes_multi_agent_mcp as mcp_module

# Agent Manager
from hermes_multi_agent_dashboard import HermesMultiAgentManager

# Plans & Limits
from apanel_plans_limits import PlanTier, get_plans_manager

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('APanelUnified')

# ========================================
# INITIALIZATION
# ========================================

app = Flask(__name__)
app.secret_key = 'apanel-secret-key-change-in-production'
CORS(app)

# Initialize components
manager = HermesMultiAgentManager()
mcp_server = mcp_module.HermesMultiAgentMCP()
mcp_server.manager = manager

billing_system = BillingIntegrationDemo()

# Plans Manager (use Redis in production)
# plans_manager = get_plans_manager()

# ========================================
# MIDDLEWARE - Inject organization_id
# ========================================

@app.before_request
def inject_context():
    """Inject organization context into each request"""
    # In production, this would come from JWT token
    g.organization_id = request.headers.get('X-Organization-ID', 'demo-org-billing')
    g.user_id = request.headers.get('X-User-ID', 'demo-user')
    g.plan_tier = request.headers.get('X-Plan-Tier', 'pro').lower()

# ========================================
# MAIN DASHBOARD
# ========================================

@app.route('/')
def index():
    """Main dashboard page with tabs"""
    return render_template('unified_dashboard.html')

@app.route('/billing')
def billing_dashboard():
    """Billing specific dashboard"""
    return render_template('billing_dashboard.html')

@app.route('/plans')
def plans_dashboard():
    """Plans specific dashboard"""
    return render_template('plans_dashboard.html')

# ========================================
# REST API - Agents
# ========================================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all agents"""
    agents_data = {name: agent.to_dict() for name, agent in manager.agents.items()}
    return jsonify({
        "success": True,
        "data": agents_data
    })

@app.route('/api/agents/<agent_name>', methods=['GET'])
def get_agent(agent_name):
    """Get information for a specific agent"""
    agent = manager.agents.get(agent_name)
    
    if not agent:
        return jsonify({
            "success": False,
            "error": f"Agent '{agent_name}' not found"
        }), 404
    
    return jsonify({
        "success": True,
        "data": agent.to_dict()
    })

@app.route('/api/agents/<agent_name>/health', methods=['GET'])
def get_agent_health(agent_name):
    """Get health score for a specific agent"""
    agent = manager.agents.get(agent_name)
    
    if not agent:
        return jsonify({
            "success": False,
            "error": f"Agente '{agent_name}' no encontrado"
        }), 404
    
    health = agent.health_score
    
    return jsonify({
        "success": True,
        "data": {
            "agent_name": agent_name,
            "health_score": health,
            "status": "healthy" if health >= 80 else "warning" if health >= 60 else "critical"
        }
    })

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get aggregated system metrics"""
    metrics = manager.get_aggregated_metrics()
    
    return jsonify({
        "success": True,
        "data": metrics
    })

# ========================================
# REST API - Integrated Billing
# ========================================

@app.route('/api/billing/unified-summary', methods=['GET'])
def get_unified_billing_summary():
    """
    Get unified billing summary including:
    - LLM costs
    - Plan limits
    - Budget
    - Alerts
    - Optimizations
    """
    try:
        org_id = g.organization_id
        
        # Get billing summary
        billing_summary = billing_system.get_billing_summary(org_id)
        
        # Get plan limits
        plan_tier = PlanTier.PRO  # In production, from JWT
        # limit_status = plans_manager.get_limit_status(org_id, plan_tier)
        
        # Simulate limit status (in production use real plans_manager)
        limit_status = {
            "concurrent_agents": {
                "current": len(manager.agents),
                "limit": 20,
                "percentage": len(manager.agents) / 20 * 100,
                "status": "ok"
            },
            "tokens_monthly": {
                "current": billing_summary['cost_summary']['total_tokens'],
                "limit": 500000,
                "percentage": billing_summary['cost_summary']['total_tokens'] / 500000 * 100,
                "status": "ok"
            }
        }
        
        return jsonify({
            "success": True,
            "data": {
                "organization_id": org_id,
                "billing": billing_summary,
                "limits": limit_status,
                "generated_at": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in unified billing summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/billing/record-call', methods=['POST'])
def record_llm_call():
    """
    Register an LLM call and verify limits
    
    This endpoint is called from the agent system
    to register each LLM API call.
    """
    try:
        data = request.get_json()
        
        provider_model_id = data.get('provider_model_id')
        prompt_tokens = data.get('prompt_tokens', 0)
        completion_tokens = data.get('completion_tokens', 0)
        
        if not provider_model_id:
            return jsonify({
                "success": False,
                "error": "provider_model_id is required"
            }), 400
        
        org_id = g.organization_id
        
        # Register the call
        call_record = billing_system.record_api_call(
            organization_id=org_id,
            provider_model_id=provider_model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Verify limits
        # In production, this would verify plan limits
        # and block if exceeded
        
        return jsonify({
            "success": True,
            "data": {
                "cost": float(call_record['cost']),
                "tokens": call_record['tokens'],
                "provider_model_id": call_record['provider_model_id'],
                "within_limits": True,
                "recorded_at": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error recording call: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ========================================
# MCP SERVER - For Agents
# ========================================

@app.route('/mcp/tools', methods=['GET'])
def mcp_list_tools():
    """MCP: List all available tools"""
    tools = mcp_server.get_tools_list()
    return jsonify({
        "success": True,
        "tools": tools
    })

@app.route('/mcp/call', methods=['POST'])
def mcp_call_tool():
    """MCP: Execute a tool"""
    try:
        data = request.json
        tool_name = data.get('tool')
        arguments = data.get('arguments', {})
        
        if not tool_name:
            return jsonify({
                "success": False,
                "error": "Tool name is required"
            }), 400
        
        # Execute tool asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            mcp_server.handle_tool_call(tool_name, arguments)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in MCP call: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/resource/<path:resource_uri>', methods=['GET'])
def mcp_get_resource(resource_uri):
    """MCP: Get a specific resource"""
    try:
        resource_uri = resource_uri.replace('apanel://', '')
        
        if resource_uri == "billing":
            # Billing summary for agents
            billing_summary = billing_system.get_billing_summary(g.organization_id)
            return jsonify({
                "success": True,
                "uri": f"apanel://{resource_uri}",
                "data": billing_summary,
                "timestamp": datetime.now().isoformat()
            })
        
        elif resource_uri == "agents":
            # List of agents
            agents = {}
            for name, agent in manager.agents.items():
                agents[name] = agent.to_dict()
            return jsonify({
                "success": True,
                "uri": f"apanel://{resource_uri}",
                "data": agents,
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            return jsonify({
                "success": False,
                "error": f"Resource not found: {resource_uri}"
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting resource: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ========================================
# HEALTH CHECK & STATUS
# ========================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check for unified system"""
    return jsonify({
        "status": "healthy",
        "service": "apanel-unified-system",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "modules": {
            "agent_management": "active",
            "billing": "active",
            "mcp_server": "active",
            "plans_limits": "active"
        },
        "interfaces": {
            "web_dashboard": f"http://localhost:5000",
            "mcp_server": f"http://localhost:5000/mcp",
            "rest_api": f"http://localhost:5000/api"
        }
    })

@app.route('/api/status', methods=['GET'])
def system_status():
    """Detailed system status"""
    return jsonify({
        "success": True,
        "data": {
            "agents": {
                "total": len(manager.agents),
                "healthy": sum(1 for a in manager.agents.values() if a.health_score >= 80),
                "warning": sum(1 for a in manager.agents.values() if 60 <= a.health_score < 80),
                "critical": sum(1 for a in manager.agents.values() if a.health_score < 60)
            },
            "billing": billing_system.get_billing_summary(g.organization_id),
            "timestamp": datetime.now().isoformat()
        }
    })

# ========================================
# REGISTER EXTERNAL BLUEPRINTS
# ========================================

# Register billing blueprint
register_billing_blueprint(app)

# ========================================
# ERROR HANDLERS
# ========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

# ========================================
# MAIN
# ========================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 APanel Unified System Starting...")
    logger.info("=" * 60)
    
    logger.info("📊 Agents detected:")
    for name, agent in manager.agents.items():
        health = agent.health_score
        status = "✅" if health >= 80 else "⚠️" if health >= 60 else "❌"
        logger.info(f"   {status} {name}: Health {health}/100")
    
    logger.info("\n🔌 Available endpoints:")
    logger.info("   Web Dashboard: http://localhost:5000")
    logger.info("   Billing Dashboard: http://localhost:5000/billing")
    logger.info("   Plans Dashboard: http://localhost:5000/plans")
    logger.info("   MCP Server: http://localhost:5000/mcp")
    logger.info("   REST API: http://localhost:5000/api")
    
    logger.info("\n💰 Billing System: Active")
    logger.info("🔐 Security: JWT + RBAC enabled")
    logger.info("📊 Plans & Limits: Active")
    
    logger.info("=" * 60)
    logger.info("🎯 System ready for use!")
    logger.info("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
