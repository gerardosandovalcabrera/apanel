#!/bin/bash
# Initialize APanel Database
# This script initializes the PostgreSQL database and creates all tables

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🗄️  APanel Database Initialization                        ║
║   Creating PostgreSQL tables for persistence                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if PostgreSQL is running
echo -e "${BLUE}🔍 Checking PostgreSQL connection...${NC}"

if ! docker ps | grep -q "hermes-postgres"; then
    echo -e "${YELLOW}⚠️  PostgreSQL container not running. Starting it...${NC}"
    docker-compose up -d postgres
    echo -e "${GREEN}✅ PostgreSQL started${NC}"
    sleep 5
fi

# Wait for PostgreSQL to be ready
echo -e "${BLUE}⏳ Waiting for PostgreSQL to be ready...${NC}"
until docker exec hermes-postgres pg_isready -U apanel -d apanel_db > /dev/null 2>&1; do
    echo -e "${YELLOW}   Waiting for database...${NC}"
    sleep 2
done
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"

# Install Python dependencies if needed
echo -e "${BLUE}📦 Checking Python dependencies...${NC}"
if ! python3 -c "import sqlalchemy" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing SQLAlchemy and psycopg2...${NC}"
    pip3 install sqlalchemy psycopg2-binary
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"

# Initialize database
echo -e "${BLUE}🗄️  Creating database tables...${NC}"

# Set environment variables for database connection
export DATABASE_URL="postgresql://apanel:apanel_password@localhost:5432/apanel_db"

# Run database initialization
python3 apanel_database.py

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   🎉 Database initialization completed!                    ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}📊 Database Information:${NC}"
echo -e "${BLUE}   Host: localhost:5432${NC}"
echo -e "${BLUE}   Database: apanel_db${NC}"
echo -e "${BLUE}   User: apanel${NC}"
echo -e "${BLUE}   Password: apanel_password${NC}\n"

echo -e "${YELLOW}📝 Useful commands:${NC}"
echo -e "${BLUE}   Connect to database: docker exec -it hermes-postgres psql -U apanel -d apanel_db${NC}"
echo -e "${BLUE}   View tables: docker exec -it hermes-postgres psql -U apanel -d apanel_db -c '\dt'${NC}"
echo -e "${BLUE}   Stop database: docker-compose stop postgres${NC}\n"

echo -e "${GREEN}✅ APanel is now ready with full persistence!${NC}"
