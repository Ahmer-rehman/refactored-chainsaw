#!/bin/bash
# PostgreSQL initialization script for Synapse
# This script runs when the PostgreSQL container is first created

set -e

# Create extensions if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    
    -- Set locale
    UPDATE pg_database SET datcollate='C', datctype='C' WHERE datname='$POSTGRES_DB';
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
EOSQL

echo "PostgreSQL initialization complete"
