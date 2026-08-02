"""
Hermes Multi-Agent Management MCP Server
Exposing multi-agent management dashboard functionality
through the MCP (Model Context Protocol)

Allows other agents to monitor and control the Hermes agent system
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict
import asyncio
from pathlib import Path

# MCP imports (simulated for this example, in production would use mcp lib)
import subprocess
import yaml

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('HermesMCP')

class HermesMultiAgentMCP:
    """MCP server for Hermes multi-agent management."""
    
    def __init__(self, dashboard_url: str = "http://localhost:5000"):
        self.dashboard_url = dashboard_url
        self.manager = None  # Initialized when loaded
        self.tools = self._register_tools()
        self.resources = self._register_resources()
        
    def _register_tools(self) -> Dict[str, Dict]:
        """Register all available MCP tools."""
        return {
            "list_agents": {
                "name": "list_agents",
                "description": "List all Hermes agents registered in the system",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "Optional filter (local/remote/healthy/unhealthy)",
                            "enum": ["local", "remote", "healthy", "unhealthy"]
                        }
                    }
                }
            },
            "get_agent_health": {
                "name": "get_agent_health",
                "description": "Get health status of a specific agent",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent to query"
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "Include detailed metrics",
                            "default": False
                        }
                    },
                    "required": ["agent_name"]
                }
            },
            "get_system_metrics": {
                "name": "get_system_metrics",
                "description": "Get aggregated metrics for the entire system",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_agents": {
                            "type": "boolean",
                            "description": "Include individual agent information",
                            "default": False
                        }
                    }
                }
            },
            "restart_agent": {
                "name": "restart_agent",
                "description": "Restart a specific agent",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent to restart"
                        }
                    },
                    "required": ["agent_name"]
                }
            }
        }
    
    def _register_resources(self) -> Dict[str, Dict]:
        """Register all available MCP resources."""
        return {
            "billing": {
                "uri": "apanel://billing",
                "name": "Billing Information",
                "description": "Current billing and cost information",
                "mime_type": "application/json"
            },
            "agents": {
                "uri": "apanel://agents",
                "name": "Agent List",
                "description": "List of all agents with their status",
                "mime_type": "application/json"
            },
            "plans": {
                "uri": "apanel://plans",
                "name": "Plans and Limits",
                "description": "Current plan and usage limits",
                "mime_type": "application/json"
            }
        }
    
    def get_tools_list(self) -> List[Dict]:
        """Get list of all available tools."""
        return list(self.tools.values())
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle a tool call from MCP client."""
        try:
            if tool_name == "list_agents":
                return await self._list_agents(arguments)
            elif tool_name == "get_agent_health":
                return await self._get_agent_health(arguments)
            elif tool_name == "get_system_metrics":
                return await self._get_system_metrics(arguments)
            elif tool_name == "restart_agent":
                return await self._restart_agent(arguments)
            else:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_agents(self, args: Dict) -> Dict:
        """List all agents with optional filtering."""
        if not self.manager:
            return {
                "success": False,
                "error": "Manager not initialized"
            }
        
        agents = self.manager.agents
        filter_type = args.get("filter")
        
        if filter_type:
            if filter_type == "healthy":
                agents = {k: v for k, v in agents.items() if v.status == "healthy"}
            elif filter_type == "unhealthy":
                agents = {k: v for k, v in agents.items() if v.status != "healthy"}
            elif filter_type == "local":
                agents = {k: v for k, v in agents.items() if v.type == "local"}
            elif filter_type == "remote":
                agents = {k: v for k, v in agents.items() if v.type != "local"}
        
        return {
            "success": True,
            "agents": {name: agent.to_dict() for name, agent in agents.items()},
            "count": len(agents),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_agent_health(self, args: Dict) -> Dict:
        """Get health status for a specific agent."""
        if not self.manager:
            return {
                "success": False,
                "error": "Manager not initialized"
            }
        
        agent_name = args.get("agent_name")
        detailed = args.get("detailed", False)
        
        agent = self.manager.agents.get(agent_name)
        if not agent:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found"
            }
        
        result = self.manager.check_agent_health(agent_name)
        
        if detailed and result.get("success"):
            agent_data = result["agent"]
            agent_data["detailed_metrics"] = agent.metrics
            agent_data["alerts"] = agent.alerts
            agent_data["uptime_percentage"] = agent.uptime
        
        return {
            "success": result.get("success", False),
            "data": result.get("agent") if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None
        }
    
    async def _get_system_metrics(self, args: Dict) -> Dict:
        """Get aggregated system metrics."""
        if not self.manager:
            return {
                "success": False,
                "error": "Manager not initialized"
            }
        
        metrics = self.manager.get_aggregated_metrics()
        
        if args.get("include_agents"):
            metrics["agents"] = {name: agent.to_dict() for name, agent in self.manager.agents.items()}
        
        return {
            "success": True,
            "metrics": metrics
        }
    
    async def _restart_agent(self, args: Dict) -> Dict:
        """Restart a specific agent."""
        if not self.manager:
            return {
                "success": False,
                "error": "Manager not initialized"
            }
        
        agent_name = args.get("agent_name")
        
        # In a real implementation, this would call the actual restart method
        # For now, simulate the restart
        logger.info(f"Restarting agent: {agent_name}")
        
        return {
            "success": True,
            "message": f"Agent '{agent_name}' restarted successfully",
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Simple test of MCP server
    mcp = HermesMultiAgentMCP()
    
    logger.info("=" * 60)
    logger.info("🔌 Hermes Multi-Agent MCP Server")
    logger.info("=" * 60)
    
    logger.info("\n🛠️  Available Tools:")
    for tool_name, tool_info in mcp.tools.items():
        logger.info(f"   • {tool_name}: {tool_info['description']}")
    
    logger.info("\n📚 Available Resources:")
    for resource_name, resource_info in mcp.resources.items():
        logger.info(f"   • {resource_name}: {resource_info['description']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 MCP Server ready!")
    logger.info("=" * 60)
