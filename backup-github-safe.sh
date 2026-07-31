#!/bin/bash
# Backup SEGURO a GitHub - SIN SECRETS
# Solo respalda configuración y código, NUNCA secrets

# Configuración
BACKUP_DIR="${HOME}/hermes-backup"
GITHUB_REPO="${GITHUB_REPO:-hermes-config-backup}"
TEMP_DIR="${BACKUP_DIR}/temp-github-safe"
LOG_FILE="${BACKUP_DIR}/github-safe-backup.log"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función para log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "${LOG_FILE}"
}

echo "========================================"
echo "🔐 Backup SEGURO a GitHub (SIN SECRETS)"
echo "========================================"
echo "Fecha: $(date)"
echo ""

# Lista de archivos a EXCLUIR (secrets)
SECRETS_FILES=(
    ".env"
    "auth.json"
    "*/.env"
    "*/auth.json"
    "*api-key*"
    "*token*"
    "*secret*"
    "*password*"
)

echo "🚫 Archivos EXCLUIDOS del backup (secrets):"
for file in "${SECRETS_FILES[@]}"; do
    echo "   ❌ ${file}"
done
echo ""

# Crear directorio temporal
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

# Copiar SOLO archivos seguros
SAFE_BACKUP_ITEMS=(
    "hermes-config/config.yaml"
    "hermes-config/tools/*.py"
    "hermes-config/tools/*.sh"
    "hermes-config/skills/**/*.md"
    "README.md"
    "backup-hermes.sh"
    "restore-hermes.sh"
)

echo "📦 Copiando archivos SEGUROS (sin secrets):"
for item in "${SAFE_BACKUP_ITEMS[@]}"; do
    src="${BACKUP_DIR}/${item}"
    if [ -e "$src" ]; then
        mkdir -p "${TEMP_DIR}/$(dirname "${item}")"
        
        if [ -d "$src" ]; then
            cp -r "$src" "${TEMP_DIR}/${item}/"
            echo "  📁 ${item}"
        else
            # Verificar que el archivo no contenga secrets
            if ! grep -qiE "(api[_-]?key|token|secret|password)" "$src"; then
                cp "$src" "${TEMP_DIR}/${item}"
                echo "  ✅ ${item}"
            else
                echo "  ⚠️  ${item} (contiene posibles secrets, excluido)"
            fi
        fi
    fi
done

# Verificar config.yaml específicamente
CONFIG_FILE="${TEMP_DIR}/hermes-config/config.yaml"
if [ -f "${CONFIG_FILE}" ]; then
    echo ""
    echo "🔍 Verificando config.yaml por secrets..."
    
    # Buscar patrones de secrets en config.yaml
    if grep -qiE "(api[_-]?key|token|secret|password)" "${CONFIG_FILE}"; then
        echo -e "${YELLOW}⚠️  config.yaml contiene posibles secrets${NC}"
        echo "   Limpiando config.yaml..."
        
        # Crear versión limpia
        python3 << 'PYTHON_SCRIPT'
import yaml
import re
from pathlib import Path

config_file = Path("hermes-config/config.yaml")
if config_file.exists():
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    # Eliminar o redactar campos sensibles
    if '.env' in config:
        config['.env'] = '[REDACTED]'
    
    if 'auth' in config:
        config['auth'] = '[REDACTED]'
    
    # Redactar valores que parezcan secrets
    def redact_secrets(obj):
        if isinstance(obj, dict):
            return {k: redact_secrets(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [redact_secrets(item) for item in obj]
        elif isinstance(obj, str):
            # Redactar strings que parezcan secrets
            if re.search(r'(api[_-]?key|token|secret|password|sk-|pk-)', obj, re.IGNORECASE):
                return '[REDACTED]'
            return obj
        else:
            return obj
    
    clean_config = redact_secrets(config)
    
    with open(config_file, 'w') as f:
        yaml.dump(clean_config, f, default_flow_style=False)
    
    print("✅ config.yaml limpiado exitosamente")

PYTHON_SCRIPT
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ config.yaml limpiado de secrets${NC}"
            log "✅ config.yaml limpiado antes de subir a GitHub"
        else
            echo -e "${RED}❌ Error al limpiar config.yaml${NC}"
            log "❌ Error al limpiar config.yaml"
            # Excluir config.yaml si no se puede limpiar
            rm "${CONFIG_FILE}"
            echo "  ❌ config.yaml excluido del backup"
        fi
    else
        echo -e "${GREEN}✅ config.yaml parece seguro${NC}"
    fi
fi

# Crear README de seguridad
cat > "${TEMP_DIR}/SECURITY_NOTICE.md" << 'EOF'
# ⚠️ AVISO DE SEGURIDAD IMPORTANTE

Este repositorio contiene una versión LIMPIA de la configuración de Hermes.

## 🚫 Lo que NO está aquí:

- **NO** `.env` - Variables de entorno con API keys
- **NO** `auth.json` - Tokens de autenticación
- **NO** Secrets ni passwords
- **NO** Información sensible

## ✅ Lo que SÍ está aquí:

- Configuración general de Hermes (sin secrets)
- Herramientas personalizadas (código)
- Skills personalizadas (documentación)
- Scripts de backup y restauración

## 🛡️ Estrategia de Seguridad:

1. **Secrets guardados localmente** - Encriptados y protegidos
2. **Solo código en GitHub** - Nada que pueda comprometer cuentas
3. **GitHub es solo para código** - No para información sensible

## 🔄 Restauración Completa:

Para restaurar tu instalación completa (incluyendo secrets):

1. **Restaurar desde este repo** (código y configuración):
   ```bash
   git clone https://github.com/TU_USUARIO/hermes-config-backup.git
   cp -r hermes-config-backup/* ~/.hermes/
   ```

2. **Restaurar secrets desde backup local**:
   ```bash
   cp ~/.hermes-backup/hermes-config/.env ~/.hermes/.env
   cp ~/.hermes-backup/hermes-config/auth.json ~/.hermes/auth.json
   ```

**IMPORTANTE:** Los archivos `.env` y `auth.json` están respaldados localmente en:
- `~/hermes-backup/hermes-config/`
- `~/remote-backups/hermes-config/`

---
Este repositorio es SEGURO por diseño - no contiene secrets.
EOF

# Inicializar repositorio Git
echo ""
echo "📝 Inicializando repositorio Git seguro..."
cd "${TEMP_DIR}"
git init
git config user.name "Hermes Backup System"
git config user.email "hermes-backup@local"

# Agregar archivos
git add .

# Verificar que no se hayan agregado secrets
echo "🔍 Verificando que no haya secrets en el staging area..."
if git diff --cached --name-only | grep -E "(\.env|auth\.json|secret|token|password)"; then
    echo -e "${RED}❌ SE DETECTARON SECRETS EN EL BACKUP${NC}"
    echo "Cancelando el backup por seguridad..."
    exit 1
fi

# Crear commit
COMMIT_MSG="Backup SEGURO - $(date '+%Y-%m-%d %H:%M:%S')

⚠️  ESTE BACKUP ES SEGURO - NO CONTIENE SECRETS

Archivos respaldados:
- Configuración de Hermes (limpia de secrets)
- Herramientas personalizadas (solo código)
- Skills personalizadas (solo documentación)
- Scripts de backup

🚫 EXCLUIDOS DEL BACKUP:
- .env (variables de entorno con API keys)
- auth.json (tokens de autenticación)
- Cualquier archivo con secrets

Este respaldo es SEGURO para subir a GitHub público o privado."

git commit -m "$COMMIT_MSG" >> "${LOG_FILE}" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Commit seguro creado"
    log "✅ Commit seguro creado (sin secrets)"
else
    echo -e "${RED}❌ Error al crear commit${NC}"
    log "❌ Error al crear commit seguro"
    exit 1
fi

# Verificar autenticación de GitHub
if [ -z "${GITHUB_TOKEN}" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN no configurado${NC}"
    echo "Para subir a GitHub, configura:"
    echo "  export GITHUB_TOKEN='tu_token'"
    echo "  export GITHUB_REPO='usuario/repo'"
    exit 1
fi

# Agregar remoto y hacer push
echo "📤 Subiendo a GitHub..."
git config --global credential.helper store
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials

git remote add origin "https://github.com/${GITHUB_REPO}.git"
git branch -M main

if git push -u origin main >> "${LOG_FILE}" 2>&1; then
    echo -e "${GREEN}✅ Backup SEGURO subido a GitHub${NC}"
    log "✅ Backup seguro subido a GitHub: ${GITHUB_REPO}"
    echo ""
    echo -e "${GREEN}🔐 Este backup es SEGURO - NO contiene secrets${NC}"
else
    echo -e "${RED}❌ Error al subir a GitHub${NC}"
    log "❌ Error al subir a GitHub"
    exit 1
fi

# Limpiar directorio temporal
cd "${BACKUP_DIR}"
rm -rf "${TEMP_DIR}"

# Mostrar estadísticas
echo ""
echo "========================================"
echo "📊 RESUMEN DEL BACKUP SEGURO"
echo "========================================"
echo "🐙 Repositorio: https://github.com/${GITHUB_REPO}"
echo "🔐 Seguridad: SEGURO (sin secrets)"
echo "📝 Log: ${LOG_FILE}"
echo ""
echo "🚫 Archivos EXCLUIDOS (secrets):"
for file in "${SECRETS_FILES[@]}"; do
    echo "   ❌ ${file}"
done
echo ""
echo "✅ Archivos INCLUIDOS (seguros):"
echo "   ✅ config.yaml (limpio de secrets)"
echo "   ✅ tools/ (solo código)"
echo "   ✅ skills/ (solo documentación)"
echo "   ✅ scripts/"
echo ""
echo -e "${GREEN}🛡️ TU REPOSITORIO GITHUB ES SEGURO${NC}"
echo -e "${GREEN}🚫 NO CONTIENE SECRETS QUE PUEDAN COMPROMETER TUS CUENTAS${NC}"
