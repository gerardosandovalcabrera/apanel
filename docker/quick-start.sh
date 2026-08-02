#!/bin/bash
# ============================================
# 🚀 QUICK START - APanel System in Docker
# ============================================
# This script does EVERYTHING automatically:
# - Checks dependencies
# - Configures Docker
# - Starts the complete system
# - Shows how to access
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 APanel - Hermes Multi-Agent Management System            ║
║   🐳 Quick Start with Docker - Fully Automatic               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Function to print messages
print_step() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📋 $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Step 1: Check dependencies
print_step "Step 1: Checking dependencies..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed"
    echo -e "${YELLOW}Install Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    print_success "Docker Compose installed: $COMPOSE_VERSION"
else
    print_warning "Docker Compose not found, trying to install..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
fi

# Step 2: Verify we're in the correct directory
print_step "Step 2: Verifying project directory..."

if [ ! -f "docker-compose.yml" ]; then
    print_error "We didn't find docker-compose.yml"
    echo -e "${YELLOW}Make sure you're in the APanel project directory${NC}"
    exit 1
fi

print_success "Correct directory: $(pwd)"

# Step 3: Create necessary directories
print_step "Step 3: Creating necessary directories..."

mkdir -p config data logs nginx/ssl
print_success "Directories created"

# Step 4: Generate automatic configuration
print_step "Step 4: Generating automatic configuration..."

# Generate random secrets
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 32)

# Create configuration file
cat > config/dashboard.env << EOF
# APanel Configuration - Auto-generated
# ==========================================
# Generated on: $(date)

# Security
JWT_SECRET=$JWT_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY
API_KEY=$API_KEY

# Application
APP_NAME=APanel
APP_ENV=production
DEBUG=false

# Ports
FLASK_PORT=5000
NGINX_PORT=80
NGINX_SSL_PORT=443

# Database (using SQLite for simplicity)
DATABASE_URL=sqlite:///data/apanel.db

# Logging
LOG_LEVEL=INFO
LOG_DIR=/app/logs
EOF

print_success "Configuration generated"

# Step 5: Build and start containers
print_step "Step 5: Building and starting containers..."

if [ -f "docker-compose.yml" ]; then
    docker-compose down 2>/dev/null || true
    docker-compose build
    docker-compose up -d
    print_success "Containers started"
else
    print_error "docker-compose.yml not found"
    exit 1
fi

# Step 6: Wait for services to be ready
print_step "Step 6: Waiting for services to be ready..."

sleep 5

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    print_success "All containers are running"
else
    print_error "Some containers failed to start"
    docker-compose ps
    exit 1
fi

# Step 7: Display access information
print_step "Step 7: System ready!"

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   🎉 APanel is running successfully!                          ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${CYAN}📊 Access the dashboard:${NC}"
echo -e "${BLUE}   HTTP:  http://localhost:80/${NC}"
echo -e "${BLUE}   HTTPS: https://localhost:443/ (if SSL is configured)${NC}\n"

echo -e "${CYAN}🔌 Available endpoints:${NC}"
echo -e "${BLUE}   Dashboard:    http://localhost:80/${NC}"
echo -e "${BLUE}   API:          http://localhost:80/api/${NC}"
echo -e "${BLUE}   MCP Server:   http://localhost:80/mcp/${NC}"
echo -e "${BLUE}   Health Check: http://localhost:80/api/health${NC}\n"

echo -e "${CYAN}📝 Useful commands:${NC}"
echo -e "${BLUE}   View logs:    docker-compose logs -f${NC}"
echo -e "${BLUE}   Stop system:  docker-compose down${NC}"
echo -e "${BLUE}   Restart:      docker-compose restart${NC}"
echo -e "${BLUE}   Check status: docker-compose ps${NC}\n"

echo -e "${YELLOW}⚠️  Note: If you're running this on a remote server,${NC}"
echo -e "${YELLOW}   replace 'localhost' with your server's IP address${NC}\n"

print_success "Installation and startup completed successfully!"
