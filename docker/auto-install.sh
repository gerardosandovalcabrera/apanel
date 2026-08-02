#!/bin/bash
# ============================================
# 🔧 AUTO-INSTALLER - Install Docker and APanel
# ============================================
# This script detects your operating system and
# installs Docker automatically if not installed
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🔧 APanel Auto-Installer                                   ║
║   Automatic installation of Docker and APanel                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Detect operating system
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

# Detect operating system
print_step "Detecting operating system..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
    print_success "System detected: $OS $OS_VERSION"
else
    print_error "Could not detect operating system"
    exit 1
fi

# Function to install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    print_step "Installing Docker on Ubuntu/Debian..."
    
    # Update repositories
    sudo apt-get update -qq
    
    # Install dependencies
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker GPG key
    curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt-get update -qq
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Install docker-compose separately
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Enable and start Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_success "Docker installed successfully"
    print_warning "Please log out and log back in for group changes to take effect"
}

# Function to install Docker on CentOS/RHEL
install_docker_centos() {
    print_step "Installing Docker on CentOS/RHEL..."
    
    # Remove old versions
    sudo yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine
    
    # Install dependencies
    sudo yum install -y yum-utils device-mapper-persistent-data lvm2
    
    # Add Docker repository
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # Install Docker
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Enable and start Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_success "Docker installed successfully"
    print_warning "Please log out and log back in for group changes to take effect"
}

# Function to install Docker on macOS
install_docker_macos() {
    print_step "Installing Docker on macOS..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Docker Desktop
    brew install --cask docker
    
    print_success "Docker Desktop installed. Please start it from Applications."
}

# Check if Docker is already installed
print_step "Checking if Docker is already installed..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker is already installed (version $DOCKER_VERSION)"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        print_success "Docker is running"
    else
        print_warning "Docker is installed but not running. Starting Docker..."
        sudo systemctl start docker 2>/dev/null || print_warning "Please start Docker manually"
    fi
    
    # Prompt for reinstall
    read -p "Do you want to reinstall Docker? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_success "Skipping Docker installation"
    else
        print_step "Reinstalling Docker..."
    fi
fi

# Install Docker based on OS
case "$OS" in
    ubuntu|debian|linuxmint)
        install_docker_ubuntu
        ;;
    centos|rhel|fedora)
        install_docker_centos
        ;;
    darwin)
        install_docker_macos
        ;;
    *)
        print_error "Unsupported operating system: $OS"
        print_warning "Please install Docker manually from https://docs.docker.com/get-docker/"
        exit 1
        ;;
esac

print_step "Verifying Docker installation..."

# Wait a bit for Docker to start
sleep 3

if docker info &> /dev/null; then
    print_success "Docker is running correctly!"
    
    # Display Docker version
    docker --version
    docker-compose --version 2>/dev/null || echo "docker-compose: Not installed as plugin"
else
    print_error "Docker is not running. Please start it manually."
    exit 1
fi

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   🎉 Docker installation completed successfully!             ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}\n"
