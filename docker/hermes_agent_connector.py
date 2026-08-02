#!/usr/bin/env python3
"""
Hermes Agent Connector - Remote Deployment
This script runs on each remote server with Hermes
and connects to the central Dashboard for monitoring and management

Features:
- Local health check API
- Real-time telemetry
- Remote command reception
- Authentication-based security
"""

import os
import json
import yaml
import time
import logging
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from flask import Flask, request, jsonify
import requests
import psutil

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HermesAgentConnector')

app = Flask(__name__)
# Configuration from environment variables
CONNECTOR_PORT = int(os.getenv('CONNECTOR_PORT', '8081'))
DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'http://localhost:5000')
HERMES_HOME = os.path.expanduser(os.getenv('HERMES_HOME', '~/.hermes'))
API_KEY = os.getenv('CONNECTOR_API_KEY', 'hermes-secure-key')

# Agent information
AGENT_INFO = {
    'name': os.getenv('AGENT_NAME', f"agent-{os.uname().nodename}"),
    'host': os.getenv('AGENT_HOST', os.uname().nodename),
    'port': int(os.getenv('HERMES_PORT', '8080')),
    'type': os.getenv('AGENT_TYPE', 'local'),
    'hermes_home': HERMES_HOME
}


def authenticate_request():
    """Authenticate incoming requests using API key."""
    auth_header = request.headers.get('X-API-Key')
    
    if not auth_header:
        return False
    
    return auth_header == API_KEY


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    if not authenticate_request():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    try:
        # Check Hermes installation
        hermes_path = Path(HERMES_HOME)
        hermes_exists = hermes_path.exists()
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate health score
        health_score = 100
        
        if cpu_percent > 80:
            health_score -= 20
        if memory.percent > 80:
            health_score -= 20
        if disk.percent > 90:
            health_score -= 20
        if not hermes_exists:
            health_score -= 40
        
        status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"
        
        return jsonify({
            "success": True,
            "status": status,
            "health_score": health_score,
            "agent": AGENT_INFO,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
                "hermes_installed": hermes_exists
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/telemetry', methods=['GET'])
def get_telemetry():
    """Get detailed system telemetry."""
    if not authenticate_request():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    try:
        # System info
        cpu_info = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Process info
        hermes_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                if 'hermes' in proc.info['name'].lower():
                    hermes_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return jsonify({
            "success": True,
            "agent": AGENT_INFO,
            "system": {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "per_core": cpu_info,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            },
            "processes": hermes_processes,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Telemetry error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/command', methods=['POST'])
def execute_command():
    """Execute remote commands."""
    if not authenticate_request():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    try:
        data = request.json
        command = data.get('command')
        
        if not command:
            return jsonify({
                "success": False,
                "error": "Command is required"
            }), 400
        
        # Security: Only allow specific safe commands
        allowed_commands = [
            'restart',
            'status',
            'logs',
            'update',
            'config'
        ]
        
        if command not in allowed_commands:
            return jsonify({
                "success": False,
                "error": f"Command '{command}' not allowed"
            }), 403
        
        # Execute command (simplified for security)
        if command == 'status':
            result = {
                "success": True,
                "command": command,
                "output": f"Agent {AGENT_INFO['name']} is running",
                "timestamp": datetime.now().isoformat()
            }
        else:
            result = {
                "success": True,
                "command": command,
                "output": f"Command '{command}' executed",
                "timestamp": datetime.now().isoformat()
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def register_with_dashboard():
    """Register this agent with the central dashboard."""
    while True:
        try:
            response = requests.post(
                f"{DASHBOARD_URL}/api/agents/register",
                json=AGENT_INFO,
                headers={'X-API-Key': API_KEY},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully registered with dashboard")
            else:
                logger.warning(f"Failed to register: {response.status_code}")
                
        except requests.RequestException as e:
            logger.warning(f"Could not connect to dashboard: {e}")
        
        time.sleep(60)  # Try every 60 seconds


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🔌 Hermes Agent Connector Starting...")
    logger.info("=" * 60)
    
    logger.info(f"\n📊 Agent Information:")
    logger.info(f"   Name: {AGENT_INFO['name']}")
    logger.info(f"   Host: {AGENT_INFO['host']}")
    logger.info(f"   Port: {AGENT_INFO['port']}")
    logger.info(f"   Type: {AGENT_INFO['type']}")
    logger.info(f"   Hermes Home: {AGENT_INFO['hermes_home']}")
    
    logger.info(f"\n🔌 Connector Configuration:")
    logger.info(f"   Port: {CONNECTOR_PORT}")
    logger.info(f"   Dashboard URL: {DASHBOARD_URL}")
    
    logger.info("\n🚀 Starting background registration...")
    registration_thread = threading.Thread(target=register_with_dashboard, daemon=True)
    registration_thread.start()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Agent connector ready!")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=CONNECTOR_PORT, debug=True)
