#!/bin/bash
# Automated Backup Script for Hermes
# Creates versioned and restorable backups

# Configuration
HERMES_HOME="${HOME}/.hermes"
BACKUP_DIR="${HOME}/hermes-backup"
BACKUP_REPO="${BACKUP_DIR}/hermes-config"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="hermes-backup-${DATE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "🔄 Automated Hermes Backup"
echo "========================================"
echo "Date: $(date)"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_REPO}"
cd "${BACKUP_REPO}"

# Initialize repository if it doesn't exist
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Repository initialized"
fi

echo "📂 Copying configuration files..."

# Directories and files to backup (excluding very large items)
backup_items=(
    "config.yaml"
    ".env"
    "auth.json"
    "tools/"
    "skills/"
    "plugins/"
)

# Copy files
for item in "${backup_items[@]}"; do
    src="${HERMES_HOME}/${item}"
    if [ -e "$src" ]; then
        if [ -d "$src" ]; then
            echo "  📁 Copying directory: ${item}"
            cp -r "$src" "${BACKUP_REPO}/"
        else
            echo "  📄 Copying file: ${item}"
            cp "$src" "${BACKUP_REPO}/"
        fi
    else
        echo "  ⚠️  Not found: ${item}"
    fi
