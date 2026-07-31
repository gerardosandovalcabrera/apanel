# 🤖 APanel - Hermes Multi-Agent Management System

Complete multi-agent management system for Hermes with dual interface (human + agent) and professional security.

## 🎯 Key Features

### 🌐 Dual Interface
- **Web Dashboard** for humans (visual and intuitive)
- **MCP Server** for agents (programmatic and automated)
- **Unified backend** with consistent data

### 🐳 Complete Docker Support
- **Central Dashboard** (Flask + Redis + Nginx)
- **Agent Connectors** for remote detection
- **Automated deployment** with scripts

### 🔐 Professional Security
- **OAuth2** (GitHub + Google) for humans
- **JWT + API Keys** for agents
- **RBAC** with 3 roles (admin/operator/viewer)
- **Rate limiting** and complete audit

### 📦 Professional Backup
- **Git versioned** (rollback to any version)
- **Free options** (Google Drive 15GB, GitHub 1GB)
- **Secure** (no secrets in repo)

## 🚀 Quick Start

### Option 1: Local Hybrid System (Recommended for development)

```bash
cd docker
python3 hermes_hybrid_system.py

# Access:
# Humans: http://localhost:5000/
# Agents: http://localhost:5000/mcp/
# Auth: http://localhost:5000/auth/
```

### Option 2: Complete Docker System (Production)

```bash
cd docker
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Dashboard: http://localhost:5000/
```

### Option 3: Quick Backup

```bash
# Local backup
./backup-hermes.sh

# Backup to Google Drive
./backup-gdrive.sh

# Secure backup to GitHub
export GITHUB_TOKEN='***'
./backup-github-safe.sh
```

## 📁 Project Structure

```
apanel/
├── docker/                          # Complete Docker system
│   ├── Dockerfile.dashboard         # Dashboard image
│   ├── Dockerfile.connector         # Connector image
│   ├── docker-compose.yml           # Dashboard orchestration
│   ├── docker-compose.connector.yml # Connector orchestration
│   ├── deploy-hermes-docker.sh     # Deployment script
│   ├── nginx/                      # Nginx configuration
│   ├── hermes_hybrid_system.py     # ⭐ Main system
│   ├── hermes_security.py          # ⭐ Security system
│   ├── hermes_auth_endpoints.py    # ⭐ Auth endpoints
│   └── SECURITY_ANALYSIS.md        # ⭐ Security analysis
│
├── backup-hermes.sh                # Complete backup
├── backup-github-safe.sh            # Secure backup to GitHub
├── restore-hermes.sh               # Restoration
├── BACKUP-GRATIS.md                # Free backup guide
└── README.md                       # This file
```

## 🔐 Security Configuration

### Required Environment Variables

```bash
# OAuth2 (Create apps on GitHub and Google)
export OAUTH_GITHUB_CLIENT_ID='***'
export OAUTH_GITHUB_CLIENT_SECRET='***'
export OAUTH_GOOGLE_CLIENT_ID='***'
export OAUTH_GOOGLE_CLIENT_SECRET='***'

# Security
export JWT_SECRET_KEY='***'  # Generate with: openssl rand -hex 32
export ENCRYPTION_KEY='***'  # Generate with: openssl rand -hex 32

# Redis
export REDIS_HOST='localhost'
export REDIS_PORT='6379'
```

### Create OAuth Apps

1. **GitHub OAuth**:
   - Go to https://github.com/settings/developers
   - Create "New OAuth App"
   - Authorization callback: `http://localhost:5000/auth/github/callback`
   - Copy Client ID and Secret

2. **Google OAuth**:
   - Go to https://console.cloud.google.com/
   - Create "OAuth 2.0 Client IDs"
   - Authorized redirect: `http://localhost:5000/auth/google/callback`
   - Copy Client ID and Secret

## 📊 Main Endpoints

### For Humans (Web Dashboard)
```
GET  /                    → Web Dashboard
GET  /api/agents          → List of agents
GET  /api/metrics         → Aggregated metrics
GET  /api/health          → Health check
GET  /docs                → Complete documentation
```

### For Agents (MCP Server)
```
GET  /mcp/tools           → List of tools (10 available)
GET  /mcp/resources       → List of resources (4 available)
POST /mcp/call            → Execute tool
GET  /mcp/resource/<uri>  → Get resource
```

### For Both (Authentication)
```
GET  /auth/providers      → Configured OAuth providers
GET  /auth/github         → Login with GitHub
GET  /auth/google         → Login with Google
POST /auth/refresh        → Refresh token
POST /auth/logout         → Logout
GET  /auth/me             → Current user info
```

## 🤖 Available MCP Tools

1. `list_agents` - List agents with filters
2. `get_agent_health` - Get agent health status
3. `get_system_metrics` - Aggregated metrics
4. `restart_agent` - Restart an agent
5. `get_agent_logs` - Get agent logs
6. `execute_agent_command` - Execute remote commands
7. `register_remote_agent` - Register new agent
8. `get_system_alerts` - Get active alerts
9. `get_agent_performance` - Performance metrics
10. `check_all_agents` - Health check of all agents

## 🛡️ Implemented Security

### 6 Layers of Defense
1. **Network Perimeter** - Firewall, VPN, Fail2Ban
2. **Authentication** - OAuth2, JWT, API Keys, RBAC, MFA
3. **Communication** - HTTPS TLS 1.3, Secure headers
4. **Application** - Rate limiting, Input validation, CSRF
5. **Data** - AES-256, Secrets manager, Rotation
6. **Monitoring** - Logs, Alerts, Incident response

### Security Features
- ✅ OAuth2 with GitHub and Google
- ✅ JWT with Access and Refresh tokens
- ✅ Rotating API Keys for agents
- ✅ RBAC (admin/operator/viewer)
- ✅ Rate limiting (Redis-based)
- ✅ Complete audit
- ✅ MFA ready to implement

## 📈 System Usage

### For Humans
1. Access `http://localhost:5000/`
2. Authenticate with GitHub or Google
3. View dashboard with all agents
4. Interact with action buttons
5. Monitor real-time metrics

### For Agents
```python
import requests

# List problematic agents
response = requests.post("http://localhost:5000/mcp/call", json={
    "tool": "list_agents",
    "arguments": {"filter": "unhealthy"}
})

# Get system metrics
metrics = requests.post("http://localhost:5000/mcp/call", json={
    "tool": "get_system_metrics",
    "arguments": {"include_agents": True}
})

# The agent analyzes and makes decisions automatically
```

## 🚀 Production Deployment

### Requirements
- Docker 20.10+
- Docker Compose 2.0+
- 2 GB RAM minimum
- 10 GB disk minimum
- Own domain (for HTTPS)

### Steps
1. **Configure environment variables**
2. **Create OAuth Apps** (GitHub + Google)
3. **Run deployment script**
4. **Configure HTTPS** with Let's Encrypt
5. **Configure firewall**
6. **Monitor logs**

## 📋 TODO

- [ ] Implement MFA for administrators
- [ ] Configure HTTPS with Let's Encrypt
- [ ] Implement security tests
- [ ] Add more OAuth providers
- [ ] Create monitoring dashboard
- [ ] Implement email/Slack alerts

## 🤝 Contributing

This project is in active development. Contributions are welcome.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Hermes Agent - Base platform
- Flask - Web framework
- Docker - Containers
- Redis - Cache and queues

## 📞 Support

For issues or questions:
- Review documentation in `/docs`
- Check logs in Docker container
- Review security analysis in `docker/SECURITY_ANALYSIS.md`

---

**Version:** 1.0.0
**Status:** Alpha - Active development
**Last updated:** 2025-07-31
