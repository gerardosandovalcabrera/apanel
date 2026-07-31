# 🤖 APanel - Hermes Multi-Agent Management System

Sistema completo de administración multi-agente de Hermes con interfaz dual (humano + agente) y seguridad profesional.

## 🎯 Características Principales

### 🌐 Interfaz Dual
- **Dashboard Web** para humanos (visual e intuitivo)
- **MCP Server** para agentes (programático y automatizado)
- **Backend unificado** con datos consistentes

### 🐳 Soporte Docker Completo
- **Dashboard Central** (Flask + Redis + Nginx)
- **Agent Connectors** para detección remota
- **Deployment automatizado** con scripts

### 🔐 Seguridad Profesional
- **OAuth2** (GitHub + Google) para humanos
- **JWT + API Keys** para agentes
- **RBAC** con 3 roles (admin/operator/viewer)
- **Rate limiting** y auditoría completa

### 📦 Backup Profesional
- **Git versionado** (rollback a cualquier versión)
- **Opciones gratuitas** (Google Drive 15GB, GitHub 1GB)
- **Seguro** (sin secrets en el repo)

## 🚀 Quick Start

### Opción 1: Sistema Híbrido Local (Recomendado para desarrollo)

```bash
cd docker
python3 hermes_hybrid_system.py

# Acceder:
# Humanos: http://localhost:5000/
# Agentes: http://localhost:5000/mcp/
# Auth: http://localhost:5000/auth/
```

### Opción 2: Sistema Docker Completo (Producción)

```bash
cd docker
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Dashboard: http://localhost:5000/
```

### Opción 3: Backup Rápido

```bash
# Backup local
./backup-hermes.sh

# Backup a Google Drive
./backup-gdrive.sh

# Backup seguro a GitHub
export GITHUB_TOKEN='***'
./backup-github-safe.sh
```

## 📁 Estructura del Proyecto

```
apanel/
├── docker/                          # Sistema Docker completo
│   ├── Dockerfile.dashboard         # Imagen del Dashboard
│   ├── Dockerfile.connector         # Imagen del Connector
│   ├── docker-compose.yml           # Orquestación Dashboard
│   ├── docker-compose.connector.yml # Orquestación Connector
│   ├── deploy-hermes-docker.sh     # Script de deployment
│   ├── nginx/                      # Configuración Nginx
│   ├── hermes_hybrid_system.py     # ⭐ Sistema principal
│   ├── hermes_security.py          # ⭐ Sistema de seguridad
│   ├── hermes_auth_endpoints.py    # ⭐ Endpoints de auth
│   └── SECURITY_ANALYSIS.md        # ⭐ Análisis de seguridad
│
├── backup-hermes.sh                # Backup completo
├── backup-github-safe.sh            # Backup seguro a GitHub
├── restore-hermes.sh               # Restauración
├── BACKUP-GRATIS.md                # Guía de backup gratuito
└── README.md                       # Este archivo
```

## 🔐 Configuración de Seguridad

### Variables de Entorno Requeridas

```bash
# OAuth2 (Crear apps en GitHub y Google)
export OAUTH_GITHUB_CLIENT_ID='***'
export OAUTH_GITHUB_CLIENT_SECRET='***'
export OAUTH_GOOGLE_CLIENT_ID='***'
export OAUTH_GOOGLE_CLIENT_SECRET='***'

# Seguridad
export JWT_SECRET_KEY='***'  # Generar con: openssl rand -hex 32
export ENCRYPTION_KEY='***'  # Generar con: openssl rand -hex 32

# Redis
export REDIS_HOST='localhost'
export REDIS_PORT='6379'
```

### Crear OAuth Apps

1. **GitHub OAuth**:
   - Ve a https://github.com/settings/developers
   - Crea "New OAuth App"
   - Authorization callback: `http://localhost:5000/auth/github/callback`
   - Copia Client ID y Secret

2. **Google OAuth**:
   - Ve a https://console.cloud.google.com/
   - Crea "OAuth 2.0 Client IDs"
   - Authorized redirect: `http://localhost:5000/auth/google/callback`
   - Copia Client ID y Secret

## 📊 Endpoints Principales

### Para Humanos (Dashboard Web)
```
GET  /                    → Dashboard Web
GET  /api/agents          → Lista de agentes
GET  /api/metrics         → Métricas agregadas
GET  /api/health          → Health check
GET  /docs                → Documentación completa
```

### Para Agentes (MCP Server)
```
GET  /mcp/tools           → Lista de herramientas (10 disponibles)
GET  /mcp/resources       → Lista de recursos (4 disponibles)
POST /mcp/call            → Ejecutar herramienta
GET  /mcp/resource/<uri>  → Obtener recurso
```

### Para Ambos (Autenticación)
```
GET  /auth/providers      → Proveedores OAuth configurados
GET  /auth/github         → Login con GitHub
GET  /auth/google         → Login con Google
POST /auth/refresh        → Refrescar token
POST /auth/logout         → Cerrar sesión
GET  /auth/me             → Info del usuario actual
```

## 🤖 Herramientas MCP Disponibles

1. `list_agents` - Listar agentes con filtros
2. `get_agent_health` - Obtener salud de un agente
3. `get_system_metrics` - Métricas agregadas
4. `restart_agent` - Reiniciar un agente
5. `get_agent_logs` - Obtener logs de un agente
6. `execute_agent_command` - Ejecutar comandos remotos
7. `register_remote_agent` - Registrar nuevo agente
8. `get_system_alerts` - Obtener alertas activas
9. `get_agent_performance` - Métricas de rendimiento
10. `check_all_agents` - Health check de todos

## 🛡️ Seguridad Implementada

### 6 Capas de Defensa
1. **Perímetro de Red** - Firewall, VPN, Fail2Ban
2. **Autenticación** - OAuth2, JWT, API Keys, RBAC, MFA
3. **Comunicación** - HTTPS TLS 1.3, Headers seguros
4. **Aplicación** - Rate limiting, Input validation, CSRF
5. **Datos** - AES-256, Secrets manager, Rotación
6. **Monitoreo** - Logs, Alertas, Incident response

### Características de Seguridad
- ✅ OAuth2 con GitHub y Google
- ✅ JWT con Access y Refresh tokens
- ✅ API Keys rotativas para agentes
- ✅ RBAC (admin/operator/viewer)
- ✅ Rate limiting (Redis-based)
- ✅ Auditoría completa
- ✅ MFA listo para implementar

## 📈 Uso del Sistema

### Para Humanos
1. Acceder a `http://localhost:5000/`
2. Autenticarse con GitHub o Google
3. Ver el dashboard con todos los agentes
4. Interactuar con botones de acción
5. Monitorear métricas en tiempo real

### Para Agentes
```python
import requests

# Listar agentes problemáticos
response = requests.post("http://localhost:5000/mcp/call", json={
    "tool": "list_agents",
    "arguments": {"filter": "unhealthy"}
})

# Obtener métricas del sistema
metrics = requests.post("http://localhost:5000/mcp/call", json={
    "tool": "get_system_metrics",
    "arguments": {"include_agents": true}
})

# El agente analiza y toma decisiones automáticamente
```

## 🚀 Deployment en Producción

### Requisitos
- Docker 20.10+
- Docker Compose 2.0+
- 2 GB RAM mínimo
- 10 GB disco mínimo
- Dominio propio (para HTTPS)

### Pasos
1. **Configurar variables de entorno**
2. **Crear OAuth Apps** (GitHub + Google)
3. **Ejecutar script de deployment**
4. **Configurar HTTPS** con Let's Encrypt
5. **Configurar firewall**
6. **Monitorear logs**

## 📋 TODO

- [ ] Implementar MFA para administradores
- [ ] Configurar HTTPS con Let's Encrypt
- [ ] Implementar tests de seguridad
- [ ] Agregar más proveedores OAuth
- [ ] Crear dashboard de monitoreo
- [ ] Implementar alertas por email/Slack

## 🤝 Contribuir

Este proyecto está en desarrollo activo. Las contribuciones son bienvenidas.

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles

## 🙏 Agradecimientos

- Hermes Agent - Plataforma base
- Flask - Framework web
- Docker - Contenedores
- Redis - Caché y colas

## 📞 Soporte

Para problemas o preguntas:
- Revisar la documentación en `/docs`
- Ver logs en el contenedor Docker
- Revisar el análisis de seguridad en `docker/SECURITY_ANALYSIS.md`

---

**Versión:** 1.0.0  
**Estado:** Alpha - En desarrollo activo  
**Última actualización:** 2025-07-31
