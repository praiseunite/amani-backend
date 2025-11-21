#!/bin/bash
# Migration Testing Script
# Tests Alembic migrations up and down for safety verification

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Alembic Migration Testing Script ===${NC}"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL environment variable is not set${NC}"
    echo "Please set DATABASE_URL to your test database connection string"
    echo "Example: export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/test_db"
    exit 1
fi

echo -e "${YELLOW}Using DATABASE_URL: ${DATABASE_URL}${NC}"
echo ""

# Function to check current migration state
check_migration_state() {
    echo -e "${YELLOW}Current migration state:${NC}"
    alembic current
    echo ""
}

# Function to show migration history
show_migration_history() {
    echo -e "${YELLOW}Migration history:${NC}"
    alembic history
    echo ""
}

# Test 1: Check current state
echo -e "${GREEN}Test 1: Checking current migration state...${NC}"
check_migration_state

# Test 2: Upgrade to head
echo -e "${GREEN}Test 2: Upgrading to head...${NC}"
alembic upgrade head
check_migration_state
echo -e "${GREEN}✓ Upgrade to head successful${NC}"
echo ""

# Test 3: Downgrade one step
echo -e "${GREEN}Test 3: Testing rollback (downgrade -1)...${NC}"
alembic downgrade -1
check_migration_state
echo -e "${GREEN}✓ Rollback successful${NC}"
echo ""

# Test 4: Re-apply last migration
echo -e "${GREEN}Test 4: Re-applying last migration...${NC}"
alembic upgrade head
check_migration_state
echo -e "${GREEN}✓ Re-apply successful${NC}"
echo ""

# Test 5: Show full history
echo -e "${GREEN}Test 5: Full migration history...${NC}"
show_migration_history

echo -e "${GREEN}=== All migration tests completed successfully ===${NC}"
echo ""
echo -e "${YELLOW}Migration verification checklist:${NC}"
echo "  ✓ Migrations apply without errors"
echo "  ✓ Rollback works correctly"
echo "  ✓ Re-apply after rollback works"
echo ""
echo -e "${GREEN}Your migrations are ready for production!${NC}"
