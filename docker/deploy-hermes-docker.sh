#!/bin/bash
# Script de Deployment del Sistema Hermes Multi-Agent en Docker
# Deploy Central (Dashboard) y Conectores Remotos

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "🐳 Hermes Multi-Agent Docker Deployment"
echo "========================================"
echo ""

# Función para verificar dependencias
check_dependencies() {
    echo "🔍 Verificando dependencias..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker no está instalado${NC}"
        echo "Instala Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose no está instalado${NC}"
        echo "Instala Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencias verificadas${NC}"
    echo ""
}

# Función para generar configuración
generate_config() {
    echo "🔧 Generando configuración..."
    
    # Crear directorios necesarios
    mkdir -p config data logs nginx/ssl
    
    # Generar secretos aleatorios
    DASHBOARD_SECRET_KEY=$(openssl rand -hex 32)
    CONNECTOR_API_KEY=$(openssl rand -hex 32)
    
    # Crear archivo de configuración
    cat > config/dashboard.env << EOF
# Configuración del Dashboard
FLASK_ENV=production
DASHBOARD_SECRET_KEY=${DASHBOARD_SECRET_KEY}
REDIS_URL=redis://redis:6379/0

# Configuración de Seguridad
CONNECTOR_API_KEY=${CONNECTOR_API_KEY}
ALLOWED_ORIGINS=*
EOF
    
    cat > config/connector.env << EOF
# Configuración del Connector
DASHBOARD_URL=http://$(hostname -I | awk '{print $1}'):5000
CONNECTOR_API_KEY=${CONNECTOR_API_KEY}
AGENT_NAME=agent-$(hostname)
AGENT_HOST=$(hostname -I | awk '{print $1}')
HERMES_PORT=8080
AGENT_TYPE=remote
EOF
    
    echo -e "${GREEN}✅ Configuración generada${NC}"
    echo -e "${BLUE}📝 API Key del Connector: ${CONNECTOR_API_KEY}${NC}"
    echo ""
}

# Función para construir imágenes Docker
build_images() {
    echo "🔨 Construyendo imágenes Docker..."
    
    docker-compose build
    
    echo -e "${GREEN}✅ Imágenes construidas${NC}"
    echo ""
}

# Función para iniciar el Dashboard Central
start_dashboard() {
    echo "🚀 Iniciando Dashboard Central..."
    
    docker-compose up -d
    
    echo -e "${GREEN}✅ Dashboard iniciado${NC}"
    echo ""
    echo "📊 Dashboard disponible en:"
    echo -e "   ${BLUE}http://localhost:5000${NC}"
    echo ""
    echo "📝 Logs del Dashboard:"
    echo "   docker-compose logs -f hermes-dashboard"
    echo ""
}

# Función para deploy de connector remoto
deploy_connector() {
    REMOTE_HOST=$1
    REMOTE_USER=$2
    
    if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_USER" ]; then
        echo -e "${YELLOW}Uso: ./deploy-hermes-docker.sh connector <host> <user>${NC}"
        exit 1
    fi
    
    echo "🚀 Desplegando Connector en ${REMOTE_USER}@${REMOTE_HOST}..."
    
    # Copiar archivos necesarios
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ~/hermes-connector"
    scp docker-compose.connector.yml "${REMOTE_USER}@${REMOTE_HOST}:~/hermes-connector/"
    scp Dockerfile.connector "${REMOTE_USER}@${REMOTE_HOST}:~/hermes-connector/"
    scp requirements-connector.txt "${REMOTE_USER}@${REMOTE_HOST}:~/hermes-connector/"
    scp hermes_agent_connector.py "${REMOTE_USER}@${REMOTE_HOST}:~/hermes-connector/"
    
    # Obtener la API key del dashboard
    CONNECTOR_API_KEY=$(grep CONNECTOR_API_KEY config/connector.env | cut -d'=' -f2)
    DASHBOARD_IP=$(hostname -I | awk '{print $1}')
    
    # Crear archivo .env en el host remoto
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "cat > ~/hermes-connector/.env << EOF
DASHBOARD_URL=http://${DASHBOARD_IP}:5000
CONNECTOR_API_KEY=${CONNECTOR_API_KEY}
AGENT_NAME=agent-${REMOTE_HOST}
AGENT_HOST=${REMOTE_HOST}
HERMES_PORT=8080
AGENT_TYPE=remote
EOF"
    
    # Construir e iniciar el connector en el host remoto
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ~/hermes-connector && docker-compose -f docker-compose.connector.yml build && docker-compose -f docker-compose.connector.yml up -d"
    
    echo -e "${GREEN}✅ Connector desplegado en ${REMOTE_HOST}${NC}"
    echo ""
}

# Función para mostrar estado
show_status() {
    echo "📊 Estado del Sistema:"
    echo ""
    
    docker-compose ps
    echo ""
    
    echo "📊 Conectores Activos:"
    curl -s http://localhost:5000/api/metrics | python3 -m json.tool || echo "Dashboard no accesible"
    echo ""
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: ./deploy-hermes-docker.sh [comando] [opciones]"
    echo ""
    echo "Comandos:"
    echo "  init        - Inicializa el sistema (verifica, configura, construye)"
    echo "  start       - Inicia el Dashboard Central"
    echo "  stop        - Detiene todos los servicios"
    echo "  restart     - Reinicia el Dashboard Central"
    echo "  status      - Muestra el estado del sistema"
    echo "  logs        - Muestra los logs del Dashboard"
    echo "  connector   - Despliega un connector remoto (requiere host y user)"
    echo "  help        - Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./deploy-hermes-docker.sh init"
    echo "  ./deploy-hermes-docker.sh start"
    echo "  ./deploy-hermes-docker.sh connector remote-server.example.com user"
    echo ""
}

# Main
case "$1" in
    init)
        check_dependencies
        generate_config
        build_images
        echo -e "${GREEN}🎉 Sistema inicializado correctamente${NC}"
        echo -e "${YELLOW}Ejecuta './deploy-hermes-docker.sh start' para iniciar el Dashboard${NC}"
        ;;
        
    start)
        start_dashboard
        ;;
        
    stop)
        echo "🛑 Deteniendo servicios..."
        docker-compose down
        echo -e "${GREEN}✅ Servicios detenidos${NC}"
        ;;
        
    restart)
        docker-compose restart
        echo -e "${GREEN}✅ Servicios reiniciados${NC}"
        ;;
        
    status)
        show_status
        ;;
        
    logs)
        docker-compose logs -f hermes-dashboard
        ;;
        
    connector)
        deploy_connector "$2" "$3"
        ;;
        
    help|--help|-h)
        show_help
        ;;
        
    *)
        echo -e "${RED}❌ Comando desconocido: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

exit 0
