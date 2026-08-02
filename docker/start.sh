#!/bin/bash
# ============================================
# 🚀 APanel - Ultra Simple Start
# ============================================
# THE SIMPLEST POSSIBLE SCRIPT
# One single command to get everything running
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 APanel - Start in ONE single command                    ║
║   Hermes Multi-Agent Management System                        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Function to show progress
show_progress() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    show_progress "Docker not found. Installing automatically..."
    
    # Execute auto-installer
    if [ -f "auto-install.sh" ]; then
        chmod +x auto-install.sh
        ./auto-install.sh
    else
        echo "Error: auto-install.sh not found"
        exit 1
    fi
else
    show_progress "Docker is already installed ✅"
fi

# Check if we're in the correct directory
if [ -f "quick-start.sh" ]; then
    show_progress "Starting APanel..."
    chmod +x quick-start.sh
    ./quick-start.sh
else
    # Try to download APanel
    show_progress "Downloading APanel from GitHub..."
    
    if [ -d "apanel" ]; then
        cd apanel
    else
        git clone git@github.com:gerardosandovalcabreira/apanel.git
        cd apanel
    fi
    
    # Execute quick-start
    chmod +x docker/quick-start.sh
    docker/quick-start.sh
fi

echo -e "\n${GREEN}🎉 ALL READY! APanel is running${NC}\n"
echo -e "${BLUE}📊 Dashboard: http://localhost:5000/${NC}"
echo -e "${BLUE}🤖 MCP Server: http://localhost:5000/mcp/${NC}\n"
