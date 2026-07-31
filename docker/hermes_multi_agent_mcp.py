"""
Hermes Multi-Agent Management MCP Server
Exponiendo funcionalidades del dashboard de administración multi-agente
a través del protocolo MCP (Model Context Protocol)

Permite que otros agentes monitoreen y controlen el sistema de agentes Hermes
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict
import asyncio
from pathlib import Path

# MCP imports (simulados para este ejemplo, en producción usaría mcp lib)
import subprocess
import yaml

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HermesMCP')

class HermesMultiAgentMCP:
    """Servidor MCP para gestión multi-agente de Hermes."""
    
    def __init__(self, dashboard_url: str = "http://localhost:5000"):
        self.dashboard_url = dashboard_url
        self.manager = None  # Se inicializa cuando se carga
        self.tools = self._register_tools()
        self.resources = self._register_resources()
        
    def _register_tools(self) -> Dict[str, Dict]:
        """Registra todas las herramientas MCP disponibles."""
        return {
            "list_agents": {
                "name": "list_agents",
                "description": "Lista todos los agentes de Hermes registrados en el sistema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "Filtro opcional (local/remote/healthy/unhealthy)",
                            "enum": ["local", "remote", "healthy", "unhealthy"]
                        }
                    }
                }
            },
            "get_agent_health": {
                "name": "get_agent_health",
                "description": "Obtiene el estado de salud de un agente específico",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Nombre del agente a consultar"
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "Incluir métricas detalladas",
                            "default": False
                        }
                    },
                    "required": ["agent_name"]
                }
            },
            "get_system_metrics": {
                "name": "get_system_metrics",
                "description": "Obtiene métricas agregadas de todo el sistema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_agents": {
                            "type": "boolean",
                            "description": "Incluir información de agentes individuales",
                            "default": False
                        }
                    }
                }
            },
            "restart_agent": {
                "name": "restart_agent",
                "description": "Reinicia un agente de Hermes específico",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Nombre del agente a reiniciar"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Forzar reinicio sin confirmación",
                            "default": False
                        }
                    },
                    "required": ["agent_name"]
                }
            },
            "get_agent_logs": {
                "name": "get_agent_logs",
                "description": "Obtiene los logs recientes de un agente",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Nombre del agente"
                        },
                        "lines": {
                            "type": "integer",
                            "description": "Número de líneas a obtener",
                            "default": 100,
                            "minimum": 10,
                            "maximum": 1000
                        },
                        "filter": {
                            "type": "string",
                            "description": "Filtro de logs (error/warning/info)",
                            "enum": ["error", "warning", "info"]
                        }
                    },
                    "required": ["agent_name"]
                }
            },
            "execute_agent_command": {
                "name": "execute_agent_command",
                "description": "Ejecuta un comando en un agente remoto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Nombre del agente"
                        },
                        "command": {
                            "type": "string",
                            "description": "Comando a ejecutar"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout en segundos",
                            "default": 30
                        }
                    },
                    "required": ["agent_name", "command"]
                }
            },
            "register_remote_agent": {
                "name": "register_remote_agent",
                "description": "Registra un nuevo agente remoto en el sistema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre único del agente"
                        },
                        "host": {
                            "type": "string",
                            "description": "Host del agente (IP o dominio)"
                        },
                        "port": {
                            "type": "integer",
                            "description": "Puerto del agente",
                            "default": 8080
                        },
                        "type": {
                            "type": "string",
                            "description": "Tipo de agente",
                            "enum": ["remote", "ssh", "docker"],
                            "default": "remote"
                        },
                        "connector_url": {
                            "type": "string",
                            "description": "URL del connector del agente"
                        }
                    },
                    "required": ["name", "host", "connector_url"]
                }
            },
            "get_system_alerts": {
                "name": "get_system_alerts",
                "description": "Obtiene todas las alertas activas del sistema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "description": "Filtro por severidad",
                            "enum": ["critical", "warning", "info"],
                            "default": "warning"
                        }
                    }
                }
            },
            "get_agent_performance": {
                "name": "get_agent_performance",
                "description": "Obtiene métricas de rendimiento de un agente",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Nombre del agente"
                        },
                        "period": {
                            "type": "string",
                            "description": "Período de tiempo",
                            "enum": ["hour", "day", "week"],
                            "default": "hour"
                        }
                    },
                    "required": ["agent_name"]
                }
            },
            "check_all_agents": {
                "name": "check_all_agents",
                "description": "Ejecuta health check en todos los agentes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "parallel": {
                            "type": "boolean",
                            "description": "Ejecutar en paralelo",
                            "default": True
                        }
                    }
                }
            }
        }
    
    def _register_resources(self) -> Dict[str, Dict]:
        """Registra recursos MCP disponibles."""
        return {
            "agents_list": {
                "uri": "hermes://agents",
                "name": "Lista de Agentes",
                "description": "Lista completa de todos los agentes registrados",
                "mime_type": "application/json"
            },
            "system_health": {
                "uri": "hermes://health",
                "name": "Salud del Sistema",
                "description": "Estado de salud agregado de todo el sistema",
                "mime_type": "application/json"
            },
            "active_alerts": {
                "uri": "hermes://alerts",
                "name": "Alertas Activas",
                "description": "Todas las alertas activas en el sistema",
                "mime_type": "application/json"
            },
            "system_metrics": {
                "uri": "hermes://metrics",
                "name": "Métricas del Sistema",
                "description": "Métricas de rendimiento del sistema completo",
                "mime_type": "application/json"
            }
        }
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Maneja llamadas a herramientas MCP."""
        try:
            logger.info(f"MCP Tool Call: {tool_name} with args: {arguments}")
            
            # Importar el manager aquí para evitar circular dependency
            from hermes_multi_agent_dashboard import HermesMultiAgentManager
            
            if self.manager is None:
                self.manager = HermesMultiAgentManager()
            
            if tool_name == "list_agents":
                return await self._list_agents(arguments)
            elif tool_name == "get_agent_health":
                return await self._get_agent_health(arguments)
            elif tool_name == "get_system_metrics":
                return await self._get_system_metrics(arguments)
            elif tool_name == "restart_agent":
                return await self._restart_agent(arguments)
            elif tool_name == "get_agent_logs":
                return await self._get_agent_logs(arguments)
            elif tool_name == "execute_agent_command":
                return await self._execute_agent_command(arguments)
            elif tool_name == "register_remote_agent":
                return await self._register_remote_agent(arguments)
            elif tool_name == "get_system_alerts":
                return await self._get_system_alerts(arguments)
            elif tool_name == "get_agent_performance":
                return await self._get_agent_performance(arguments)
            elif tool_name == "check_all_agents":
                return await self._check_all_agents(arguments)
            else:
                return {
                    "success": False,
                    "error": f"Tool not found: {tool_name}"
                }
                
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_agents(self, args: Dict) -> Dict:
        """Lista todos los agentes con filtros opcionales."""
        filter_type = args.get('filter')
        
        agents = {}
        for name, agent in self.manager.agents.items():
            if filter_type:
                if filter_type == "local" and agent.type != "local":
                    continue
                elif filter_type == "remote" and agent.type != "remote":
                    continue
                elif filter_type == "healthy" and agent.health_score < 70:
                    continue
                elif filter_type == "unhealthy" and agent.health_score >= 70:
                    continue
            
            agents[name] = {
                "name": agent.name,
                "host": agent.host,
                "port": agent.port,
                "type": agent.type,
                "status": agent.status,
                "health_score": agent.health_score,
                "uptime": agent.uptime,
                "last_check": agent.last_check,
                "alert_count": len(agent.alerts)
            }
        
        return {
            "success": True,
            "data": {
                "total": len(agents),
                "filter": filter_type,
                "agents": agents
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_agent_health(self, args: Dict) -> Dict:
        """Obtiene el estado de salud de un agente."""
        agent_name = args.get('agent_name')
        detailed = args.get('detailed', False)
        
        if agent_name not in self.manager.agents:
            return {
                "success": False,
                "error": f"Agent not found: {agent_name}"
            }
        
        agent = self.manager.agents[agent_name]
        
        result = {
            "success": True,
            "data": {
                "name": agent.name,
                "status": agent.status,
                "health_score": agent.health_score,
                "uptime": agent.uptime,
                "last_check": agent.last_check,
                "alerts": agent.alerts
            }
        }
        
        if detailed:
            result["data"]["metrics"] = agent.metrics
            result["data"]["total_tokens"] = agent.total_tokens
            result["data"]["sessions_count"] = agent.sessions_count
        
        return result
    
    async def _get_system_metrics(self, args: Dict) -> Dict:
        """Obtiene métricas del sistema."""
        include_agents = args.get('include_agents', False)
        
        metrics = self.manager.get_aggregated_metrics()
        
        result = {
            "success": True,
            "data": metrics
        }
        
        if include_agents:
            result["data"]["agents"] = {}
            for name, agent in self.manager.agents.items():
                result["data"]["agents"][name] = {
                    "health_score": agent.health_score,
                    "status": agent.status,
                    "uptime": agent.uptime
                }
        
        return result
    
    async def _restart_agent(self, args: Dict) -> Dict:
        """Reinicia un agente."""
        agent_name = args.get('agent_name')
        force = args.get('force', False)
        
        if agent_name not in self.manager.agents:
            return {
                "success": False,
                "error": f"Agent not found: {agent_name}"
            }
        
        if not force:
            return {
                "success": False,
                "error": "Restart requires confirmation. Set force=true to proceed."
            }
        
        # Ejecutar reinicio
        result = self.manager.check_agent_health(agent_name)
        
        # En una implementación real, aquí se ejecutaría el reinicio
        return {
            "success": True,
            "data": {
                "agent_name": agent_name,
                "message": "Restart command sent",
                "result": result
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_agent_logs(self, args: Dict) -> Dict:
        """Obtiene logs de un agente."""
        agent_name = args.get('agent_name')
        lines = args.get('lines', 100)
        filter_type = args.get('filter')
        
        if agent_name not in self.manager.agents:
            return {
                "success": False,
                "error": f"Agent not found: {agent_name}"
            }
        
        # Simular obtención de logs
        logs = [
            f"[INFO] {datetime.now().isoformat()} - Agent {agent_name} is running",
            f"[INFO] {datetime.now().isoformat()} - Health score: 85",
            f"[WARNING] {datetime.now().isoformat()} - High memory usage: 75%"
        ]
        
        if filter_type:
            logs = [log for log in logs if filter_type.upper() in log]
        
        return {
            "success": True,
            "data": {
                "agent_name": agent_name,
                "lines": lines,
                "filter": filter_type,
                "logs": logs[:lines]
            }
        }
    
    async def _execute_agent_command(self, args: Dict) -> Dict:
        """Ejecuta un comando en un agente."""
        agent_name = args.get('agent_name')
        command = args.get('command')
        timeout = args.get('timeout', 30)
        
        if agent_name not in self.manager.agents:
            return {
                "success": False,
                "error": f"Agent not found: {agent_name}"
            }
        
        # Simular ejecución de comando
        return {
            "success": True,
            "data": {
                "agent_name": agent_name,
                "command": command,
                "timeout": timeout,
                "output": f"Command '{command}' executed on {agent_name}",
                "exit_code": 0
            }
        }
    
    async def _register_remote_agent(self, args: Dict) -> Dict:
        """Registra un agente remoto."""
        name = args.get('name')
        host = args.get('host')
        port = args.get('port', 8080)
        agent_type = args.get('type', 'remote')
        connector_url = args.get('connector_url')
        
        if not all([name, host, connector_url]):
            return {
                "success": False,
                "error": "Missing required fields: name, host, connector_url"
            }
        
        if name in self.manager.agents:
            return {
                "success": False,
                "error": f"Agent already exists: {name}"
            }
        
        # Registrar el agente
        # En implementación real, se llamaría a la API del dashboard
        return {
            "success": True,
            "data": {
                "name": name,
                "host": host,
                "port": port,
                "type": agent_type,
                "connector_url": connector_url,
                "message": "Agent registered successfully"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_system_alerts(self, args: Dict) -> Dict:
        """Obtiene alertas del sistema."""
        severity = args.get('severity', 'warning')
        
        all_alerts = []
        for name, agent in self.manager.agents.items():
            for alert in agent.alerts:
                if severity == 'info' or alert['level'] == severity:
                    all_alerts.append({
                        "agent": name,
                        **alert
                    })
        
        return {
            "success": True,
            "data": {
                "total": len(all_alerts),
                "severity_filter": severity,
                "alerts": all_alerts
            }
        }
    
    async def _get_agent_performance(self, args: Dict) -> Dict:
        """Obtiene métricas de rendimiento."""
        agent_name = args.get('agent_name')
        period = args.get('period', 'hour')
        
        if agent_name not in self.manager.agents:
            return {
                "success": False,
                "error": f"Agent not found: {agent_name}"
            }
        
        agent = self.manager.agents[agent_name]
        
        # Simular datos de rendimiento
        performance_data = {
            "tokens_per_hour": agent.total_tokens if period == "hour" else agent.total_tokens * 24,
            "sessions_per_hour": agent.sessions_count if period == "hour" else agent.sessions_count * 24,
            "avg_response_time": 1.2,  # segundos
            "error_rate": 0.02,  # 2%
            "success_rate": 0.98  # 98%
        }
        
        return {
            "success": True,
            "data": {
                "agent_name": agent_name,
                "period": period,
                "performance": performance_data
            }
        }
    
    async def _check_all_agents(self, args: Dict) -> Dict:
        """Ejecuta health check en todos los agentes."""
        parallel = args.get('parallel', True)
        
        results = {}
        for name in self.manager.agents:
            result = self.manager.check_agent_health(name)
            results[name] = {
                "success": result.get("status") == "success",
                "health_score": result.get("agent", {}).get("health_score", 0),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "data": {
                "total_agents": len(results),
                "healthy_count": sum(1 for r in results.values() if r["health_score"] >= 70),
                "unhealthy_count": sum(1 for r in results.values() if r["health_score"] < 70),
                "results": results
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def get_tools_list(self) -> List[Dict]:
        """Devuelve la lista de herramientas disponibles."""
        return [
            {
                "name": name,
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            for name, tool in self.tools.items()
        ]
    
    def get_resources_list(self) -> List[Dict]:
        """Devuelve la lista de recursos disponibles."""
        return [
            {
                "uri": resource["uri"],
                "name": resource["name"],
                "description": resource["description"],
                "mime_type": resource["mime_type"]
            }
            for uri, resource in self.resources.items()
        ]

# Función principal para el servidor MCP
async def run_mcp_server():
    """Ejecuta el servidor MCP."""
    mcp_server = HermesMultiAgentMCP()
    
    print("🤖 Hermes Multi-Agent MCP Server iniciado")
    print("📋 Herramientas disponibles:")
    for tool in mcp_server.get_tools_list():
        print(f"  • {tool['name']}: {tool['description']}")
    
    print("\n📚 Recursos disponibles:")
    for resource in mcp_server.get_resources_list():
        print(f"  • {resource['uri']}: {resource['name']}")
    
    print("\n🚀 Servidor MCP listo para recibir comandos...")
    
    # Aquí se implementaría el servidor MCP real
    # Por ahora, simulamos estar escuchando
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_mcp_server())
