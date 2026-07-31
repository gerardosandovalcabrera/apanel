#!/bin/bash
# ============================================
# 🔧 AUTO-INSTALLER - Instala Docker y APanel
# ============================================
# Este script detecta tu sistema operativo e instala
# Docker automáticamente si no está instalado
# ============================================

set -e

# Colores
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
║   Instalación automática de Docker y APanel                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Detectar sistema operativo
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

# Detectar sistema operativo
print_step "Detectando sistema operativo..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
    print_success "Sistema detectado: $OS $OS_VERSION"
else
    print_error "No se pudo detectar el sistema operativo"
    exit 1
fi

# Función para instalar Docker en Ubuntu/Debian
install_docker_ubuntu() {
    print_step "Instalando Docker en Ubuntu/Debian..."
    
    # Actualizar repositorios
    sudo apt-get update -qq
    
    # Instalar dependencias
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Agregar clave GPG de Docker
    curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Agregar repositorio de Docker
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    sudo apt-get update -qq
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Instalar docker-compose separado
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Habilitar y arrancar Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Agregar usuario al grupo docker
    sudo usermod -aG docker $USER
    
    print_success "Docker instalado exitosamente"
    print_warning "Necesitas cerrar sesión y volver a entrar para que los cambios de grupo surtan efecto"
}

# Función para instalar Docker en CentOS/RHEL
install_docker_centos() {
    print_step "Instalando Docker en CentOS/RHEL..."
    
    # Instalar dependencias
    sudo yum install -y yum-utils
    
    # Agregar repositorio de Docker
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # Instalar Docker
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Instalar docker-compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Habilitar y arrancar Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Agregar usuario al grupo docker
    sudo usermod -aG docker $USER
    
    print_success "Docker instalado exitosamente"
    print_warning "Necesitas cerrar sesión y volver a entrar para que los cambios de grupo surtan efecto"
}

# Función para instalar Docker en Fedora
install_docker_fedora() {
    print_step "Instalando Docker en Fedora..."
    
    # Agregar repositorio de Docker
    sudo dnf -y install dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    
    # Instalar Docker
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Instalar docker-compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Habilitar y arrancar Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Agregar usuario al grupo docker
    sudo usermod -aG docker $USER
    
    print_success "Docker instalado exitosamente"
    print_warning "Necesitas cerrar sesión y volver a entrar para que los cambios de grupo surtan efecto"
}

# Verificar si Docker está instalado
print_step "Verificando instalación de Docker..."

if ! command -v docker &> /dev/null; then
    print_warning "Docker no está instalado. Procediendo a instalar..."
    
    case $OS in
        ubuntu|debian)
            install_docker_ubuntu
            ;;
        centos|rhel)
            install_docker_centos
            ;;
        fedora)
            install_docker_fedora
            ;;
        *)
            print_error "Sistema operativo no soportado automáticamente: $OS"
            echo "Por favor instala Docker manualmente: https://docs.docker.com/get-docker/"
            exit 1
            ;;
    esac
    
    # Verificar instalación
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker instalado: $DOCKER_VERSION"
    else
        print_error "Error en la instalación de Docker"
        exit 1
    fi
else
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker ya está instalado: $DOCKER_VERSION"
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose no encontrado, instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose instalado"
else
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    print_success "Docker Compose ya está instalado: $COMPOSE_VERSION"
fi

# Probar Docker
print_step "Probando Docker..."

if sudo docker run --rm hello-world > /dev/null 2>&1; then
    print_success "Docker funciona correctamente"
else
    print_error "Docker no funciona correctamente"
    print_warning "Intenta reiniciar el servicio Docker: sudo systemctl restart docker"
    exit 1
fi

# Descargar APanel si no existe
print_step "Verificando instalación de APanel..."

if [ ! -d "apanel" ]; then
    print_warning "APanel no encontrado, clonando desde GitHub..."
    git clone git@github.com:gerardosandovalcabrera/apanel.git
    cd apanel
    print_success "APanel clonado exitosamente"
else
    print_success "APanel ya existe"
    cd apanel
    
    # Actualizar si existe
    print_step "Actualizando APanel..."
    git pull origin main
fi

# Verificar que estamos en el directorio correcto
if [ ! -f "quick-start.sh" ]; then
    print_error "No encontramos el script quick-start.sh"
    exit 1
fi

# Ejecutar quick-start
print_step "Ejecutando configuración rápida de APanel..."

chmod +x quick-start.sh
./quick-start.sh

print_success "¡Instalación completada!"
echo -e "${GREEN}🎉 El sistema APanel está listo para usar${NC}\n"
