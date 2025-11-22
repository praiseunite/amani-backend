# Alembic Migration Guide

## Overview

This guide explains the migration setup for the Amani Backend project, including best practices for enum handling and idempotent migrations.

## Migration Architecture

### Enum Handling Best Practices

All PostgreSQL ENUM types in our migrations follow these best practices:

1. **Top-level enum instances**: All enums are defined as module-level variables, NOT inline with table columns
2. **create_type=False**: Enums use `create_type=False` to prevent automatic creation during column definition
3. **Explicit creation with checkfirst=True**: Enums are created explicitly before tables with `checkfirst=True` for idempotency
4. **Explicit drop with checkfirst=True**: Enums are dropped explicitly after tables with `checkfirst=True` for idempotency

#### Example:

```python
# ✅ CORRECT - Top-level enum instance
user_role_enum = postgresql.ENUM('admin', 'client', 'freelancer', name='userrole', create_type=False)

def upgrade() -> None:
    # Create enum first, with checkfirst=True for idempotency
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Create table using the enum
    op.create_table(
        'users',
        sa.Column('role', user_role_enum, nullable=False),
        ...
    )

def downgrade() -> None:
    # Drop table first
    op.drop_table('users')
    
    # Drop enum after all dependent tables, with checkfirst=True
    user_role_enum.drop(op.get_bind(), checkfirst=True)
```

```python
# ❌ INCORRECT - Inline enum (DO NOT USE)
op.create_table(
    'users',
    sa.Column('role', sa.Enum('admin', 'client', 'freelancer', name='userrole'), nullable=False),
    ...
)
```

### Current Enums

The following enums are defined in the database:

1. **userrole**: `admin`, `client`, `freelancer`
2. **holdstatus**: `active`, `released`, `captured`
3. **kyctype**: `kyc`, `kyb`
4. **kycstatus**: `pending`, `approved`, `rejected`
5. **transactiontype** (ledger): `debit`, `credit`
6. **walletprovider**: `fincra`, `paystack`, `flutterwave`
7. **milestone_status**: `pending`, `in_progress`, `completed`, `approved`, `rejected`, `disputed`
8. **project_status**: `draft`, `pending`, `active`, `in_progress`, `completed`, `disputed`, `cancelled`, `refunded`
9. **transaction_type**: `deposit`, `withdrawal`, `escrow_hold`, `escrow_release`, `refund`, `fee`, `commission`
10. **transaction_status**: `pending`, `processing`, `completed`, `failed`, `cancelled`, `refunded`

### Database Tables

The following tables are defined in the database:

1. **users**: User authentication and profile management
2. **projects**: Escrow projects
3. **milestones**: Project deliverables
4. **transactions**: Financial transactions
5. **kyc**: KYC/KYB records
6. **holds**: Escrow fund holds
7. **ledger_entries**: Accounting entries
8. **link_tokens**: Wallet connection tokens
9. **wallet_registry**: Connected wallets
10. **wallet_balance_snapshot**: Wallet balance tracking

## Migration Operations

### Running Migrations

```bash
# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"
export SECRET_KEY="your-secret-key"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
export SUPABASE_SERVICE_KEY="your-service-role-key"
export ENVIRONMENT="development"

# Upgrade to latest
alembic upgrade head

# Upgrade by N steps
alembic upgrade +2

# Check current version
alembic current

# View migration history
alembic history
```

### Rolling Back Migrations

```bash
# Downgrade by 1 step
alembic downgrade -1

# Downgrade to base (WARNING: drops all tables)
alembic downgrade base

# Downgrade to specific revision
alembic downgrade <revision_id>
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration template
alembic revision -m "Description of changes"
```

**IMPORTANT**: After auto-generating a migration with enums:

1. Move all enum definitions to the top of the file as module-level variables
2. Set `create_type=False` on all enum instances
3. Add explicit enum creation with `checkfirst=True` at the start of `upgrade()`
4. Add explicit enum drop with `checkfirst=True` at the end of `downgrade()`

### Example Migration Template with Enum

```python
"""Description

Revision ID: xxx
Revises: yyy
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'xxx'
down_revision: Union[str, None] = 'yyy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enum at module level
my_status_enum = postgresql.ENUM('active', 'inactive', name='mystatus', create_type=False)


def upgrade() -> None:
    """Apply migration."""
    # Create enum first
    my_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create or modify tables
    op.create_table(
        'my_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status', my_status_enum, nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Rollback migration."""
    # Drop tables first
    op.drop_table('my_table')
    
    # Drop enum after all dependent tables
    my_status_enum.drop(op.get_bind(), checkfirst=True)
```

## Testing Migrations

### Local Testing

```bash
# Start test database
docker run -d --name test-postgres \
  -e POSTGRES_USER=test_user \
  -e POSTGRES_PASSWORD=test_pass \
  -e POSTGRES_DB=test_db \
  -p 5432:5432 \
  postgres:15

# Wait for database to be ready
sleep 10

# Set test environment
export DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
export SECRET_KEY="test-secret-key"
export SUPABASE_URL="https://test.supabase.co"
export SUPABASE_KEY="test-key"
export SUPABASE_SERVICE_KEY="test-service-key"
export ENVIRONMENT="testing"

# Test upgrade
alembic upgrade head

# Test idempotency (should not error)
alembic upgrade head

# Test downgrade
alembic downgrade base

# Test re-upgrade
alembic upgrade head

# Clean up
docker stop test-postgres && docker rm test-postgres
```

### CI/CD Testing

Migrations are automatically tested in CI via the `migration-tests` job in `.github/workflows/ci.yml`:

1. **Upgrade test**: Applies all migrations to a fresh database
2. **Verification**: Checks migration state and history
3. **Rollback test**: Downgrades the last migration
4. **Re-apply test**: Re-applies the rolled-back migration

## Idempotency

All migrations are designed to be idempotent, meaning they can be run multiple times without error:

- `checkfirst=True` on enum creation checks if the enum already exists
- `checkfirst=True` on enum drop checks if the enum exists before dropping
- Table creation uses SQLAlchemy's built-in idempotency
- Foreign key constraints are properly ordered

### Testing Idempotency

```bash
# This should succeed without errors
alembic upgrade head
alembic upgrade head  # Run again
alembic downgrade base
alembic downgrade base  # Run again (no-op)
alembic upgrade head
```

## Troubleshooting

### Issue: Enum already exists

**Error**: `DuplicateObject: type "enumname" already exists`

**Solution**: This shouldn't happen with `checkfirst=True`, but if it does:

```sql
-- Check existing enums
SELECT typname FROM pg_type WHERE typtype = 'e';

-- Drop enum manually if needed
DROP TYPE enumname CASCADE;
```

### Issue: Enum in use

**Error**: `DependentObjectsStillExist: cannot drop type enumname because other objects depend on it`

**Solution**: Ensure tables are dropped before enums in downgrade():

```python
def downgrade() -> None:
    # Drop tables FIRST
    op.drop_table('table_using_enum')
    
    # Then drop enum
    my_enum.drop(op.get_bind(), checkfirst=True)
```

### Issue: Cannot drop enum that doesn't exist

**Error**: `UndefinedObject: type "enumname" does not exist`

**Solution**: Use `checkfirst=True` when dropping enums:

```python
my_enum.drop(op.get_bind(), checkfirst=True)  # Won't error if doesn't exist
```

### Issue: Async driver error in migrations

**Error**: `The asyncio extension requires an async driver to be used`

**Solution**: The env.py automatically converts asyncpg URLs to psycopg2. Ensure:

1. `psycopg2` or `psycopg2-binary` is installed:
   - **Production**: Use `pip install psycopg2` (built from source, better performance and reliability)
   - **Development/Testing**: Use `pip install psycopg2-binary` (pre-compiled, easier installation)
   - **Note**: `psycopg2-binary` is NOT recommended for production due to potential compatibility and performance issues
2. The DATABASE_URL is set correctly
3. The env.py is converting the URL properly

## Best Practices Summary

1. ✅ **DO** define all enums as top-level module variables
2. ✅ **DO** use `create_type=False` on enum definitions
3. ✅ **DO** explicitly create enums with `checkfirst=True` before tables
4. ✅ **DO** explicitly drop enums with `checkfirst=True` after tables
5. ✅ **DO** test migrations locally before committing
6. ✅ **DO** test both upgrade and downgrade paths
7. ✅ **DO** verify idempotency by running migrations twice

8. ❌ **DON'T** use inline `sa.Enum()` in table columns
9. ❌ **DON'T** forget to import `postgresql` from `sqlalchemy.dialects`
10. ❌ **DON'T** drop enums before dropping dependent tables
11. ❌ **DON'T** skip testing downgrade migrations
12. ❌ **DON'T** commit migrations without verifying they work

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy PostgreSQL Types](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [PostgreSQL ENUM Type](https://www.postgresql.org/docs/current/datatype-enum.html)
