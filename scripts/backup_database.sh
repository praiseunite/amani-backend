#!/bin/bash
#
# Database Backup Script for Amani Backend
# Creates timestamped backups of the PostgreSQL database
#
# Usage: ./backup_database.sh [backup_directory]
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="amani_backup_${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Retention settings
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    # SECURITY: Load environment variables safely
    # Only export variables that match the expected pattern
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        # Only export valid variable names (alphanumeric and underscore)
        if [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
            export "$key=$value"
        fi
    done < .env
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Parse DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    echo -e "${RED}Error: DATABASE_URL not set in .env${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting database backup...${NC}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Extract connection details from DATABASE_URL
# Format: postgresql+asyncpg://user:password@host:port/dbname
DB_URL_CLEAN=$(echo "${DATABASE_URL}" | sed 's/postgresql+asyncpg:/postgresql:/')
export PGPASSWORD=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_USER=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_HOST=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo -e "${YELLOW}Database: ${DB_NAME}${NC}"
echo -e "${YELLOW}Host: ${DB_HOST}${NC}"
echo -e "${YELLOW}Port: ${DB_PORT}${NC}"

# Perform backup
echo -e "${YELLOW}Creating backup: ${BACKUP_PATH}${NC}"

pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --format=custom \
    --compress=9 \
    --file="${BACKUP_PATH}" \
    --verbose

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup completed successfully!${NC}"
    
    # Get backup size
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    echo -e "${GREEN}Backup size: ${BACKUP_SIZE}${NC}"
    
    # Compress backup
    echo -e "${YELLOW}Compressing backup...${NC}"
    gzip "${BACKUP_PATH}"
    COMPRESSED_SIZE=$(du -h "${BACKUP_PATH}.gz" | cut -f1)
    echo -e "${GREEN}Compressed size: ${COMPRESSED_SIZE}${NC}"
    
    # Clean up old backups
    echo -e "${YELLOW}Cleaning up backups older than ${RETENTION_DAYS} days...${NC}"
    find "${BACKUP_DIR}" -name "amani_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
    
    # List recent backups
    echo -e "${YELLOW}Recent backups:${NC}"
    ls -lh "${BACKUP_DIR}" | grep "amani_backup_" | tail -5
    
else
    echo -e "${RED}Backup failed!${NC}"
    exit 1
fi

# Unset password
unset PGPASSWORD

echo -e "${GREEN}Backup process completed!${NC}"
