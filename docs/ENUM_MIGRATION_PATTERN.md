# PostgreSQL ENUM Handling Pattern for Alembic Migrations

## Problem
When using PostgreSQL ENUMs in Alembic migrations, improper handling can lead to errors such as:
- "type already exists" errors when running migrations
- "type does not exist" errors when rolling back migrations
- ENUMs not being cleaned up properly during downgrades

## Solution: Proper ENUM Handling Pattern

All Alembic migrations that use PostgreSQL ENUM types MUST follow this pattern to prevent duplicate type errors and ensure proper cleanup.

### 1. Define ENUMs as Top-Level Instances

Define all ENUM types as module-level variables at the top of your migration file, NOT inline in table definitions.

```python
from sqlalchemy.dialects import postgresql

# ✅ CORRECT: Top-level ENUM instances
wallet_provider_enum = postgresql.ENUM('fincra', 'paystack', 'flutterwave', name='wallet_provider')
project_status_enum = postgresql.ENUM('draft', 'pending', 'active', name='project_status')

# ❌ INCORRECT: Don't use inline sa.Enum in column definitions
# sa.Column('status', sa.Enum('draft', 'pending', name='status'), nullable=False)
```

### 2. Create ENUMs BEFORE Tables in upgrade()

In the `upgrade()` function, create all ENUM types BEFORE creating any tables that use them. Always use `checkfirst=True` to prevent errors if the type already exists.

```python
def upgrade() -> None:
    # ✅ CORRECT: Create ENUMs BEFORE tables
    wallet_provider_enum.create(op.get_bind(), checkfirst=True)
    project_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Then create tables
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('status', project_status_enum, nullable=False),
        # ... other columns
    )
```

### 3. Reference Top-Level ENUM Instances in Columns

When defining table columns, reference the top-level ENUM instance, NOT an inline definition.

```python
# ✅ CORRECT: Reference the top-level instance
sa.Column('status', project_status_enum, nullable=False)

# ❌ INCORRECT: Don't create inline ENUMs
sa.Column('status', sa.Enum('draft', 'pending', name='project_status'), nullable=False)
sa.Column('status', postgresql.ENUM('draft', 'pending', name='project_status'), nullable=False)
```

### 4. Drop ENUMs AFTER Tables in downgrade()

In the `downgrade()` function, drop all tables that use ENUMs BEFORE dropping the ENUM types themselves. Always use `checkfirst=True` to prevent errors if the type doesn't exist.

```python
def downgrade() -> None:
    # ✅ CORRECT: Drop tables FIRST
    op.drop_table('projects')
    op.drop_table('users')
    
    # Then drop ENUMs AFTER all tables
    project_status_enum.drop(op.get_bind(), checkfirst=True)
    wallet_provider_enum.drop(op.get_bind(), checkfirst=True)
```

## Complete Example

```python
"""Create projects table with proper ENUM handling

Revision ID: abc123
Revises: xyz789
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'abc123'
down_revision: Union[str, None] = 'xyz789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define all ENUMs as top-level instances
project_status_enum = postgresql.ENUM(
    'draft', 'pending', 'active', 'completed', 
    name='project_status'
)
milestone_status_enum = postgresql.ENUM(
    'pending', 'in_progress', 'completed', 
    name='milestone_status'
)


def upgrade() -> None:
    # Create ENUM types BEFORE tables
    project_status_enum.create(op.get_bind(), checkfirst=True)
    milestone_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create tables that use the ENUMs
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('status', project_status_enum, nullable=False),
        # ... other columns
    )
    
    op.create_table(
        'milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True)),
        sa.Column('status', milestone_status_enum, nullable=False),
        # ... other columns
    )


def downgrade() -> None:
    # Drop tables BEFORE ENUMs
    op.drop_table('milestones')
    op.drop_table('projects')
    
    # Drop ENUM types AFTER tables
    milestone_status_enum.drop(op.get_bind(), checkfirst=True)
    project_status_enum.drop(op.get_bind(), checkfirst=True)
```

## ENUMs Used in This Project

The following ENUM types are defined in this project's models:

| ENUM Type | Values | Used In Tables |
|-----------|--------|----------------|
| `wallet_provider` | fincra, paystack, flutterwave | link_tokens, wallet_registry, wallet_balance_snapshot |
| `project_status` | draft, pending, active, in_progress, completed, disputed, cancelled, refunded | projects |
| `milestone_status` | pending, in_progress, completed, approved, rejected, disputed | milestones |
| `transaction_type` | deposit, withdrawal, escrow_hold, escrow_release, refund, fee, commission | transactions |
| `transaction_status` | pending, processing, completed, failed, cancelled, refunded | transactions |
| `kyc_type` | kyc, kyb | kyc |
| `kyc_status` | pending, approved, rejected | kyc |
| `user_role` | admin, client, freelancer | users |
| `hold_status` | active, released, captured | holds |
| `ledger_transaction_type` | debit, credit | ledger_entries |

## Checklist for Creating New Migrations with ENUMs

When creating a new migration that involves ENUM types, ensure:

- [ ] All ENUMs are defined as top-level `postgresql.ENUM()` instances
- [ ] `.create(op.get_bind(), checkfirst=True)` is called for each ENUM BEFORE creating tables in `upgrade()`
- [ ] Table columns reference the top-level ENUM instances (no inline definitions)
- [ ] `.drop(op.get_bind(), checkfirst=True)` is called for each ENUM AFTER dropping tables in `downgrade()`
- [ ] The migration has been tested with both `alembic upgrade` and `alembic downgrade`

## Testing Migrations

Always test your migrations in both directions:

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

This ensures that:
1. ENUMs are created correctly
2. Tables are created with proper ENUM columns
3. Downgrades clean up ENUMs properly
4. Re-running upgrades doesn't cause "type already exists" errors

## References

- [SQLAlchemy PostgreSQL ENUM Documentation](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#postgresql-enum-types)
- [Alembic Operations Reference](https://alembic.sqlalchemy.org/en/latest/ops.html)
- Migration: `45182f983623_create_all_database_tables_with_proper_.py` - Reference implementation
