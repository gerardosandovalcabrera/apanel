#!/bin/bash
# SAFE Backup to GitHub - NO SECRETS
# Only backs up configuration and code, NEVER secrets

# Configuration
BACKUP_DIR="${HOME}/hermes-backup"
GITHUB_REPO="${GITHUB_REPO:-hermes-config-backup}"
TEMP_DIR="${BACKUP_DIR}/temp-github-safe"
LOG_FILE="${BACKUP_DIR}/github-safe-backup.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "${LOG_FILE}"
}

echo "========================================"
echo "🔐 SAFE Backup to GitHub (NO SECRETS)"
echo "========================================"
echo "Date: $(date)"
echo ""

# List of files to EXCLUDE (secrets)
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

echo "🚫 Files EXCLUDED from backup (secrets):"
for file in "${SECRETS_FILES[@]}"; do
    echo "   ❌ ${file}"
done
echo ""

# Create temporary directory
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

# Copy ONLY safe files
SAFE_BACKUP_ITEMS=(
    "hermes-config/config.yaml"
    "hermes-config/tools/*.py"
    "hermes-config/tools/*.sh"
    "hermes-config/skills/**/*.md"
    "README.md"
    "backup-hermes.sh"
    "restore-hermes.sh"
)

echo "📦 Copying SAFE files (no secrets):"
for item in "${SAFE_BACKUP_ITEMS[@]}"; do
    src="${BACKUP_DIR}/${item}"
    if [ -e "$src" ]; then
        mkdir -p "${TEMP_DIR}/$(dirname "${item}")"
        
        if [ -d "$src" ]; then
            cp -r "$src" "${TEMP_DIR}/${item}/"
            echo "  📁 ${item}"
        else
            # Verify file doesn't contain secrets
            if ! grep -qiE "(api[_-]?key|token|secret|password)" "$src"; then
                cp "$src" "${TEMP_DIR}/${item}"
                echo "  ✅ ${item}"
            else
                echo "  ⚠️  ${item} (contains potential secrets, excluded)"
            fi
        fi
    fi
