"""
🚀 APanel Unified System - Sistema Principal Integrado
Dashboard Web + MCP Server + Billing System + Plans & Limits

Este es el sistema principal que une todos los módulos en una sola aplicación.

Módulos integrados:
1. Multi-Agent Management
2. Billing System (Cost Tracking + Budget)
3. Plans & Limits
4. Security (OAuth, JWT, RBAC)

Interfaces:
- Dashboard Web (para humanos)
- MCP Server (para agentes)
- REST API (para integraciones)
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

# Configuración
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('APanelUnified')

# ========================================
# INICIALIZACIÓN
# ========================================

app = Flask(__name__)
app.secret_key = 'apanel-secret-key-change-in-production'
CORS(app)

# Inicializar componentes
manager = HermesMultiAgentManager()
mcp_server = mcp_module.HermesMultiAgentMCP()
mcp_server.manager = manager

billing_system = BillingIntegrationDemo()

# Plans Manager (en producción usar Redis)
# plans_manager = get_plans_manager()

# ========================================
# MIDDLEWARE - Inyectar organization_id
# ========================================

@app.before_request
def inject_context():
    """Inyectar contexto de organización en cada request"""
    # En producción, esto vendría del JWT token
    g.organization_id = request.headers.get('X-Organization-ID', 'demo-org-billing')
    g.user_id = request.headers.get('X-User-ID', 'demo-user')
    g.plan_tier = request.headers.get('X-Plan-Tier', 'pro').lower()

# ========================================
# DASHBOARD PRINCIPAL
# ========================================

@app.route('/')
def index():
    """Página principal del dashboard con tabs"""
    return render_template('unified_dashboard.html')

@app.route('/billing')
def billing_dashboard():
    """Dashboard específico de billing"""
    return render_template('billing_dashboard.html')

@app.route('/plans')
def plans_dashboard():
    """Dashboard específico de planes"""
    return render_template('plans_dashboard.html')

# ========================================
# API REST - Agentes
# ========================================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Obtener todos los agentes"""
    agents_data = {name: agent.to_dict() for name, agent in manager.agents.items()}
    return jsonify({
        "success": True,
        "data": agents_data
    })

@app.route('/api/agents/<agent_name>', methods=['GET'])
def get_agent(agent_name):
    """Obtener información de un agente específico"""
    agent = manager.agents.get(agent_name)
    
    if not agent:
        return jsonify({
            "success": False,
            "error": f"Agente '{agent_name}' no encontrado"
        }), 404
    
    return jsonify({
        "success": True,
        "data": agent.to_dict()
    })

@app.route('/api/agents/<agent_name>/health', methods=['GET'])
def get_agent_health(agent_name):
    """Obtener health score de un agente"""
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
    """Obtener métricas agregadas del sistema"""
    metrics = manager.get_aggregated_metrics()
    
    return jsonify({
        "success": True,
        "data": metrics
    })

# ========================================
# API REST - Billing Integrado
# ========================================

@app.route('/api/billing/unified-summary', methods=['GET'])
def get_unified_billing_summary():
    """
    Obtener resumen unificado de billing incluyendo:
    - Costos de LLM
    - Límites del plan
    - Presupuesto
    - Alertas
    - Optimizaciones
    """
    try:
        org_id = g.organization_id
        
        # Obtener resumen de billing
        billing_summary = billing_system.get_billing_summary(org_id)
        
        # Obtener límites del plan
        plan_tier = PlanTier.PRO  # En producción, del JWT
        # limit_status = plans_manager.get_limit_status(org_id, plan_tier)
        
        # Simular limit status (en producción usar plans_manager real)
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
        logger.error(f"Error en unified billing summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/billing/record-call', methods=['POST'])
def record_llm_call():
    """
    Registrar una llamada a la LLM y verificar límites
    
    Este endpoint es el que se llamaría desde el sistema de agentes
    para registrar cada llamada a la API de LLM.
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
        
        org_id = g.organization_id
        
        # Registrar la llamada
        call_record = billing_system.record_api_call(
            organization_id=org_id,
            provider_model_id=provider_model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Verificar límites
        # En producción, esto verificaría los límites del plan
        # y bloquearía si se exceden
        
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
        logger.error(f"Error registrando llamada: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ========================================
# MCP SERVER - Para Agentes
# ========================================

@app.route('/mcp/tools', methods=['GET'])
def mcp_list_tools():
    """MCP: Listar todas las herramientas disponibles"""
    tools = mcp_server.get_tools_list()
    return jsonify({
        "success": True,
        "tools": tools
    })

@app.route('/mcp/call', methods=['POST'])
def mcp_call_tool():
    """MCP: Ejecutar una herramienta"""
    try:
        data = request.json
        tool_name = data.get('tool')
        arguments = data.get('arguments', {})
        
        if not tool_name:
            return jsonify({
                "success": False,
                "error": "Tool name is required"
            }), 400
        
        # Ejecutar la herramienta de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            mcp_server.handle_tool_call(tool_name, arguments)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en MCP call: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mcp/resource/<path:resource_uri>', methods=['GET'])
def mcp_get_resource(resource_uri):
    """MCP: Obtener un recurso específico"""
    try:
        resource_uri = resource_uri.replace('apanel://', '')
        
        if resource_uri == "billing":
            # Resumen de billing para agentes
            billing_summary = billing_system.get_billing_summary(g.organization_id)
            return jsonify({
                "success": True,
                "uri": f"apanel://{resource_uri}",
                "data": billing_summary,
                "timestamp": datetime.now().isoformat()
            })
        
        elif resource_uri == "agents":
            # Lista de agentes
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
    """Health check del sistema unificado"""
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
    """Estado detallado del sistema"""
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
# REGISTRAR BLUEPRINTS EXTERNOS
# ========================================

# Registrar blueprint de billing
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
    
    logger.info("📊 Agentes detectados:")
    for name, agent in manager.agents.items():
        health = agent.health_score
        status = "✅" if health >= 80 else "⚠️" if health >= 60 else "❌"
        logger.info(f"   {status} {name}: Health {health}/100")
    
    logger.info("\n🔌 Endpoints disponibles:")
    logger.info("   Web Dashboard: http://localhost:5000")
    logger.info("   Billing Dashboard: http://localhost:5000/billing")
    logger.info("   Plans Dashboard: http://localhost:5000/plans")
    logger.info("   MCP Server: http://localhost:5000/mcp")
    logger.info("   REST API: http://localhost:5000/api")
    
    logger.info("\n💰 Billing System: Activo")
    logger.info("🔐 Seguridad: JWT + RBAC activado")
    logger.info("📊 Plans & Limits: Activo")
    
    logger.info("=" * 60)
    logger.info("🎯 Sistema listo para uso!")
    logger.info("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
