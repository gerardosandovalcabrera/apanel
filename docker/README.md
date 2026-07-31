# 🐳 Hermes Multi-Agent Docker System

Complete Hermes multi-agent management system based on Docker for deployment across multiple locations.

## 🏛️ Architecture

```
🌐 Central Dashboard (Your main server)
├── Docker Container: hermes-dashboard
│   ├── Flask Web Dashboard (port 5000)
│   ├── Redis for cache (port 6379)
│   └── Nginx Reverse Proxy (port 80/443)
│
🔗 Remote Agents (Other servers with Hermes)
├── Docker Container: hermes-connector (on each server)
│   ├── Health check API (port 8081)
│   ├── Real-time telemetry
│   ├── Remote commands
│   └── Authentication with API Key
│
🌐 Docker Network
├── Secure communication between dashboard and connectors
└── Support for multiple remote networks
```

## 📋 Requirements

### **For the Central Dashboard:**
- Docker 20.10+
- Docker Compose 2.0+
- 2 GB RAM minimum
- 10 GB disk minimum
- Available ports: 80, 443, 5000, 6379

### **For Remote Agents:**
- Docker 20.10+
- Docker Compose 2.0+
- 512 MB RAM minimum
- 2 GB disk minimum
- Hermes Agent installed on host
- Port 8081 available
- SSH access from the dashboard

## 🚀 Quick Installation

### **Step 1: Clone and configure the Central Dashboard**

```bash
# Copy Docker files to central server
scp -r docker/* user@dashboard-server:/opt/hermes-docker/

# Connect to central server
ssh user@dashboard-server

# Go to Docker directory
cd /opt/hermes-docker

# Initialize system
chmod +x deploy-hermes-docker.sh
./deploy-hermes-docker.sh init

# Start Dashboard
./deploy-hermes-docker.sh start
```

### **Step 2: Deploy Remote Connectors**

```bash
# From central server, deploy connectors to other servers
./deploy-hermes-docker.sh connector remote-server.com user

# The script automatically:
# 1. Copies necessary files to remote server
# 2. Configures connection to central dashboard
# 3. Builds and starts connector Docker
# 4. Registers agent in dashboard
```

### **Step 3: Access Dashboard**

```
http://dashboard-server:5000
```

## 📖 System Commands

### **Central Dashboard Management:**

```bash
# Initialize system (first time)
./deploy-hermes-docker.sh init

# Start Dashboard
./deploy-hermes-docker.sh start

# Stop Dashboard
./deploy-hermes-docker.sh stop

# Restart Dashboard
./deploy-hermes-docker.sh restart

# Check status
./deploy-hermes-docker.sh status

# View real-time logs
./deploy-hermes-docker.sh logs
```

### **Remote Connector Management:**

```bash
# Deploy connector to remote server
./deploy-hermes-docker.sh connector <host> <user>

# Example:
./deploy-hermes-docker.sh connector production-server.com admin
./deploy-hermes-docker.sh connector 192.168.1.100 user

# Connector is automatically registered in dashboard
```

## 🔧 Configuration

### **Dashboard Environment Variables:**

File: `config/dashboard.env`

```bash
# Flask Configuration
FLASK_ENV=production
DASHBOARD_SECRET_KEY=<random-generated-secret>

# Redis
REDIS_URL=redis://redis:6379/0

# Security
CONNECTOR_API_KEY=<generated-api-key>
ALLOWED_ORIGINS=*
```

### **Connector Environment Variables:**

File: `~/hermes-connector/.env` (on remote server)

```bash
# Dashboard Connection
DASHBOARD_URL=http://dashboard-server:5000
CONNECTOR_API_KEY=<same-api-key-as-dashboard>

# Agent Information
AGENT_NAME=agent-production-server
AGENT_HOST=production-server.com
HERMES_PORT=8080
AGENT_TYPE=remote
```

## 🌐 Network Architecture

### **Dashboard ↔ Connector Communication:**

```
Central Dashboard (192.168.1.10)
├── Port 5000: Web Dashboard
├── Port 8081: Not used (connectors only)
└── Docker Network: 172.20.0.0/16

Remote Connector 1 (192.168.1.20)
├── Port 8081: Connector API
├── Mounts ~/.hermes from host
└── Connects to Dashboard:5000

Remote Connector 2 (192.168.1.30)
├── Port 8081: Connector API
├── Mounts ~/.hermes from host
└── Connects to Dashboard:5000
```

### **Registration Flow:**

1. **Connector starts** → Connects to Dashboard
2. **Sends registration** → With its info and API key
3. **Dashboard validates** → Verifies API key
4. **Dashboard accepts** → Agent appears in dashboard
5. **Periodic heartbeat** → Every 60 seconds

## 🔒 Security

### **Authentication:**
- **API Key** randomly generated
- **Header `X-API-Key`** in all requests
- **Validation on every endpoint**

### **Communication:**
- **HTTP** by default (you can add HTTPS with Nginx)
- **Recommended firewall:** Only necessary ports
- **VPN recommended** for public networks

### **Host Resources:**
- **Read-only `~/.hermes`**
- **Limited command execution**
- **Non-root user inside container**

## 📊 Connector API

The connector exposes an API for the Dashboard to monitor it:

### **GET /health**
```bash
curl -H "X-API-Key: ***" http://connector-host:8081/health
```

Response:
```json
{
  "status": "healthy",
  "agent": {
    "name": "agent-production",
    "host": "production-server.com",
    "port": 8080,
    "type": "remote"
  },
  "hermes_health": {
    "health_score": 85,
    "resource_usage": {
      "cpu_percent": 45,
      "memory_percent": 60,
      "disk_percent": 30
    }
  }
}
```

### **POST /restart**
```bash
curl -X POST \
  -H "X-API-Key: ***" \
  http://connector-host:8081/restart
```

### **GET /logs**
```bash
curl -H "X-API-Key: ***" \
  "http://connector-host:8081/logs?lines=100"
```

## 🎯 Use Cases

### **Case 1: Local Development + Production Server**

```bash
# Dashboard on your local machine (for testing)
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Connector on production server
./deploy-hermes-docker.sh connector production.com admin
```

### **Case 2: Multiple Production Servers**

```bash
# Dashboard on dedicated monitoring server
ssh admin@monitoring-server.com
cd /opt/hermes-docker
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Connectors on multiple servers
./deploy-hermes-docker.sh connector server1.prod.com admin
./deploy-hermes-docker.sh connector server2.prod.com admin
./deploy-hermes-docker.sh connector server3.prod.com admin
```

### **Case 3: Cloud + On-Premise**

```bash
# Dashboard in cloud (AWS, GCP, Azure)
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Connectors on on-premise servers
./deploy-hermes-docker.sh connector on-premise-1.local user
./deploy-hermes-docker.sh connector on-premise-2.local user
```

## 🐛 Troubleshooting

### **Problem: Connector not registering**

```bash
# View connector logs on remote server
ssh user@remote-server
docker logs -f hermes-connector

# Verify Dashboard is accessible
curl http://dashboard-server:5000/api/metrics

# Verify API key matches
grep CONNECTOR_API_KEY ~/hermes-connector/.env
```

### **Problem: Cannot access Dashboard**

```bash
# Verify container is running
docker ps | grep hermes-dashboard

# View Dashboard logs
docker logs hermes-dashboard

# Verify ports
netstat -tuln | grep 5000
```

### **Problem: Heartbeat failing**

```bash
# Check network connectivity
ping dashboard-server
telnet dashboard-server 5000

# Check firewall
sudo ufw status
sudo firewall-cmd --list-all
```

## 📈 Monitoring and Logs

### **Central Dashboard Logs:**
```bash
# View real-time logs
docker logs -f hermes-dashboard

# View all service logs
docker-compose logs -f
```

### **Remote Connector Logs:**
```bash
# On remote server
ssh user@remote-server
docker logs -f hermes-connector

# View specific logs
docker logs hermes-connector | grep ERROR
docker logs hermes-connector | grep heartbeat
```

## 🚀 System Update

### **Update Central Dashboard:**
```bash
# Stop services
./deploy-hermes-docker.sh stop

# Update code
git pull  # or copy new files

# Rebuild images
./deploy-hermes-docker.sh init

# Start services
./deploy-hermes-docker.sh start
```

### **Update Remote Connectors:**
```bash
# Deploy script updates automatically
./deploy-hermes-docker.sh connector remote-server.com user
```

## 💡 Best Practices

### **Security:**
1. ✅ Use VPN for server-to-server communication
2. ✅ Change API keys periodically
3. ✅ Use HTTPS in production (configure Nginx)
4. ✅ Limit access with firewall
5. ✅ Use non-root users for SSH

### **Monitoring:**
1. ✅ Configure alerts in Dashboard
2. ✅ Review logs periodically
3. ✅ Monitor container resources
4. ✅ Configure automatic backups

### **Scalability:**
1. ✅ Use Redis cluster for many agents
2. ✅ Load balance with multiple dashboards
3. ✅ Use Nginx for HTTPS and caching
4. ✅ Configure aggressive health checks

## 📞 Support

If you encounter issues:

1. Review container logs
2. Check network connectivity
3. Confirm ports are available
4. Validate API keys match

---

**🎉 System created specifically for Hermes multi-agent management with Docker**
