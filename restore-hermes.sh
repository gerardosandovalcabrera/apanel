#!/bin/bash
# Script de Restauración para Hermes
# Restaura versiones específicas desde el backup

# Configuración
HERMES_HOME="${HOME}/.hermes"
BACKUP_DIR="${HOME}/hermes-backup"
BACKUP_REPO="${BACKUP_DIR}/hermes-config"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo "🔄 Sistema de Restauración de Hermes"
    echo ""
    echo "Uso: $0 [opción] [argumento]"
    echo ""
    echo "Opciones:"
    echo "  list                          Listar todos los backups disponibles"
    echo "  show <commit>                 Mostrar detalles de un backup específico"
    echo "  restore <commit>              Restaurar desde un commit específico"
    echo "  restore-latest                Restaurar el backup más reciente"
    echo "  export <commit> <destino>     Exportar un backup a un archivo .tar.gz"
    echo "  import <archivo>              Importar un backup desde un archivo .tar.gz"
    echo "  help                          Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 list                       # Ver todos los backups"
    echo "  $0 restore abc1234            # Restaurar el backup abc1234"
    echo "  $0 restore-latest             # Restaurar el backup más reciente"
}

# Función para listar backups
list_backups() {
    if [ ! -d "${BACKUP_REPO}" ]; then
        echo -e "${RED}❌ No se encontró directorio de backup: ${BACKUP_REPO}${NC}"
        exit 1
    fi
    
    cd "${BACKUP_REPO}"
    
    if [ ! -d ".git" ]; then
        echo -e "${RED}❌ No es un repositorio Git${NC}"
        exit 1
    fi
    
    echo "📋 Backups disponibles:"
    echo "====================="
    git log --oneline --graph --decorate --all
    echo ""
    
    echo "📊 Información de estado:"
    echo "  Commits totales: $(git rev-list --count HEAD)"
    echo "  Último commit: $(git log -1 --format='%h - %an - %ar' | head -c 60)..."
}

# Función para mostrar detalles de un backup
show_backup() {
    if [ -z "$1" ]; then
        echo -e "${RED}❌ Especifica un commit${NC}"
        exit 1
    fi
    
    cd "${BACKUP_REPO}"
    
    echo "📋 Detalles del backup: $1"
    echo "====================="
    echo ""
    
    git show --stat "$1"
    echo ""
    
    echo "📝 Mensaje del commit:"
    git log -1 --format=%B "$1"
    echo ""
    
    echo "📂 Archivos en este backup:"
    git ls-tree -r --name-only "$1" | head -20
    if [ $(git ls-tree -r --name-only "$1" | wc -l) -gt 20 ]; then
        echo "  ... y $(($(git ls-tree -r --name-only "$1" | wc -l) - 20)) archivos más"
    fi
}

# Función para restaurar desde un commit
restore_backup() {
    if [ -z "$1" ]; then
        echo -e "${RED}❌ Especifica un commit${NC}"
        exit 1
    fi
    
    cd "${BACKUP_REPO}"
    
    echo "🔄 Restaurando backup: $1"
    echo "====================="
    echo ""
    
    # Verificar que el commit existe
    if ! git cat-file -e "$1" 2>/dev/null; then
        echo -e "${RED}❌ El commit $1 no existe${NC}"
        exit 1
    fi
    
    # Crear backup de seguridad del estado actual
    echo "📦 Creando backup de seguridad del estado actual..."
    TEMP_BACKUP="${BACKUP_DIR}/emergency-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${TEMP_BACKUP}"
    
    if [ -f "${HERMES_HOME}/config.yaml" ]; then
        cp "${HERMES_HOME}/config.yaml" "${TEMP_BACKUP}/"
    fi
    if [ -f "${HERMES_HOME}/.env" ]; then
        cp "${HERMES_HOME}/.env" "${TEMP_BACKUP}/"
    fi
    
    echo "✅ Backup de seguridad creado: ${TEMP_BACKUP}"
    echo ""
    
    # Restaurar archivos
    echo "📂 Restaurando archivos..."
    
    # Hacer checkout del commit especificado
    git checkout "$1" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error al hacer checkout del commit${NC}"
        echo "🔄 Restaurando backup de seguridad..."
        cp "${TEMP_BACKUP}"/* "${HERMES_HOME}/"
        exit 1
    fi
    
    # Copiar archivos restaurados a .hermes
    cp -r config.yaml "${HERMES_HOME}/" 2>/dev/null && echo "  ✅ config.yaml"
    cp -r .env "${HERMES_HOME}/" 2>/dev/null && echo "  ✅ .env"
    cp -r auth.json "${HERMES_HOME}/" 2>/dev/null && echo "  ✅ auth.json"
    cp -r tools/* "${HERMES_HOME}/tools/" 2>/dev/null && echo "  ✅ tools/"
    cp -r skills/* "${HERMES_HOME}/skills/" 2>/dev/null && echo "  ✅ skills/"
    cp -r plugins/* "${HERMES_HOME}/plugins/" 2>/dev/null && echo "  ✅ plugins/"
    
    echo ""
    echo "✅ Restauración completada!"
    echo ""
    echo "⚠️  NOTA IMPORTANTE:"
    echo "  • El backup de seguridad está en: ${TEMP_BACKUP}"
    echo "  • Es posible que necesites reiniciar Hermes para aplicar los cambios"
    echo "  • Verifica que todo funciona correctamente antes de eliminar el backup de seguridad"
    echo ""
}

# Función para restaurar el último backup
restore_latest() {
    cd "${BACKUP_REPO}"
    LATEST=$(git log -1 --format=%H)
    echo "🔄 Restaurando el backup más reciente: ${LATEST}"
    restore_backup "$LATEST"
}

# Función para exportar un backup
export_backup() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo -e "${RED}❌ Especifica commit y destino${NC}"
        exit 1
    fi
    
    cd "${BACKUP_REPO}"
    
    echo "📦 Exportando backup: $1"
    echo "====================="
    
    # Crear archivo temporal
    TEMP_DIR=$(mktemp -d)
    git archive "$1" | tar -x -C "${TEMP_DIR}"
    
    # Comprimir
    tar -czf "$2" -C "${TEMP_DIR}" .
    
    rm -rf "${TEMP_DIR}"
    
    echo "✅ Backup exportado a: $2"
}

# Función para importar un backup
import_backup() {
    if [ -z "$1" ]; then
        echo -e "${RED}❌ Especifica el archivo de backup${NC}"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        echo -e "${RED}❌ El archivo no existe: $1${NC}"
        exit 1
    fi
    
    cd "${BACKUP_REPO}"
    
    echo "📥 Importando backup: $1"
    echo "====================="
    
    # Extraer backup
    TEMP_DIR=$(mktemp -d)
    tar -xzf "$1" -C "${TEMP_DIR}"
    
    # Copiar archivos
    cp -r "${TEMP_DIR}"/* .
    
    # Hacer commit
    git add .
    git commit -m "Backup importado desde: $1
Fecha: $(date)"

    rm -rf "${TEMP_DIR}"
    
    echo "✅ Backup importado exitosamente!"
}

# Procesar argumentos
case "$1" in
    list)
        list_backups
        ;;
    show)
        show_backup "$2"
        ;;
    restore)
        restore_backup "$2"
        ;;
    restore-latest)
        restore_latest
        ;;
    export)
        export_backup "$2" "$3"
        ;;
    import)
        import_backup "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Opción no reconocida${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
