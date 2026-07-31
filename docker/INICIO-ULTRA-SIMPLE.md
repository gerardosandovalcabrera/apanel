# 🚀 **ULTRA SIMPLE STARTUP - APanel in Docker**

## 🎯 **You have 3 options to start APanel, choose the one you prefer:**

---

## 🔥 **OPTION 1: ONE COMMAND (EASIEST)**

### **If you want EVERYTHING working with ONE command:**

```bash
# Clone the repo
git clone git@github.com:gerardosandovalcabrera/apanel.git
cd apanel

# EXECUTE ONE COMMAND:
chmod +x docker/start.sh
./docker/start.sh
```

**This script does EVERYTHING automatically:**
- ✅ Verifies if Docker is installed
- ✅ If not, installs it automatically
- ✅ Downloads APanel if you don't have it
- ✅ Configures everything automatically
- ✅ Starts the complete system
- ✅ Shows you how to access

**Total time:** 5-10 minutes (depends on your connection)

---

## 🛠️ **OPTION 2: Auto-Installer (RECOMMENDED for new servers)**

### **If you have a new server without Docker:**

```bash
# Clone the repo
git clone git@github.com:gerardosandovalcabreira/apanel.git
cd apanel/docker

# EXECUTE:
chmod +x auto-install.sh
./auto-install.sh
```

**This script:**
- ✅ Automatically detects your operating system
- ✅ Installs Docker if not present
- ✅ Installs Docker Compose
- ✅ Configures system settings
- ✅ Starts APanel

**Supported OS:**
- ✅ Ubuntu 20.04, 22.04
- ✅ Debian 11, 12
- ✅ CentOS 7, 8, 9
- ✅ RHEL 8, 9

**Total time:** 10-15 minutes

---

## ⚡ **OPTION 3: Quick Start (if you already have Docker)**

### **If you already have Docker installed:**

```bash
# Clone the repo
git clone git@github.com:gerardosandovalcabreira/apanel.git
cd apanel/docker

# Execute:
chmod +x quick-start.sh
./quick-start.sh
```

**This script:**
- ✅ Verifies Docker is running
- ✅ Builds APanel containers
- ✅ Starts all services
- ✅ Shows you how to access

**Total time:** 3-5 minutes

---

## 🎯 **How to Access APanel**

After running any of the scripts, you'll see:

```
✅ APanel is ready!

Access your dashboard:
🌐 Web Dashboard: http://localhost:5000
🤖 MCP Server: http://localhost:5000/mcp
📊 Billing: http://localhost:5000/billing
📋 Plans: http://localhost:5000/plans

Login with:
• GitHub OAuth
• Google OAuth
• Or configure your own auth
```

---

## 🛠️ **System Requirements**

### **Minimum Requirements:**
- **CPU:** 2 cores
- **RAM:** 2 GB
- **Disk:** 10 GB
- **OS:** Linux (Ubuntu, Debian, CentOS, RHEL)

### **Recommended Requirements:**
- **CPU:** 4 cores
- **RAM:** 4 GB
- **Disk:** 20 GB
- **OS:** Ubuntu 22.04 LTS

---

## 🔧 **After First Startup**

### **1. Configure Authentication**

```bash
# Edit environment variables
cd ~/apanel/docker
nano .env

# Add your OAuth credentials:
OAUTH_GITHUB_CLIENT_ID='your-github-client-id'
OAUTH_GITHUB_CLIENT_SECRET='your-github-client-secret'
OAUTH_GOOGLE_CLIENT_ID='your-google-client-id'
OAUTH_GOOGLE_CLIENT_SECRET='your-google-client-secret'
```

### **2. Create OAuth Apps**

**For GitHub:**
1. Go to https://github.com/settings/developers
2. Create "New OAuth App"
3. Set callback: `http://localhost:5000/auth/github/callback`

**For Google:**
1. Go to https://console.cloud.google.com/
2. Create "OAuth 2.0 Client IDs"
3. Set redirect: `http://localhost:5000/auth/google/callback`

### **3. Restart the System**

```bash
./start.sh restart
```

---

## 📊 **What Gets Installed**

### **Services Started:**
- ✅ **Flask Web Dashboard** (port 5000)
- ✅ **Redis Cache** (port 6379)
- ✅ **MCP Server** (port 5000/mcp)
- ✅ **Billing System** (integrated)
- ✅ **Plans & Limits** (integrated)

### **Features Available:**
- ✅ Multi-agent management
- ✅ Real-time cost tracking
- ✅ Budget monitoring
- ✅ Plan management
- ✅ Security (OAuth, JWT, RBAC)
- ✅ API for integrations

---

## 🐛 **Troubleshooting**

### **Problem: Docker not found**

```bash
# Install Docker manually
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### **Problem: Port 5000 already in use**

```bash
# Find what's using the port
sudo lsof -i :5000

# Kill the process (if needed)
sudo kill -9 <PID>

# Or use a different port
# Edit docker-compose.yml and change port mapping
```

### **Problem: Cannot access dashboard**

```bash
# Check if containers are running
docker ps

# View logs
docker logs apanel-dashboard

# Check firewall
sudo ufw status
```

---

## 🚀 **Next Steps**

### **For Development:**
1. ✅ Read the [README.md](../README.md)
2. ✅ Explore the [docker/README.md](./README.md)
3. ✅ Check the [API documentation](http://localhost:5000/docs)

### **For Production:**
1. ✅ Configure HTTPS with Let's Encrypt
2. ✅ Set up firewall rules
3. ✅ Configure automated backups
4. ✅ Set up monitoring and alerts
5. ✅ Review security best practices

### **For Customization:**
1. ✅ Explore the code structure
2. ✅ Modify the dashboard (templates/)
3. ✅ Add custom skills
4. ✅ Configure billing rules
5. ✅ Set up custom plans

---

## 💡 **Tips**

### **1. Use Auto-Start**
```bash
# Add to crontab for auto-start on boot
@reboot /home/user/apanel/docker/start.sh start
```

### **2. Regular Updates**
```bash
# Update APanel regularly
cd ~/apanel
git pull origin main
cd docker
./start.sh restart
```

### **3. Monitor Resources**
```bash
# Check container resources
docker stats

# View logs
docker logs -f apanel-dashboard
```

---

## 📞 **Support**

If you encounter issues:

1. **Check logs:** `docker logs apanel-dashboard`
2. **Verify Docker:** `docker --version`
3. **Check ports:** `sudo netstat -tuln | grep 5000`
4. **Review documentation:** [README.md](../README.md)

---

## 🎉 **You're Ready!**

APanel is now running with:
- 🤖 Multi-agent management
- 💰 Cost tracking & billing
- 📋 Plans & limits
- 🔐 Professional security
- 🎨 Beautiful dashboard

**Start exploring at:** http://localhost:5000

---

**Last Updated:** 2025-07-31
**Version:** 1.0.0
**Status:** ✅ Ready to use
