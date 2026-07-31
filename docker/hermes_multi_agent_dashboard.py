#!/usr/bin/env python3
"""
Hermes Multi-Agent Management Dashboard
Dashboard web para administrar múltiples instancias de Hermes Agent

Este es el paso 2 del sistema de administración multi-agente:
- Paso 1: Meta-monitor (CLI) - ✅ Ya creado
- Paso 2: Dashboard web - 🚧 Este archivo
- Paso 3: API REST - 📋 Pendiente
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

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HermesDashboard')

app = Flask(__name__)

@dataclass
class HermesAgent:
    """Representación de un agente de Hermes para el dashboard."""
    name: str
    host: str
    port: int
    type: str  # local, ssh, docker, k8s
    status: str  # healthy, unhealthy, unknown, error
    health_score: int  # 0-100
    last_check: Optional[str]
    metrics: Dict
    alerts: List[Dict]
    uptime: float  # porcentaje
    total_tokens: int
    sessions_count: int

    def to_dict(self):
        return asdict(self)

class HermesMultiAgentManager:
    """Gestor de múltiples agentes de Hermes."""
    
    def __init__(self, config_path: str = "meta_config.yaml"):
        self.config_path = Path(config_path)
        self.agents: Dict[str, HermesAgent] = {}
        self.monitoring = False
        self.monitor_thread = None
        
        # Cargar configuración
        self.load_config()
        
        # Iniciar monitoreo automático
        self.start_monitoring()
    
    def load_config(self):
        """Carga la configuración de agentes."""
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
                
            logger.info(f"Configuración cargada: {len(self.agents)} agentes")
    
    def check_agent_health(self, agent_name: str) -> Dict:
        """Verifica la salud de un agente específico."""
        if agent_name not in self.agents:
            return {"error": f"Agente {agent_name} no encontrado"}
            
        agent = self.agents[agent_name]
        
        try:
            # Ejecutar el health check usando el script existente
            if agent.type == "local":
                result = subprocess.run(
                    ["python3", "/home/hermeswebui/.hermes/tools/hermes_maintenance_health_check.py"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    health_data = json.loads(result.stdout)
                    
                    # Actualizar estado del agente
                    agent.status = "healthy"
                    agent.health_score = health_data.get('health_score', 0)
                    agent.last_check = datetime.datetime.now().isoformat()
                    agent.metrics = health_data
                    
                    # Extraer métricas adicionales
                    resource_usage = health_data.get('resource_usage', {})
                    agent.total_tokens = health_data.get('performance_metrics', {}).get('total_tokens', 0)
                    agent.sessions_count = health_data.get('performance_metrics', {}).get('total_sessions', 0)
                    
                    # Calcular uptime (simulado por ahora)
                    agent.uptime = 100.0 if agent.health_score >= 70 else 50.0
                    
                    # Detectar alertas
                    alerts = []
                    if agent.health_score < 70:
                        alerts.append({"level": "warning", "message": f"Health score bajo: {agent.health_score}"})
                    if agent.health_score < 50:
                        alerts.append({"level": "critical", "message": f"Health score crítico: {agent.health_score}"})
                    
                    agent.alerts = alerts
                    
                    return {
                        "status": "success",
                        "agent": agent.to_dict()
                    }
                else:
                    agent.status = "check_failed"
                    agent.health_score = 0
                    return {"status": "error", "error": result.stderr}
            
            # Para otros tipos (SSH, Docker, K8s) - implementar similar
            return {"status": "not_implemented", "message": f"Tipo {agent.type} no implementado aún"}
            
        except Exception as e:
            agent.status = "error"
            agent.health_score = 0
            return {"status": "error", "error": str(e)}
    
    def check_all_agents(self) -> Dict:
        """Verifica la salud de todos los agentes."""
        results = {}
        for agent_name in self.agents:
            results[agent_name] = self.check_agent_health(agent_name)
        return results
    
    def get_aggregated_metrics(self) -> Dict:
        """Obtiene métricas agregadas de todos los agentes."""
        total_tokens = 0
        total_sessions = 0
        avg_health_score = 0
        healthy_count = 0
        unhealthy_count = 0
        agent_count = len(self.agents)
        
        for agent in self.agents.values():
            total_tokens += agent.total_tokens
            total_sessions += agent.sessions_count
            avg_health_score += agent.health_score
            
            if agent.health_score >= 70:
                healthy_count += 1
            else:
                unhealthy_count += 1
        
        if agent_count > 0:
            avg_health_score = avg_health_score / agent_count
        
        return {
            "agent_count": agent_count,
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "total_tokens": total_tokens,
            "total_sessions": total_sessions,
            "avg_health_score": round(avg_health_score, 2),
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def monitor_loop(self):
        """Loop principal de monitoreo."""
        logger.info("Iniciando loop de monitoreo del dashboard...")
        
        while self.monitoring:
            try:
                logger.info("Verificando todos los agentes...")
                self.check_all_agents()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
                time.sleep(60)
    
    def start_monitoring(self):
        """Inicia el monitoreo en segundo plano."""
        if self.monitoring:
            logger.warning("Monitoreo ya está activo")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoreo iniciado en segundo plano")
    
    def stop_monitoring(self):
        """Detiene el monitoreo."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitoreo detenido")

# Inicializar el gestor
manager = HermesMultiAgentManager()

# Rutas de la API
@app.route('/')
def index():
    """Página principal del dashboard."""
    return render_template('dashboard.html')

@app.route('/api/agents')
def get_agents():
    """API para obtener todos los agentes."""
    agents_data = {name: agent.to_dict() for name, agent in manager.agents.items()}
    return jsonify(agents_data)

@app.route('/api/agents/<agent_name>')
def get_agent(agent_name):
    """API para obtener un agente específico."""
    if agent_name not in manager.agents:
        return jsonify({"error": "Agente no encontrado"}), 404
    
    return jsonify(manager.agents[agent_name].to_dict())

@app.route('/api/agents/<agent_name>/health')
def check_agent_health_api(agent_name):
    """API para verificar la salud de un agente."""
    result = manager.check_agent_health(agent_name)
    return jsonify(result)

@app.route('/api/agents/check-all')
def check_all_agents_api():
    """API para verificar todos los agentes."""
    results = manager.check_all_agents()
    return jsonify(results)

@app.route('/api/metrics')
def get_metrics():
    """API para obtener métricas agregadas."""
    metrics = manager.get_aggregated_metrics()
    return jsonify(metrics)

@app.route('/api/agents/<agent_name>/restart', methods=['POST'])
def restart_agent(agent_name):
    """API para reiniciar un agente."""
    if agent_name not in manager.agents:
        return jsonify({"error": "Agente no encontrado"}), 404
    
    agent = manager.agents[agent_name]
    
    try:
        if agent.type == "local":
            # Ejecutar comando de reinicio
            result = subprocess.run(
                ["cd", "/workspace/hermes-agent", "&&", "uv", "run", "hermes", "gateway", "restart"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return jsonify({"status": "success", "message": "Agente reiniciado"})
            else:
                return jsonify({"status": "error", "error": result.stderr}), 500
        else:
            return jsonify({"status": "error", "message": "Tipo no implementado"}), 501
            
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/agents/<agent_name>/logs')
def get_agent_logs(agent_name):
    """API para obtener logs de un agente."""
    if agent_name not in manager.agents:
        return jsonify({"error": "Agente no encontrado"}), 404
    
    agent = manager.agents[agent_name]
    
    try:
        # Leer logs recientes del agente
        if agent.type == "local":
            log_file = Path("/home/hermeswebui/.hermes/logs/agent.log")
            if log_file.exists():
                with open(log_file) as f:
                    lines = f.readlines()[-100:]  # Últimas 100 líneas
                return jsonify({"logs": lines})
            else:
                return jsonify({"logs": [], "message": "Archivo de logs no encontrado"})
        elif agent.type == "remote":
            # Obtener logs del connector remoto
            if 'connector_url' in agent.__dict__:
                response = requests.get(
                    f"{agent.connector_url}/logs?lines=100",
                    headers={"X-API-Key": os.getenv('CONNECTOR_API_KEY', 'hermes-secure-key')},
                    timeout=30
                )
                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({"error": "Error al obtener logs remotos"}), 500
            else:
                return jsonify({"error": "Connector URL no configurada"}), 500
        else:
            return jsonify({"error": "Tipo no implementado"}), 501
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Nuevos endpoints para conectores remotos
@app.route('/api/agents/register', methods=['POST'])
def register_agent():
    """API para registrar un nuevo agente remoto."""
    try:
        data = request.json
        
        required_fields = ['name', 'host', 'port', 'connector_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo faltante: {field}"}), 400
        
        # Verificar API key
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('CONNECTOR_API_KEY', 'hermes-secure-key'):
            return jsonify({"error": "Unauthorized"}), 401
        
        # Crear nuevo agente
        new_agent = HermesAgent(
            name=data['name'],
            host=data['host'],
            port=data['port'],
            type=data.get('type', 'remote'),
            status='registered',
            health_score=0,
            last_check=None,
            metrics={},
            alerts=[],
            uptime=0.0,
            total_tokens=0,
            sessions_count=0
        )
        
        # Agregar atributos específicos de conectores
        new_agent.connector_url = data['connector_url']
        new_agent.api_key_validated = True
        
        # Agregar al manager
        manager.agents[data['name']] = new_agent
        
        logger.info(f"✅ Agente remoto registrado: {data['name']}")
        
        return jsonify({
            "status": "success",
            "message": "Agente registrado",
            "agent": new_agent.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error registrando agente: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agents/heartbeat', methods=['POST'])
def receive_heartbeat():
    """API para recibir heartbeat de agentes remotos."""
    try:
        data = request.json
        agent_name = data.get('agent_name')
        health = data.get('health', {})
        
        if not agent_name:
            return jsonify({"error": "Agent name required"}), 400
        
        # Verificar API key
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('CONNECTOR_API_KEY', 'hermes-secure-key'):
            return jsonify({"error": "Unauthorized"}), 401
        
        if agent_name not in manager.agents:
            return jsonify({"error": "Agent not found"}), 404
        
        agent = manager.agents[agent_name]
        
        # Actualizar estado del agente
        agent.status = "healthy"
        agent.health_score = health.get('health_score', 0)
        agent.last_check = data.get('timestamp')
        agent.metrics = health
        
        # Extraer métricas adicionales
        if 'performance_metrics' in health:
            agent.total_tokens = health['performance_metrics'].get('total_tokens', 0)
            agent.sessions_count = health['performance_metrics'].get('total_sessions', 0)
        
        # Calcular uptime (simulado basado en health score)
        agent.uptime = 100.0 if agent.health_score >= 70 else 50.0
        
        # Detectar alertas
        alerts = []
        if agent.health_score < 70:
            alerts.append({"level": "warning", "message": f"Health score bajo: {agent.health_score}"})
        if agent.health_score < 50:
            alerts.append({"level": "critical", "message": f"Health score crítico: {agent.health_score}"})
        
        agent.alerts = alerts
        
        logger.debug(f"❤️  Heartbeat recibido de {agent_name}")
        
        return jsonify({
            "status": "success",
            "message": "Heartbeat received"
        })
        
    except Exception as e:
        logger.error(f"Error en heartbeat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/connectors', methods=['GET'])
def list_connectors():
    """API para listar todos los conectores remotos."""
    try:
        connectors = {}
        for name, agent in manager.agents.items():
            if agent.type == "remote":
                connectors[name] = {
                    "name": agent.name,
                    "host": agent.host,
                    "port": agent.port,
                    "connector_url": getattr(agent, 'connector_url', None),
                    "status": agent.status,
                    "health_score": agent.health_score,
                    "last_heartbeat": agent.last_check,
                    "uptime": agent.uptime
                }
        
        return jsonify({
            "total": len(connectors),
            "connectors": connectors
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Crear directorio de templates
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Crear template HTML básico
    dashboard_html = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hermes Multi-Agent Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        .metric-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .agent-card {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .agent-name {
            font-size: 1.2em;
            font-weight: bold;
        }
        .agent-status {
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .status-healthy {
            background-color: #2ecc71;
            color: white;
        }
        .status-unhealthy {
            background-color: #e74c3c;
            color: white;
        }
        .status-unknown {
            background-color: #f39c12;
            color: white;
        }
        .health-score {
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
        }
        .score-good {
            color: #2ecc71;
        }
        .score-medium {
            color: #f39c12;
        }
        .score-bad {
            color: #e74c3c;
        }
        .agent-details {
            margin-top: 15px;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .alerts {
            margin-top: 15px;
        }
        .alert {
            padding: 5px 10px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .alert-warning {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }
        .alert-critical {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }
        .actions {
            margin-top: 15px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
        }
        .btn-primary {
            background-color: #3498db;
            color: white;
        }
        .btn-danger {
            background-color: #e74c3c;
            color: white;
        }
        .refresh-indicator {
            text-align: center;
            color: #7f8c8d;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🤖 Hermes Multi-Agent Dashboard</h1>
            <p>Administración centralizada de múltiples instancias de Hermes Agent</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value" id="agent-count">0</div>
                <div class="metric-label">Agentes Totales</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="healthy-count" style="color: #2ecc71;">0</div>
                <div class="metric-label">Agentes Saludables</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="unhealthy-count" style="color: #e74c3c;">0</div>
                <div class="metric-label">Agentes Problemáticos</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="avg-health">0</div>
                <div class="metric-label">Health Score Promedio</div>
            </div>
        </div>
        
        <div class="refresh-indicator">
            🔄 Última actualización: <span id="last-update">Cargando...</span>
        </div>
        
        <div class="agents-grid" id="agents-grid">
            <!-- Los agentes se cargarán dinámicamente aquí -->
        </div>
    </div>
    
    <script>
        async function loadMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                document.getElementById('agent-count').textContent = data.agent_count;
                document.getElementById('healthy-count').textContent = data.healthy_count;
                document.getElementById('unhealthy-count').textContent = data.unhealthy_count;
                document.getElementById('avg-health').textContent = data.avg_health_score;
                document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleString();
            } catch (error) {
                console.error('Error al cargar métricas:', error);
            }
        }
        
        async function loadAgents() {
            try {
                const response = await fetch('/api/agents');
                const agents = await response.json();
                
                const grid = document.getElementById('agents-grid');
                grid.innerHTML = '';
                
                for (const [name, agent] of Object.entries(agents)) {
                    const statusClass = agent.health_score >= 70 ? 'status-healthy' : 
                                      agent.health_score >= 50 ? 'status-unknown' : 'status-unhealthy';
                    const scoreClass = agent.health_score >= 70 ? 'score-good' : 
                                     agent.health_score >= 50 ? 'score-medium' : 'score-bad';
                    
                    const alertsHtml = agent.alerts.map(alert => `
                        <div class="alert alert-${alert.level}">
                            <strong>${alert.level.toUpperCase()}:</strong> ${alert.message}
                        </div>
                    `).join('');
                    
                    const card = document.createElement('div');
                    card.className = 'agent-card';
                    card.innerHTML = `
                        <div class="agent-header">
                            <div class="agent-name">${name}</div>
                            <div class="agent-status ${statusClass}">${agent.status}</div>
                        </div>
                        <div class="health-score ${scoreClass}">${agent.health_score}</div>
                        <div class="agent-details">
                            <div class="detail-row">
                                <span>Host:</span>
                                <span>${agent.host}:${agent.port}</span>
                            </div>
                            <div class="detail-row">
                                <span>Tipo:</span>
                                <span>${agent.type}</span>
                            </div>
                            <div class="detail-row">
                                <span>Uptime:</span>
                                <span>${agent.uptime.toFixed(1)}%</span>
                            </div>
                            <div class="detail-row">
                                <span>Tokens:</span>
                                <span>${agent.total_tokens.toLocaleString()}</span>
                            </div>
                            <div class="detail-row">
                                <span>Sesiones:</span>
                                <span>${agent.sessions_count.toLocaleString()}</span>
                            </div>
                            <div class="detail-row">
                                <span>Último check:</span>
                                <span>${agent.last_check ? new Date(agent.last_check).toLocaleString() : 'Nunca'}</span>
                            </div>
                        </div>
                        ${alertsHtml ? `<div class="alerts">${alertsHtml}</div>` : ''}
                        <div class="actions">
                            <button class="btn btn-primary" onclick="checkAgent('${name}')">Verificar</button>
                            <button class="btn btn-danger" onclick="restartAgent('${name}')">Reiniciar</button>
                        </div>
                    `;
                    grid.appendChild(card);
                }
            } catch (error) {
                console.error('Error al cargar agentes:', error);
            }
        }
        
        async function checkAgent(name) {
            try {
                const response = await fetch(`/api/agents/${name}/health`);
                const data = await response.json();
                alert(JSON.stringify(data, null, 2));
                loadAgents(); // Recargar para mostrar cambios
            } catch (error) {
                console.error('Error al verificar agente:', error);
                alert('Error al verificar agente');
            }
        }
        
        async function restartAgent(name) {
            if (!confirm(`¿Estás seguro de que quieres reiniciar ${name}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/agents/${name}/restart`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Agente reiniciado exitosamente');
                    loadAgents(); // Recargar para mostrar cambios
                } else {
                    alert('Error al reiniciar: ' + (data.error || data.message));
                }
            } catch (error) {
                console.error('Error al reiniciar agente:', error);
                alert('Error al reiniciar agente');
            }
        }
        
        // Cargar datos iniciales
        loadMetrics();
        loadAgents();
        
        // Actualizar cada 30 segundos
        setInterval(() => {
            loadMetrics();
            loadAgents();
        }, 30000);
    </script>
</body>
</html>
'''
    
    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(dashboard_html)
    
    # Iniciar el servidor
    logger.info("Iniciando dashboard web en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
