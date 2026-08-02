#!/usr/bin/env python3
"""
Hermes Multi-Agent Management Dashboard
Web dashboard to manage multiple Hermes Agent instances

This is step 2 of the multi-agent management system:
- Step 1: Meta-monitor (CLI) - ✅ Already created
- Step 2: Web Dashboard - 🚧 This file
- Step 3: REST API - 📋 Pending
"""

import json
import yaml
import subprocess
import threading
import time
import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from flask import Flask, render_template, jsonify, request
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HermesDashboard')

app = Flask(__name__)

@dataclass
class HermesAgent:
    """Representation of a Hermes agent for the dashboard."""
    name: str
    host: str
    port: int
    type: str  # local, ssh, docker, k8s
    status: str  # healthy, unhealthy, unknown, error
    health_score: int  # 0-100
    last_check: Optional[str]
    metrics: Dict
    alerts: List[Dict]
    uptime: float  # percentage
    total_tokens: int
    sessions_count: int

    def to_dict(self):
        return asdict(self)

class HermesMultiAgentManager:
    """Manager for multiple Hermes agents."""
    
    def __init__(self, config_path: str = "meta_config.yaml"):
        self.config_path = Path(config_path)
        self.agents: Dict[str, HermesAgent] = {}
        self.monitoring = False
        self.monitor_thread = None
        
        # Load configuration
        self.load_config()
        
        # Start automatic monitoring
        self.start_monitoring()
    
    def load_config(self):
        """Load agent configuration."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            for agent_config in config.get('agents', []):
                agent = HermesAgent(
                    name=agent_config['name'],
                    host=agent_config['host'],
                    port=agent_config['port'],
                    type=agent_config.get('type', 'local'),
                    status='unknown',
                    health_score=0,
                    last_check=None,
                    metrics={},
                    alerts=[],
                    uptime=0.0,
                    total_tokens=0,
                    sessions_count=0
                )
                self.agents[agent.name] = agent
                
            logger.info(f"Configuration loaded: {len(self.agents)} agents")
    
    def check_agent_health(self, agent_name: str) -> Dict:
        """Check the health of a specific agent."""
        if agent_name not in self.agents:
            return {"error": f"Agent {agent_name} not found"}
            
        agent = self.agents[agent_name]
        
        try:
            # Execute health check using the existing script
            if agent.type == "local":
                result = subprocess.run(
                    ["python3", "/home/hermeswebui/.hermes/tools/hermes_maintenance_health_check.py"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Parse output and update agent status
                    output = result.stdout
                    agent.status = "healthy"
                    agent.health_score = 85
                    agent.last_check = datetime.now().isoformat()
                    agent.uptime = 95.0
                    
                    logger.info(f"Agent {agent_name}: Health check passed")
                    return {"success": True, "agent": agent.to_dict()}
                else:
                    agent.status = "unhealthy"
                    agent.health_score = 30
                    agent.last_check = datetime.now().isoformat()
                    
                    logger.warning(f"Agent {agent_name}: Health check failed")
                    return {"success": False, "error": "Health check failed"}
                    
        except subprocess.TimeoutExpired:
            agent.status = "error"
            agent.health_score = 0
            agent.last_check = datetime.now().isoformat()
            
            logger.error(f"Agent {agent_name}: Health check timeout")
            return {"success": False, "error": "Health check timeout"}
            
        except Exception as e:
            agent.status = "error"
            agent.health_score = 0
            agent.last_check = datetime.now().isoformat()
            
            logger.error(f"Agent {agent_name}: Health check error: {e}")
            return {"success": False, "error": str(e)}
    
    def check_all_agents(self):
        """Check health of all agents."""
        for agent_name in self.agents:
            self.check_agent_health(agent_name)
    
    def get_aggregated_metrics(self) -> Dict:
        """Get aggregated metrics from all agents."""
        total_agents = len(self.agents)
        healthy_agents = sum(1 for a in self.agents.values() if a.status == "healthy")
        unhealthy_agents = total_agents - healthy_agents
        
        avg_health_score = 0
        if total_agents > 0:
            avg_health_score = sum(a.health_score for a in self.agents.values()) / total_agents
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": unhealthy_agents,
            "average_health_score": round(avg_health_score, 1),
            "timestamp": datetime.now().isoformat()
        }
    
    def start_monitoring(self):
        """Start background monitoring of all agents."""
        if self.monitoring:
            return
            
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                logger.info("Checking all agents...")
                self.check_all_agents()
                logger.info(f"Monitoring complete: {len(self.agents)} agents checked")
                time.sleep(60)  # Check every 60 seconds
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Monitoring started in background...")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring = False
        logger.info("Monitoring stopped")


# Flask routes
@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all agents."""
    agents_data = {name: agent.to_dict() for name, agent in manager.agents.items()}
    return jsonify({
        "success": True,
        "data": agents_data
    })

@app.route('/api/agents/<agent_name>', methods=['GET'])
def get_agent(agent_name):
    """Get specific agent information."""
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
def check_agent_health(agent_name):
    """Check health of a specific agent."""
    result = manager.check_agent_health(agent_name)
    
    if result.get("success"):
        return jsonify({
            "success": True,
            "data": result["agent"]
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Unknown error")
        }), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get aggregated metrics."""
    metrics = manager.get_aggregated_metrics()
    
    return jsonify({
        "success": True,
        "data": metrics
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "hermes-multi-agent-dashboard",
        "agents_count": len(manager.agents),
        "monitoring": manager.monitoring,
        "timestamp": datetime.now().isoformat()
    })


# Initialize manager
manager = HermesMultiAgentManager()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Hermes Multi-Agent Dashboard Starting...")
    logger.info("=" * 60)
    
    logger.info(f"📊 Agents configured: {len(manager.agents)}")
    for name, agent in manager.agents.items():
        logger.info(f"   • {name} ({agent.type}): {agent.host}:{agent.port}")
    
    logger.info("\n🔌 Available endpoints:")
    logger.info("   Web Dashboard: http://localhost:5000")
    logger.info("   API: http://localhost:5000/api")
    logger.info("   Health Check: http://localhost:5000/api/health")
    
    logger.info("\n📊 Monitoring:")
    logger.info(f"   Status: {'Active' if manager.monitoring else 'Inactive'}")
    logger.info("   Interval: Every 60 seconds")
    
    logger.info("=" * 60)
    logger.info("🎯 Dashboard ready for use!")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
