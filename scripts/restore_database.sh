#!/bin/bash
#
# Database Restore Script for Amani Backend
# Restores a PostgreSQL database from a backup file
#
# Usage: ./restore_database.sh <backup_file>
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Check for backup file argument
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 ./backups/amani_backup_20250122_143000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Parse DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    echo -e "${RED}Error: DATABASE_URL not set in .env${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting database restore...${NC}"
echo -e "${RED}WARNING: This will OVERWRITE the current database!${NC}"
echo -e "${YELLOW}Backup file: ${BACKUP_FILE}${NC}"

# Extract connection details from DATABASE_URL
DB_URL_CLEAN=$(echo "${DATABASE_URL}" | sed 's/postgresql+asyncpg:/postgresql:/')
export PGPASSWORD=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_USER=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_HOST=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo "${DB_URL_CLEAN}" | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo -e "${YELLOW}Database: ${DB_NAME}${NC}"
echo -e "${YELLOW}Host: ${DB_HOST}${NC}"
echo -e "${YELLOW}Port: ${DB_PORT}${NC}"

# Confirmation prompt
read -p "Are you sure you want to restore? This cannot be undone! (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    exit 0
fi

# Decompress if needed
WORK_FILE="${BACKUP_FILE}"
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    echo -e "${YELLOW}Decompressing backup file...${NC}"
    WORK_FILE="${BACKUP_FILE%.gz}"
    gunzip -c "${BACKUP_FILE}" > "${WORK_FILE}"
    CLEANUP_NEEDED=true
else
    CLEANUP_NEEDED=false
fi

# Drop existing connections to the database
echo -e "${YELLOW}Terminating existing database connections...${NC}"
psql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="postgres" \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
    || true

# Perform restore
echo -e "${YELLOW}Restoring database from backup...${NC}"

pg_restore \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --verbose \
    "${WORK_FILE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database restore completed successfully!${NC}"
    
    # Clean up decompressed file if needed
    if [ "${CLEANUP_NEEDED}" = true ]; then
        rm -f "${WORK_FILE}"
    fi
    
    # Verify restore
    echo -e "${YELLOW}Verifying restore...${NC}"
    TABLE_COUNT=$(psql \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    echo -e "${GREEN}Number of tables in database: ${TABLE_COUNT}${NC}"
    
else
    echo -e "${RED}Database restore failed!${NC}"
    if [ "${CLEANUP_NEEDED}" = true ]; then
        rm -f "${WORK_FILE}"
    fi
    exit 1
fi

# Unset password
unset PGPASSWORD

echo -e "${GREEN}Restore process completed!${NC}"
echo -e "${YELLOW}Remember to run migrations if needed: alembic upgrade head${NC}"
