#!/usr/bin/env python3
"""
Hermes Agent Connector - Despliegue Remoto
Este script se ejecuta en cada servidor remoto con Hermes
y se conecta al Dashboard central para monitoreo y gestión

Funcionalidades:
- API de health check local
- Telemetría en tiempo real
- Recepción de comandos remotos
- Seguridad con autenticación
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

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HermesAgentConnector')

app = Flask(__name__)

# Configuración desde variables de entorno
CONNECTOR_PORT = int(os.getenv('CONNECTOR_PORT', '8081'))
DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'http://localhost:5000')
HERMES_HOME = os.path.expanduser(os.getenv('HERMES_HOME', '~/.hermes'))
API_KEY = os.getenv('CONNECTOR_API_KEY', 'hermes-secure-key')

# Información del agente
AGENT_INFO = {
    'name': os.getenv('AGENT_NAME', f"agent-{os.uname().nodename}"),
    'host': os.getenv('AGENT_HOST', os.uname().nodename),
    'port': int(os.getenv('HERMES_PORT', '8080')),
    'type': os.getenv('AGENT_TYPE', 'local'),
    'hermes_home': HERMES_HOME
}

def verify_api_key():
    """Verifica la API key en las requests."""
    api_key = request.headers.get('X-API-Key')
    return api_key == API_KEY

def get_hermes_health() -> Dict:
    """Obtiene información de salud de Hermes local."""
    try:
        # Ejecutar el script de health check
        health_script = Path(HERMES_HOME) / "tools" / "hermes_maintenance_health_check.py"
        
        if health_script.exists():
            result = subprocess.run(
                ["python3", str(health_script)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": f"Health check failed: {result.stderr}"}
        else:
            # Si no existe el script, usar métodos alternativos
            return get_basic_health()
            
    except Exception as e:
        logger.error(f"Error al obtener health: {e}")
        return {"error": str(e), "health_score": 0}

def get_basic_health() -> Dict:
    """Obtiene información básica de salud sin usar scripts."""
    try:
        # Información básica del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Verificar si Hermes está corriendo
        hermes_running = False
        try:
            # Buscar procesos de Hermes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] and 'hermes' in proc.info['name'].lower():
                    hermes_running = True
                    break
        except:
            pass
        
        health_score = 100
        
        # Reducir score basado en recursos
        if cpu_percent > 80:
            health_score -= 20
        if memory.percent > 85:
            health_score -= 20
        if disk.percent > 90:
            health_score -= 10
        if not hermes_running:
            health_score -= 50
        
        health_score = max(0, health_score)
        
        return {
            "health_score": health_score,
            "hermes_dir": HERMES_HOME,
            "resource_usage": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            },
            "status": "running" if hermes_running else "stopped"
        }
        
    except Exception as e:
        logger.error(f"Error en basic health: {e}")
        return {"error": str(e), "health_score": 0}

def register_with_dashboard():
    """Registra este agente con el dashboard central."""
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            # Obtener información de salud
            health = get_hermes_health()
            
            # Preparar datos de registro
            registration_data = {
                "name": AGENT_INFO['name'],
                "host": AGENT_INFO['host'],
                "port": AGENT_INFO['port'],
                "type": AGENT_INFO['type'],
                "connector_url": f"http://{AGENT_INFO['host']}:{CONNECTOR_PORT}",
                "api_key": API_KEY,
                "initial_health": health
            }
            
            # Registrar con el dashboard
            response = requests.post(
                f"{DASHBOARD_URL}/api/agents/register",
                json=registration_data,
                headers={"X-API-Key": API_KEY},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Agente registrado exitosamente en dashboard")
                return True
            else:
                logger.warning(f"⚠️  Error al registrar: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️  Intento {attempt + 1}/{max_retries} falló: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    logger.error("❌ No se pudo registrar con el dashboard")
    return False

def send_heartbeat():
    """Envía heartbeat periódico al dashboard."""
    while True:
        try:
            health = get_hermes_health()
            
            heartbeat_data = {
                "agent_name": AGENT_INFO['name'],
                "health": health,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{DASHBOARD_URL}/api/agents/heartbeat",
                json=heartbeat_data,
                headers={"X-API-Key": API_KEY},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"❤️  Heartbeat enviado")
            else:
                logger.warning(f"⚠️  Heartbeat falló: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️  Error en heartbeat: {e}")
        
        # Enviar heartbeat cada 60 segundos
        time.sleep(60)

# Endpoints del API del connector
@app.route('/health', methods=['GET'])
def get_health():
    """Endpoint para health check del connector."""
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        health = get_hermes_health()
        return jsonify({
            "status": "healthy",
            "agent": AGENT_INFO,
            "hermes_health": health,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Endpoint para obtener información del agente."""
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({
        "agent": AGENT_INFO,
        "connector": {
            "version": "1.0.0",
            "port": CONNECTOR_PORT,
            "dashboard": DASHBOARD_URL
        },
        "system": {
            "hostname": os.uname().nodename,
            "os": os.uname().sysname,
            "kernel": os.uname().release
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/restart', methods=['POST'])
def restart_hermes():
    """Endpoint para reiniciar Hermes remotamente."""
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        logger.info("🔄 Recibiendo comando de reinicio remoto")
        
        # Ejecutar comando de reinicio
        result = subprocess.run(
            ["cd", "/workspace/hermes-agent", "&&", "hermes", "gateway", "restart"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("✅ Hermes reiniciado exitosamente")
            return jsonify({
                "status": "success",
                "message": "Hermes reiniciado",
                "output": result.stdout
            })
        else:
            logger.error(f"❌ Error al reiniciar: {result.stderr}")
            return jsonify({
                "status": "error",
                "error": result.stderr
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Excepción al reiniciar: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/command', methods=['POST'])
def execute_command():
    """Endpoint para ejecutar comandos remotos."""
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.json
        command = data.get('command')
        timeout = data.get('timeout', 30)
        
        if not command:
            return jsonify({"error": "No command provided"}), 400
        
        logger.info(f"🔧 Ejecutando comando remoto: {command}")
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return jsonify({
            "status": "success",
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timeout"}), 408
    except Exception as e:
        logger.error(f"❌ Error ejecutando comando: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Endpoint para obtener logs de Hermes."""
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        lines = request.args.get('lines', 100, type=int)
        log_file = Path(HERMES_HOME) / "logs" / "agent.log"
        
        if not log_file.exists():
            return jsonify({"logs": [], "message": "Log file not found"})
        
        # Leer últimas líneas
        with open(log_file) as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return jsonify({
            "logs": recent_lines,
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo logs: {e}")
        return jsonify({"error": str(e)}), 500

def main():
    """Función principal del connector."""
    logger.info("🚀 Iniciando Hermes Agent Connector")
    logger.info(f"📡 Agente: {AGENT_INFO['name']}")
    logger.info(f"🌐 Dashboard: {DASHBOARD_URL}")
    logger.info(f"🔌 Puerto: {CONNECTOR_PORT}")
    logger.info(f"🏠 Hermes Home: {HERMES_HOME}")
    
    # Registrar con el dashboard
    logger.info("📝 Registrando agente con el dashboard...")
    if register_with_dashboard():
        logger.info("✅ Registro exitoso")
        
        # Iniciar thread de heartbeat
        heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        heartbeat_thread.start()
        logger.info("❤️  Heartbeat iniciado")
    else:
        logger.warning("⚠️  No se pudo registrar, pero el connector seguirá funcionando")
    
    # Iniciar el servidor Flask
    logger.info(f"🌐 Servidor iniciado en puerto {CONNECTOR_PORT}")
    app.run(host='0.0.0.0', port=CONNECTOR_PORT, debug=False)

if __name__ == '__main__':
    main()
