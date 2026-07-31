#!/bin/bash
# ============================================
# 🚀 APanel - Inicio Ultra Simple
# ============================================
# EL SCRIPT MÁS SIMPLE POSIBLE
# Un solo comando para tener todo funcionando
# ============================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 APanel - Inicio en UN solo comando                      ║
║   Sistema de Administración Multi-Agente de Hermes             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Función para mostrar progreso
show_progress() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    show_progress "Docker no encontrado. Instalando automáticamente..."
    
    # Ejecutar auto-installer
    if [ -f "auto-install.sh" ]; then
        chmod +x auto-install.sh
        ./auto-install.sh
    else
        echo "Error: auto-install.sh no encontrado"
        exit 1
    fi
else
    show_progress "Docker ya está instalado ✅"
fi

# Verificar si estamos en el directorio correcto
if [ -f "quick-start.sh" ]; then
    show_progress "Iniciando APanel..."
    chmod +x quick-start.sh
    ./quick-start.sh
else
    # Intentar descargar APanel
    show_progress "Descargando APanel desde GitHub..."
    
    if [ -d "apanel" ]; then
        cd apanel
    else
        git clone git@github.com:gerardosandovalcabrera/apanel.git
        cd apanel
    fi
    
    # Ejecutar quick-start
    chmod +x docker/quick-start.sh
    docker/quick-start.sh
fi

echo -e "\n${GREEN}🎉 ¡TODO LISTO! APanel está corriendo${NC}\n"
echo -e "${BLUE}📊 Dashboard: http://localhost:5000/${NC}"
echo -e "${BLUE}🤖 MCP Server: http://localhost:5000/mcp/${NC}\n"
