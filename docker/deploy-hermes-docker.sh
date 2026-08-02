#!/bin/bash
# Hermes Multi-Agent System Docker Deployment Script
# Deploy Central (Dashboard) and Remote Connectors

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "🐳 Hermes Multi-Agent Docker Deployment"
echo "========================================"
echo ""

# Function to check dependencies
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        echo "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        echo "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencies verified${NC}"
    echo ""
}

# Function to generate configuration
generate_config() {
    echo "🔧 Generating configuration..."
    
    # Create necessary directories
    mkdir -p config data logs nginx/ssl
    
    # Generate random secrets
    DASHBOARD_SECRET_KEY=$(openssl rand -hex 32)
    CONNECTOR_API_KEY=$(openssl rand -hex 32)
    
    # Create configuration file
    cat > config/dashboard.env << EOF
# Dashboard Configuration
FLASK_ENV=production
DASHBOARD_SECRET_KEY=${DASHBOARD_SECRET_KEY}
REDIS_URL=redis://redis:6379/0

# Security Configuration
CONNECTOR_API_KEY=${CONNECTOR_API_KEY}
ALLOWED_ORIGINS=*
EOF
