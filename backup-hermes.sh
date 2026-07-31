#!/bin/bash
# Script de Backup Automatizado para Hermes
# Crea backups versionados y restaurables

# Configuración
HERMES_HOME="${HOME}/.hermes"
BACKUP_DIR="${HOME}/hermes-backup"
BACKUP_REPO="${BACKUP_DIR}/hermes-config"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="hermes-backup-${DATE}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "🔄 Backup Automatizado de Hermes"
echo "========================================"
echo "Fecha: $(date)"
echo ""

# Crear directorio de backup si no existe
mkdir -p "${BACKUP_REPO}"
cd "${BACKUP_REPO}"

# Inicializar repositorio si no existe
if [ ! -d ".git" ]; then
    echo "📦 Inicializando repositorio Git..."
    git init
    echo "✅ Repositorio inicializado"
fi

echo "📂 Copiando archivos de configuración..."

# Directorios y archivos a respaldar (excluyendo cosas muy grandes)
backup_items=(
    "config.yaml"
    ".env"
    "auth.json"
    "tools/"
    "skills/"
    "plugins/"
)

# Copiar archivos
for item in "${backup_items[@]}"; do
    src="${HERMES_HOME}/${item}"
    if [ -e "$src" ]; then
        if [ -d "$src" ]; then
            echo "  📁 Copiando directorio: ${item}"
            cp -r "$src" "${BACKUP_REPO}/"
        else
            echo "  📄 Copiando archivo: ${item}"
            cp "$src" "${BACKUP_REPO}/"
        fi
    else
        echo "  ⚠️  No encontrado: ${item}"
    fi
done

echo ""
echo "📝 Creando commit en Git..."

# Verificar si hay cambios
if git diff --quiet && git diff --cached --quiet; then
    echo "ℹ️  No hay cambios para commit"
else
    git add .
    git commit -m "Backup automático - ${DATE}
    
Archivos respaldados:
- Configuración (config.yaml)
- Variables de entorno (.env)
- Autenticación (auth.json)  
- Herramientas personalizadas (tools/)
- Skills personalizadas (skills/)
- Plugins instalados (plugins/)

Generado automáticamente por backup-hermes.sh"
    
    echo "✅ Commit creado: ${DATE}"
fi

# Crear backup comprimido de estado (opcional, para restauraciones completas)
echo ""
echo "📦 Creando backup comprimido del estado actual..."

STATE_BACKUP="${BACKUP_DIR}/state-backups"
mkdir -p "${STATE_BACKUP}"

# Backup de bases de datos y estado
if [ -f "${HERMES_HOME}/state.db" ]; then
    echo "  📊 Respaldando state.db..."
    cp "${HERMES_HOME}/state.db" "${STATE_BACKUP}/state-${DATE}.db"
fi

if [ -d "${HERMES_HOME}/sessions" ]; then
    echo "  📝 Respaldando sesiones..."
    tar -czf "${STATE_BACKUP}/sessions-${DATE}.tar.gz" -C "${HERMES_HOME}" sessions/ 2>/dev/null || echo "  ⚠️  Error al respaldar sesiones"
fi

# Limpiar backups viejos (mantener últimos 7 días)
echo ""
echo "🧹 Limpiando backups viejos..."
find "${STATE_BACKUP}" -name "state-*.db" -mtime +7 -delete 2>/dev/null
find "${STATE_BACKUP}" -name "sessions-*.tar.gz" -mtime +7 -delete 2>/dev/null
find "${BACKUP_DIR}" -name "hermes-backup-*.tar.gz" -mtime +7 -delete 2>/dev/null

echo "✅ Backups viejos eliminados"

# Crear backup comprimido completo (opcional)
echo ""
echo "📦 Creando backup comprimido completo..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "${BACKUP_REPO}" . 2>/dev/null
echo "✅ Backup completo: ${BACKUP_NAME}.tar.gz"

# Mostrar resumen
echo ""
echo "========================================"
echo "📊 RESUMEN DEL BACKUP"
echo "========================================"
echo "📍 Repositorio Git: ${BACKUP_REPO}"
echo "📦 Backup completo: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "📊 Backups de estado: ${STATE_BACKUP}"
echo ""
echo "📈 Estadísticas del repositorio:"
cd "${BACKUP_REPO}"
echo "  Commits totales: $(git rev-list --count HEAD)"
echo "  Último commit: $(git log -1 --format='%h - %s' | head -c 50)..."
echo ""
echo "💾 Espacio utilizado:"
du -sh "${BACKUP_REPO}" | awk '{print "  Repositorio: " $1}'
du -sh "${BACKUP_DIR}" | awk '{print "  Total backup: " $1}'
echo ""
echo "✅ Backup completado exitosamente!"
echo ""
echo "🔄 Para restaurar, usa:"
echo "   cd ${BACKUP_REPO}"
echo "   git log --oneline"
echo "   git checkout <commit-hash>"
echo "   cp -r * ${HERMES_HOME}/"
echo ""