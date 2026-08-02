#!/bin/bash
# Restoration Script for Hermes
# Restores specific versions from backup

# Configuration
HERMES_HOME="${HOME}/.hermes"
BACKUP_DIR="${HOME}/hermes-backup"
BACKUP_REPO="${BACKUP_DIR}/hermes-config"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show help
show_help() {
    echo "🔄 Hermes Restoration System"
    echo ""
    echo "Usage: $0 [option] [argument]"
    echo ""
    echo "Options:"
    echo "  list                          List all available backups"
    echo "  show <commit>                 Show details of a specific backup"
    echo "  restore <commit>              Restore from a specific commit"
    echo "  restore-latest                Restore the most recent backup"
    echo "  export <commit> <destination> Export a backup to a .tar.gz file"
    echo "  import <file>                 Import a backup from a .tar.gz file"
    echo "  help                          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 list                       # View all backups"
    echo "  $0 restore abc1234            # Restore backup abc1234"
    echo "  $0 restore-latest             # Restore most recent backup"
}

# Function to list backups
list_backups() {
    if [ ! -d "${BACKUP_REPO}" ]; then
        echo -e "${RED}❌ Backup directory not found: ${BACKUP_REPO}${NC}"
        exit 1
    fi
    
    cd "${BACKUP_REPO}"
    
    if [ ! -d ".git" ]; then
        echo -e "${RED}❌ Not a Git repository${NC}"
        exit 1
    fi
    
    echo "📋 Available backups:"
    echo "====================="
    git log --oneline --graph --decorate --all
    echo ""
    
    echo "📊 Status information:"
    echo "  Total commits: $(git rev-list --count HEAD)"
    echo "  Last commit: $(git log -1 --format='%h - %an - %ar' | head -c 60)..."
}
