#!/bin/bash
# ============================================
# 🚀 QUICK START - Sistema APanel en Docker
# ============================================
# Este script hace TODO automáticamente:
# - Verifica dependencias
# - Configura Docker
# - Inicia el sistema completo
# - Muestra cómo acceder
# ============================================

set -e

# Colores para output
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
║   🐳 Inicio Rápido con Docker - Todo Automático                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Función para imprimir mensajes
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

# Paso 1: Verificar dependencias
print_step "Paso 1: Verificando dependencias..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker instalado: $DOCKER_VERSION"
else
    print_error "Docker no está instalado"
    echo -e "${YELLOW}Instala Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    print_success "Docker Compose instalado: $COMPOSE_VERSION"
else
    print_warning "Docker Compose no encontrado, intentando instalar..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose instalado"
fi

# Paso 2: Verificar que estamos en el directorio correcto
print_step "Paso 2: Verificando directorio del proyecto..."

if [ ! -f "docker-compose.yml" ]; then
    print_error "No encontramos docker-compose.yml"
    echo -e "${YELLOW}Asegúrate de estar en el directorio del proyecto APanel${NC}"
    exit 1
fi

print_success "Directorio correcto: $(pwd)"

# Paso 3: Crear directorios necesarios
print_step "Paso 3: Creando directorios necesarios..."

mkdir -p config data logs nginx/ssl
print_success "Directorios creados"

# Paso 4: Generar configuración automáticamente
print_step "Paso 4: Generando configuración automática..."

# Generar secrets aleatorios
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 32)

# Crear archivo de configuración
cat > config/dashboard.env << EOF
# ============================================
# 🔐 Configuración de Seguridad de APanel
# ============================================
# Generado automáticamente: $(date)

# JWT Configuration
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Encryption
ENCRYPTION_KEY=$ENCRYPTION_KEY

# API Keys
CONNECTOR_API_KEY=hermes_$API_KEY

# Redis
REDIS_URL=redis://redis:6379/0

# Security
ALLOWED_ORIGINS=*
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_TIME=900
RATE_LIMIT_PER_MINUTE=60

# OAuth (configurar después)
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
EOF

print_success "Configuración generada"

# Paso 5: Crear archivo .env para docker-compose
print_step "Paso 5: Configurando variables de entorno..."

cat > .env << EOF
# APanel Docker Configuration
COMPOSE_PROJECT_NAME=apanel

# Dashboard Configuration
DASHBOARD_PORT=5000
REDIS_PORT=6379

# Security
JWT_SECRET_KEY=$JWT_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY
CONNECTOR_API_KEY=hermes_$API_KEY

# OAuth (configurar después de instalar)
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
EOF

print_success "Variables de entorno configuradas"

# Paso 6: Construir imágenes Docker
print_step "Paso 6: Construyendo imágenes Docker (esto puede tardar unos minutos)..."

if docker-compose build; then
    print_success "Imágenes Docker construidas"
else
    print_error "Error al construir imágenes Docker"
    exit 1
fi

# Paso 7: Iniciar contenedores
print_step "Paso 7: Iniciando contenedores..."

if docker-compose up -d; then
    print_success "Contenedores iniciados"
else
    print_error "Error al iniciar contenedores"
    exit 1
fi

# Paso 8: Esperar a que el sistema esté listo
print_step "Paso 8: Esperando que el sistema esté listo..."

echo "Esperando al dashboard..."
for i in {1..30}; do
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        print_success "Sistema listo y funcionando"
        break
    fi
    echo -n "."
    sleep 2
    
    if [ $i -eq 30 ]; then
        print_warning "Tiempo de espera agotado, pero el sistema puede estar iniciándose"
        echo "Revisa los logs con: docker-compose logs -f"
    fi
done

# Paso 9: Verificar estado
print_step "Paso 9: Verificando estado del sistema..."

docker-compose ps

# Paso 10: Mostrar información de acceso
print_step "🎉 ¡SISTEMA APANEL INICIADO EXITOSAMENTE!"

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                  🌐 ACCESO AL SISTEMA                           ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  📊 Dashboard Web:                                             ║
║     http://localhost:5000/                                     ║
║                                                               ║
║  🤖 MCP Server (para agentes):                               ║
║     http://localhost:5000/mcp/                                ║
║                                                               ║
║  🔐 Documentación de Auth:                                     ║
║     http://localhost:5000/auth/providers                       ║
║                                                               ║
║  📚 Documentación completa:                                    ║
║     http://localhost:5000/docs                                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Comandos útiles:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${GREEN}Ver logs en tiempo real:${NC}"
echo "  docker-compose logs -f"

echo -e "${GREEN}Ver estado de contenedores:${NC}"
echo "  docker-compose ps"

echo -e "${GREEN}Detener el sistema:${NC}"
echo "  docker-compose down"

echo -e "${GREEN}Reiniciar el sistema:${NC}"
echo "  docker-compose restart"

echo -e "${GREEN}Actualizar el sistema:${NC}"
echo "  docker-compose pull && docker-compose up -d"

echo -e "\n${YELLOW}⚠️  IMPORTANTE - Configurar OAuth Providers:${NC}"
echo "  Para el login completo, configura OAuth apps en GitHub y Google"
echo "  Luego actualiza las variables en config/dashboard.env"
echo "  y reinicia: docker-compose restart"

echo -e "\n${GREEN}🔐 API Key para conectar agentes remotos:${NC}"
echo "  hermes_$API_KEY"
echo "  Guárdala en un lugar seguro"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ¡TODO LISTO! El sistema APanel está corriendo en Docker${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Preguntar si el usuario quiere configurar OAuth ahora
read -p "¿Quieres configurar OAuth providers ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo -e "\n${BLUE}Configurando OAuth Providers...${NC}"
    echo -e "${YELLOW}1. GitHub OAuth:${NC}"
    echo "   Ve a: https://github.com/settings/developers"
    echo "   Crea 'New OAuth App'"
    echo "   Authorization callback: http://localhost:5000/auth/github/callback"
    echo -e "\n${YELLOW}2. Google OAuth:${NC}"
    echo "   Ve a: https://console.cloud.google.com/"
    echo "   Crea 'OAuth 2.0 Client IDs'"
    echo "   Authorized redirect: http://localhost:5000/auth/google/callback"
    echo -e "\n${YELLOW}3. Actualiza el archivo config/dashboard.env${NC}"
    echo "   Luego ejecuta: docker-compose restart"
fi

echo -e "\n${GREEN}¡Disfruta de tu sistema APanel! 🚀${NC}\n"
