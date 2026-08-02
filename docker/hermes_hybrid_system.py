#!/usr/bin/env python3
"""
Hermes Multi-Agent Management System - Hybrid (Human + Agent)
Web Dashboard + MCP Server in a single system

Architecture:
- Human Interface: Web Dashboard (Flask)
- Agent Interface: MCP Server (JSON-RPC)
- Unified Backend: Shared logic
"""

import json
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Flask for human interface
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# MCP for agent interface
import hermes_multi_agent_mcp as mcp_module

# Import the existing manager
from hermes_multi_agent_dashboard import HermesMultiAgentManager, HermesAgent

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HermesHybrid')

app = Flask(__name__)
CORS(app)  # Enable CORS for MCP

# Initialize manager
manager = HermesMultiAgentManager()
mcp_server = mcp_module.HermesMultiAgentMCP()
mcp_server.manager = manager

# ==========================================
# HUMAN INTERFACE - REST API (Web Dashboard)
# ==========================================

@app.route('/')
def index():
    """Main dashboard page for humans."""
    return render_template('dashboard.html')

@app.route('/api/agents')
def get_agents():
    """API for humans: Get all agents."""
    agents_data = {name: agent.to_dict() for name, agent in manager.agents.items()}
    return jsonify(agents_data)

@app.route('/api/metrics')
def get_metrics():
    """API for humans: Get aggregated metrics."""
    metrics = manager.get_aggregated_metrics()
    return jsonify(metrics)

@app.route('/api/agents/<agent_name>')
def get_agent(agent_name):
    """API for humans: Get specific agent information."""
    agent = manager.agents.get(agent_name)
    
    if not agent:
        return jsonify({
            "success": False,
            "error": f"Agent '{agent_name}' not found"
        }), 404
    
    return jsonify(agent.to_dict())

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "agents_count": len(manager.agents),
        "monitoring": manager.monitoring,
        "timestamp": datetime.now().isoformat()
    })

# ==========================================
# AGENT INTERFACE - MCP Server
# ==========================================

@app.route('/mcp/tools', methods=['GET'])
def mcp_list_tools():
    """MCP: List all available tools."""
    tools = mcp_server.get_tools_list()
    return jsonify({
        "success": True,
        "tools": tools
    })

@app.route('/mcp/call', methods=['POST'])
def mcp_call_tool():
    """MCP: Execute a tool."""
    try:
        data = request.json
        tool_name = data.get('tool')
        arguments = data.get('arguments', {})
        
        if not tool_name:
            return jsonify({
                "success": False,
                "error": "Tool name is required"
            }), 400
        
        # Execute the tool asynchronously
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
    """MCP: Get a specific resource."""
    try:
        resource_uri = resource_uri.replace('apanel://', '')
        
        if resource_uri == "billing":
            # Billing information for agents
            billing_summary = {
                "total_cost": 123.45,
                "total_tokens": 50000,
                "calls_count": 150,
                "timestamp": datetime.now().isoformat()
            }
            return jsonify({
                "success": True,
                "uri": f"apanel://{resource_uri}",
                "data": billing_summary,
                "timestamp": datetime.now().isoformat()
            })
        
        elif resource_uri == "agents":
            # List of agents for agents
            agents = {}
            for name, agent in manager.agents.items():
                agents[name] = {
                    "name": agent.name,
                    "status": agent.status,
                    "health_score": agent.health_score
                }
            return jsonify({
                "success": True,
                "uri": f"apanel://{resource_uri}",
                "data": agents,
                "timestamp": datetime.now().isoformat()
            })
        
        elif resource_uri == "plans":
            # Plans and limits for agents
            plans_info = {
                "current_plan": "Pro",
                "tier": "pro",
                "limits": {
                    "concurrent_agents": 20,
                    "monthly_tokens": 500000
                },
                "usage": {
                    "concurrent_agents": len(manager.agents),
                    "monthly_tokens": 25000
                }
            }
            return jsonify({
                "success": True,
                "uri": f"apanel://{resource_uri}",
                "data": plans_info,
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

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Hermes Hybrid System Starting...")
    logger.info("=" * 60)
    
    logger.info("\n📊 Agents detected:")
    for name, agent in manager.agents.items():
        health = agent.health_score
        status = "✅" if health >= 80 else "⚠️" if health >= 60 else "❌"
        logger.info(f"   {status} {name}: Health {health}/100")
    
    logger.info("\n🔌 Available endpoints:")
    logger.info("   Web Dashboard: http://localhost:5000")
    logger.info("   MCP Server: http://localhost:5000/mcp")
    logger.info("   REST API: http://localhost:5000/api")
    
    logger.info("\n💡 Interfaces:")
    logger.info("   Human: Web Dashboard (Flask)")
    logger.info("   Agent: MCP Server (JSON-RPC)")
    
    logger.info("=" * 60)
    logger.info("🎯 Hybrid system ready!")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
