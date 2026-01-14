#!/bin/bash
# Restore script for Synapse deployment
# Usage: ./restore.sh <backup_date>
# Example: ./restore.sh 20260114_120000

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backup date is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Backup date required${NC}"
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20260114_120000"
    echo ""
    echo "Available backups:"
    ls -1 ./backups/synapse_db_*.sql.gz 2>/dev/null | sed 's/.*synapse_db_/  /' | sed 's/.sql.gz//' || echo "  No backups found"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="./backups"
COMPOSE_FILE="docker-compose.yaml"

# Check if backup files exist
if [ ! -f "$BACKUP_DIR/synapse_db_${BACKUP_DATE}.sql.gz" ]; then
    echo -e "${RED}Error: Database backup not found: synapse_db_${BACKUP_DATE}.sql.gz${NC}"
    exit 1
fi

echo -e "${YELLOW}WARNING: This will restore Synapse to backup from ${BACKUP_DATE}${NC}"
echo -e "${YELLOW}All current data will be replaced!${NC}"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

echo -e "${GREEN}Starting restore process...${NC}"

# Stop Synapse
echo -e "${YELLOW}Stopping Synapse...${NC}"
docker compose -f "$COMPOSE_FILE" stop synapse
echo -e "${GREEN}✓ Synapse stopped${NC}"

# Restore database
echo -e "${YELLOW}Restoring PostgreSQL database...${NC}"
gunzip -c "$BACKUP_DIR/synapse_db_${BACKUP_DATE}.sql.gz" | \
    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U synapse -d synapse
echo -e "${GREEN}✓ Database restored${NC}"

# Restore data directory
if [ -f "$BACKUP_DIR/synapse_data_${BACKUP_DATE}.tar.gz" ]; then
    echo -e "${YELLOW}Restoring data directory...${NC}"
    tar -xzf "$BACKUP_DIR/synapse_data_${BACKUP_DATE}.tar.gz"
    echo -e "${GREEN}✓ Data directory restored${NC}"
fi

# Restore media store (if exists)
if [ -f "$BACKUP_DIR/synapse_media_${BACKUP_DATE}.tar.gz" ]; then
    echo -e "${YELLOW}Restoring media store...${NC}"
    tar -xzf "$BACKUP_DIR/synapse_media_${BACKUP_DATE}.tar.gz"
    echo -e "${GREEN}✓ Media store restored${NC}"
fi

# Restore configuration (if exists)
if [ -f "$BACKUP_DIR/synapse_config_${BACKUP_DATE}.tar.gz" ]; then
    echo -e "${YELLOW}Restoring configuration files...${NC}"
    tar -xzf "$BACKUP_DIR/synapse_config_${BACKUP_DATE}.tar.gz"
    echo -e "${GREEN}✓ Configuration restored${NC}"
fi

# Start Synapse
echo -e "${YELLOW}Starting Synapse...${NC}"
docker compose -f "$COMPOSE_FILE" start synapse
echo -e "${GREEN}✓ Synapse started${NC}"

echo ""
echo -e "${GREEN}=== Restore Complete ===${NC}"
echo -e "Synapse has been restored from backup: ${BACKUP_DATE}"
echo -e "Check logs: docker compose logs -f synapse"
echo ""
