#!/bin/bash
# Quick start script for Synapse deployment
# This script helps you get started quickly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Matrix Synapse Quick Start Setup Script            ║${NC}"
echo -e "${BLUE}║       Security-Hardened Deployment                        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Step 1: Create .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Step 1: Creating environment configuration...${NC}"
    read -p "Enter your server domain (e.g., matrix.example.com): " SERVER_NAME
    read -sp "Enter PostgreSQL password: " POSTGRES_PASS
    echo ""
    
    cat > .env << EOF
# PostgreSQL Configuration
POSTGRES_DB=synapse
POSTGRES_USER=synapse
POSTGRES_PASSWORD=${POSTGRES_PASS}
POSTGRES_INITDB_ARGS=--encoding=UTF8 --locale=C

# Synapse Configuration
SYNAPSE_SERVER_NAME=${SERVER_NAME}
SYNAPSE_REPORT_STATS=no
SYNAPSE_CONFIG_PATH=/data/homeserver.yaml

# Timezone
TZ=UTC

# Docker Compose Project Name
COMPOSE_PROJECT_NAME=synapse
EOF
    
    echo -e "${GREEN}✓ Environment file created (.env)${NC}"
else
    echo -e "${GREEN}✓ Environment file already exists (.env)${NC}"
fi

# Step 2: Update homeserver.yaml
echo ""
echo -e "${YELLOW}Step 2: Updating homeserver configuration...${NC}"
if [ -f data/homeserver.yaml ]; then
    # Backup existing config
    cp data/homeserver.yaml data/homeserver.yaml.backup
    echo -e "${GREEN}✓ Backed up existing homeserver.yaml${NC}"
fi

# Create data directory if it doesn't exist
mkdir -p data/media_store
chmod 700 data

echo -e "${GREEN}✓ Data directory prepared${NC}"

# Step 3: Generate signing key
echo ""
echo -e "${YELLOW}Step 3: Generating signing key...${NC}"
if [ ! -f data/signing.key ]; then
    echo "Generating signing key (this may take a moment)..."
    docker compose run --rm synapse generate || {
        echo -e "${RED}Failed to generate signing key${NC}"
        echo "You may need to run this manually:"
        echo "  docker compose run --rm synapse generate"
    }
    echo -e "${GREEN}✓ Signing key generated${NC}"
else
    echo -e "${GREEN}✓ Signing key already exists${NC}"
fi

# Step 4: Create required directories
echo ""
echo -e "${YELLOW}Step 4: Creating required directories...${NC}"
mkdir -p logs/radius
mkdir -p backups
mkdir -p config/ssl
echo -e "${GREEN}✓ Directories created${NC}"

# Step 5: Build and start services
echo ""
echo -e "${YELLOW}Step 5: Building Docker images...${NC}"
echo "This may take several minutes on first run..."
docker compose build

echo ""
echo -e "${YELLOW}Step 6: Starting services...${NC}"
docker compose up -d

echo ""
echo -e "${GREEN}✓ Services started!${NC}"

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check service status
echo ""
echo -e "${BLUE}Service Status:${NC}"
docker compose ps

# Step 7: Create admin user
echo ""
echo -e "${YELLOW}Step 7: Create admin user${NC}"
read -p "Do you want to create an admin user now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter admin username: " ADMIN_USER
    echo "Creating admin user..."
    docker compose exec synapse register_new_matrix_user \
        -c /data/homeserver.yaml \
        -u "$ADMIN_USER" \
        -a \
        http://localhost:8008 || {
        echo -e "${YELLOW}Note: You can create an admin user later with:${NC}"
        echo "  docker compose exec synapse register_new_matrix_user -c /data/homeserver.yaml -u admin -a http://localhost:8008"
    }
fi

# Final instructions
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   Setup Complete!                         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Your Synapse server is now running!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Check service health:"
echo "   ${BLUE}curl http://localhost:8008/health${NC}"
echo ""
echo "2. View logs:"
echo "   ${BLUE}docker compose logs -f synapse${NC}"
echo ""
echo "3. Create users:"
echo "   ${BLUE}docker compose exec synapse register_new_matrix_user -c /data/homeserver.yaml http://localhost:8008${NC}"
echo ""
echo "4. Configure SSL (for production):"
echo "   - Obtain SSL certificate for your domain"
echo "   - Place in config/ssl/ directory"
echo "   - Uncomment nginx service in docker-compose.yaml"
echo "   - Run: ${BLUE}docker compose up -d nginx${NC}"
echo ""
echo "5. Backup your data:"
echo "   ${BLUE}./scripts/backup.sh${NC}"
echo ""
echo -e "${YELLOW}Important Files:${NC}"
echo "   - Configuration: ${BLUE}data/homeserver.yaml${NC}"
echo "   - Logs: ${BLUE}data/homeserver.log${NC}"
echo "   - Environment: ${BLUE}.env${NC}"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "   - Deployment Guide: ${BLUE}DEPLOYMENT_GUIDE.md${NC}"
echo "   - Configuration Index: ${BLUE}CONFIG_INDEX.md${NC}"
echo "   - Security Fixes: ${BLUE}SECURITY_FIXES_ACUNETIX.md${NC}"
echo ""
echo -e "${GREEN}Happy chatting! 🚀${NC}"
echo ""
