#!/bin/bash
# Backup script for Synapse deployment
# Run this script regularly to backup your data

set -e

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="docker-compose.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Synapse backup...${NC}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
echo -e "${YELLOW}Backing up PostgreSQL database...${NC}"
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U synapse synapse | gzip > "$BACKUP_DIR/synapse_db_${DATE}.sql.gz"
echo -e "${GREEN}✓ Database backup complete: synapse_db_${DATE}.sql.gz${NC}"

# Backup Synapse data directory
echo -e "${YELLOW}Backing up Synapse data directory...${NC}"
tar -czf "$BACKUP_DIR/synapse_data_${DATE}.tar.gz" \
    --exclude='./data/media_store' \
    ./data
echo -e "${GREEN}✓ Data directory backup complete: synapse_data_${DATE}.tar.gz${NC}"

# Backup media store (optional, can be large)
# Uncomment if you want to backup media files
# echo -e "${YELLOW}Backing up media store...${NC}"
# tar -czf "$BACKUP_DIR/synapse_media_${DATE}.tar.gz" ./data/media_store
# echo -e "${GREEN}✓ Media store backup complete: synapse_media_${DATE}.tar.gz${NC}"

# Backup configuration files
echo -e "${YELLOW}Backing up configuration files...${NC}"
tar -czf "$BACKUP_DIR/synapse_config_${DATE}.tar.gz" \
    ./config \
    ./docker-compose.yaml \
    ./.env 2>/dev/null || tar -czf "$BACKUP_DIR/synapse_config_${DATE}.tar.gz" \
    ./config \
    ./docker-compose.yaml
echo -e "${GREEN}✓ Configuration backup complete: synapse_config_${DATE}.tar.gz${NC}"

# Calculate backup sizes
DB_SIZE=$(du -h "$BACKUP_DIR/synapse_db_${DATE}.sql.gz" | cut -f1)
DATA_SIZE=$(du -h "$BACKUP_DIR/synapse_data_${DATE}.tar.gz" | cut -f1)
CONFIG_SIZE=$(du -h "$BACKUP_DIR/synapse_config_${DATE}.tar.gz" | cut -f1)

echo ""
echo -e "${GREEN}=== Backup Summary ===${NC}"
echo -e "Database backup: ${DB_SIZE}"
echo -e "Data backup: ${DATA_SIZE}"
echo -e "Config backup: ${CONFIG_SIZE}"
echo -e "Backup location: ${BACKUP_DIR}"
echo ""

# Clean up old backups (keep last 7 days)
echo -e "${YELLOW}Cleaning up old backups (keeping last 7 days)...${NC}"
find "$BACKUP_DIR" -name "synapse_*.gz" -mtime +7 -delete
echo -e "${GREEN}✓ Cleanup complete${NC}"

echo -e "${GREEN}Backup completed successfully!${NC}"
