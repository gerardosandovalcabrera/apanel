#!/usr/bin/env python3
"""
Hermes Multi-Agent Management System - Híbrido (Humano + Agente)
Dashboard Web + MCP Server en un solo sistema

Arquitectura:
- Interfaz Humana: Dashboard Web (Flask)
- Interfaz Agentes: MCP Server (JSON-RPC)
- Backend Unificado: Lógica compartida
"""

import json
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Flask para interfaz humana
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# MCP para interfaz de agentes
import hermes_multi_agent_mcp as mcp_module

# Importar el manager existente
from hermes_multi_agent_dashboard import HermesMultiAgentManager, HermesAgent

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HermesHybrid')

app = Flask(__name__)
CORS(app)  # Habilitar CORS para MCP

# Inicializar manager
manager = HermesMultiAgentManager()
mcp_server = mcp_module.HermesMultiAgentMCP()
mcp_server.manager = manager

# ==========================================
# INTERFAZ HUMANA - API REST (Dashboard Web)
# ==========================================

@app.route('/')
def index():
    """Página principal del dashboard para humanos."""
    return render_template('dashboard.html')

@app.route('/api/agents')
def get_agents():
    """API para humanos: Obtener todos los agentes."""
    agents_data = {name: agent.to_dict() for name, agent in manager.agents.items()}
    return jsonify(agents_data)

@app.route('/api/metrics')
def get_metrics():
    """API para humanos: Obtener métricas agregadas."""
    metrics = manager.get_aggregated_metrics()
    return jsonify(metrics)

# ==========================================
# INTERFAZ AGENTES - MCP Server (JSON-RPC)
# ==========================================

@app.route('/mcp/tools', methods=['GET'])
def mcp_list_tools():
    """MCP: Listar todas las herramientas disponibles."""
    tools = mcp_server.get_tools_list()
    return jsonify({
        "success": True,
        "tools": tools
    })

@app.route('/mcp/resources', methods=['GET'])
def mcp_list_resources():
    """MCP: Listar todos los recursos disponibles."""
    resources = mcp_server.get_resources_list()
    return jsonify({
        "success": True,
        "resources": resources
    })

@app.route('/mcp/call', methods=['POST'])
def mcp_call_tool():
    """MCP: Ejecutar una herramienta (JSON-RPC style)."""
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
    """MCP: Obtener un recurso específico."""
    try:
        # Normalizar URI
        resource_uri = resource_uri.replace('hermes://', '')
        
        if resource_uri == "agents":
            # Lista de agentes
            agents = {}
            for name, agent in manager.agents.items():
                agents[name] = agent.to_dict()
            return jsonify({
                "success": True,
                "uri": f"hermes://{resource_uri}",
                "data": agents,
                "timestamp": datetime.now().isoformat()
            })
            
        elif resource_uri == "health":
            # Salud del sistema
            health = manager.get_aggregated_metrics()
            return jsonify({
                "success": True,
                "uri": f"hermes://{resource_uri}",
                "data": health,
                "timestamp": datetime.now().isoformat()
            })
            
        elif resource_uri == "alerts":
            # Alertas activas
            alerts = []
            for name, agent in manager.agents.items():
                for alert in agent.alerts:
                    alerts.append({
                        "agent": name,
                        **alert
                    })
            return jsonify({
                "success": True,
                "uri": f"hermes://{resource_uri}",
                "data": {
                    "total": len(alerts),
                    "alerts": alerts
                },
                "timestamp": datetime.now().isoformat()
            })
            
        elif resource_uri == "metrics":
            # Métricas del sistema
            metrics = manager.get_aggregated_metrics()
            return jsonify({
                "success": True,
                "uri": f"hermes://{resource_uri}",
                "data": metrics,
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

# ==========================================
# ENDPOINTS COMPARTIDOS (Humanos + Agentes)
# ==========================================

@app.route('/api/health')
def health_check():
    """Health check compartido para humanos y agentes."""
    return jsonify({
        "status": "healthy",
        "service": "hermes-hybrid-dashboard",
        "timestamp": datetime.now().isoformat(),
        "interfaces": {
            "human": {
                "dashboard": f"http://{request.host}/",
                "api": f"http://{request.host}/api/"
            },
            "agent": {
                "mcp_server": f"http://{request.host}/mcp/",
                "protocol": "HTTP+JSON"
            }
        },
        "agents": {
            "total": len(manager.agents),
            "healthy": sum(1 for a in manager.agents.values() if a.health_score >= 70),
            "unhealthy": sum(1 for a in manager.agents.values() if a.health_score < 70)
        }
    })

# ==========================================
# DOCUMENTACIÓN DE AMBAS INTERFACES
# ==========================================

@app.route('/docs')
def documentation():
    """Documentación de ambas interfaces."""
    docs = {
        "hermes_hybrid_management_system": {
            "version": "2.0.0",
            "description": "Sistema híbrido de administración multi-agente con interfaces para humanos y agentes",
            "timestamp": datetime.now().isoformat()
        },
        "human_interface": {
            "type": "Web Dashboard + REST API",
            "access": {
                "dashboard": "http://localhost:5000/",
                "api_base": "http://localhost:5000/api/",
                "health": "http://localhost:5000/api/health"
            },
            "endpoints": {
                "GET /": "Dashboard web principal",
                "GET /api/agents": "Obtener todos los agentes",
                "GET /api/metrics": "Obtener métricas agregadas",
                "GET /api/health": "Health check del sistema"
            },
            "use_cases": [
                "Monitoreo visual en tiempo real",
                "Gestión manual de agentes",
                "Visualización de métricas y alertas",
                "Interacción con botones de acción"
            ]
        },
        "agent_interface": {
            "type": "MCP Server (HTTP+JSON)",
            "access": {
                "mcp_base": "http://localhost:5000/mcp/",
                "tools": "http://localhost:5000/mcp/tools",
                "resources": "http://localhost:5000/mcp/resources",
                "call": "http://localhost:5000/mcp/call"
            },
            "protocol": {
                "transport": "HTTP POST",
                "format": "JSON",
                "style": "JSON-RPC inspired"
            },
            "tools": [
                "list_agents - Listar agentes con filtros",
                "get_agent_health - Obtener salud de un agente",
                "get_system_metrics - Obtener métricas del sistema",
                "restart_agent - Reiniciar un agente",
                "get_agent_logs - Obtener logs de un agente",
                "execute_agent_command - Ejecutar comandos remotos",
                "register_remote_agent - Registrar nuevo agente",
                "get_system_alerts - Obtener alertas activas",
                "get_agent_performance - Obtener rendimiento",
                "check_all_agents - Health check de todos"
            ],
            "resources": [
                "hermes://agents - Lista de agentes",
                "hermes://health - Salud del sistema",
                "hermes://alerts - Alertas activas",
                "hermes://metrics - Métricas del sistema"
            ],
            "use_cases": [
                "Monitoreo programático por agentes",
                "Automatización de tareas de mantenimiento",
                "Integración con otros sistemas",
                "Respuestas automáticas a alertas",
                "Análisis de tendencias y patrones"
            ]
        },
        "shared_features": {
            "backend": "Lógica compartida (HermesMultiAgentManager)",
            "data_source": "Única fuente de verdad",
            "real_time": "Datos en tiempo real para ambos",
            "authentication": "API key para agentes, sesión para humanos"
        },
        "examples": {
            "human_usage": {
                "description": "Un administrador humano usando el dashboard web",
                "workflow": [
                    "1. Accede a http://localhost:5000/",
                    "2. Ve el estado de todos los agentes en tarjetas visuales",
                    "3. Hace clic en 'Verificar' en un agente específico",
                    "4. Ve el health score actualizado en tiempo real",
                    "5. Hace clic en 'Reiniciar' si es necesario"
                ]
            },
            "agent_usage": {
                "description": "Un agente AI monitoreando el sistema",
                "workflow": [
                    "1. Consulta herramientas disponibles: GET /mcp/tools",
                    "2. Obtiene lista de agentes: POST /mcp/call con tool='list_agents'",
                    "3. Verifica salud de agentes problemáticos: POST /mcp/call con tool='get_agent_health'",
                    "4. Analiza alertas: POST /mcp/call con tool='get_system_alerts'",
                    "5. Toma decisiones automáticas basadas en datos"
                ],
                "example_call": {
                    "method": "POST",
                    "url": "http://localhost:5000/mcp/call",
                    "headers": {"Content-Type": "application/json"},
                    "body": {
                        "tool": "get_system_metrics",
                        "arguments": {"include_agents": true}
                    }
                }
            }
        }
    }
    
    return jsonify(docs)

# ==========================================
# INICIO DEL SERVIDOR HÍBRIDO
# ==========================================

def main():
    """Inicia el servidor híbrido."""
    logger.info("🚀 Iniciando Sistema Híbrido de Administración Multi-Agente")
    logger.info("👥 Interfaz Humana: Dashboard Web + REST API")
    logger.info("🤖 Interfaz Agentes: MCP Server (HTTP+JSON)")
    logger.info("🔄 Backend Unificado: Lógica compartida")
    logger.info("")
    
    # Iniciar el servidor Flask
    logger.info("🌐 Servidor iniciado en http://localhost:5000")
    logger.info("📊 Dashboard: http://localhost:5000/")
    logger.info("📚 Documentación: http://localhost:5000/docs")
    logger.info("🤖 MCP Server: http://localhost:5000/mcp/")
    logger.info("")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

if __name__ == '__main__':
    main()
