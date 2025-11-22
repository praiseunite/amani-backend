# Database Migration Guide

Complete guide for managing database migrations using Alembic.

## Table of Contents
- [Understanding Migrations](#understanding-migrations)
- [Migration Commands](#migration-commands)
- [Creating Migrations](#creating-migrations)
- [Testing Migrations](#testing-migrations)
- [Rollback Procedures](#rollback-procedures)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Understanding Migrations

Alembic is used to manage database schema changes. Migrations are version-controlled database changes that can be applied and rolled back.

### Current Migration

The project currently has one comprehensive migration:

- **001_initial_schema**: Creates all tables with proper enum handling, indexes, and constraints

### Migration Files

Migrations are stored in:
```
alembic/
├── versions/
│   └── 001_initial_schema.py
├── env.py
└── script.py.mpl
```

## Migration Commands

### Check Current Version

```bash
# Show current database migration version
alembic current

# Example output:
# 001_initial_schema (head)
```

### View Migration History

```bash
# Show all migrations
alembic history

# Show verbose history
alembic history --verbose

# Show history with date ranges
alembic history -r-3:head
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific version
alembic upgrade 001_initial_schema

# Upgrade one version forward
alembic upgrade +1

# Dry run (show SQL without executing)
alembic upgrade head --sql
```

### Rollback Migrations

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 001_initial_schema

# Downgrade to base (remove all migrations)
alembic downgrade base

# Dry run rollback
alembic downgrade -1 --sql
```

## Creating Migrations

### Auto-Generate Migration

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Add new column to users table"

# Review the generated file in alembic/versions/
# Edit if necessary before applying
```

### Manual Migration

```bash
# Create empty migration file
alembic revision -m "Custom migration description"

# Edit the generated file with your changes
```

### Migration File Structure

```python
"""Migration description

Revision ID: abc123
Revises: previous_revision
Create Date: 2025-11-22 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    """Apply migration."""
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False)
    )

def downgrade():
    """Rollback migration."""
    op.drop_table('new_table')
```

## Testing Migrations

### Before Deploying

Always test migrations before deploying to production:

```bash
# 1. Backup database
pg_dump -U username -d database_name > backup.sql

# 2. Test upgrade
alembic upgrade head

# 3. Verify tables and data
psql -U username -d database_name -c "\dt"
psql -U username -d database_name -c "SELECT * FROM your_table LIMIT 5;"

# 4. Test downgrade
alembic downgrade -1

# 5. Verify rollback worked
psql -U username -d database_name -c "\dt"

# 6. Re-apply upgrade
alembic upgrade head

# 7. Run application tests
pytest

# 8. If all good, apply to staging/production
```

### Testing on Staging

```bash
# Set staging database URL
export DATABASE_URL="postgresql+asyncpg://user:pass@staging-db:5432/db"

# Run migrations
alembic upgrade head

# Run tests
pytest

# Check application health
curl https://staging.yourdomain.com/api/v1/health
```

## Rollback Procedures

### Emergency Rollback

If a migration causes issues in production:

```bash
# 1. Immediately rollback the migration
alembic downgrade -1

# 2. Restart application
systemctl restart amani-backend

# 3. Verify application is working
curl https://api.yourdomain.com/api/v1/health

# 4. Check logs for errors
journalctl -u amani-backend -n 100
```

### Planned Rollback

For planned rollbacks during maintenance:

```bash
# 1. Put application in maintenance mode (if applicable)
# 2. Stop application
systemctl stop amani-backend

# 3. Backup database
pg_dump -U username -d database_name > backup_before_rollback.sql

# 4. Rollback migration
alembic downgrade -1

# 5. Start application
systemctl start amani-backend

# 6. Verify health
curl https://api.yourdomain.com/api/v1/health
```

### Rollback Documentation

For the current migration (001_initial_schema):

**Upgrade**: Creates all tables with enums, indexes, and constraints
**Downgrade**: Drops all tables and enums

**Tables Created**:
- users
- projects
- milestones
- transactions
- kyc
- wallet_registry
- wallet_balance_snapshot
- wallet_transaction_event
- holds
- ledger_entries
- link_tokens

**Rollback Impact**:
- All data in these tables will be lost
- Application will not function without these tables
- Requires re-running upgrade to restore

**Rollback Command**:
```bash
alembic downgrade base
```

## Best Practices

### Migration Development

1. **Always test locally first**
   ```bash
   # Create test database
   createdb test_amani
   
   # Run migrations
   DATABASE_URL=postgresql+asyncpg://localhost/test_amani alembic upgrade head
   ```

2. **Review auto-generated migrations**
   - Auto-generation is helpful but not perfect
   - Always review and edit generated files
   - Ensure indexes and constraints are included

3. **Make migrations atomic**
   - Each migration should be a single logical change
   - Don't combine unrelated changes
   - Keep migrations small and focused

4. **Write reversible migrations**
   - Always implement `downgrade()` function
   - Test rollback before deploying
   - Document any data loss in downgrade

5. **Use transactions**
   - Most migrations run in a transaction by default
   - For data migrations, consider manual transaction control

### Enum Handling

Enums require special handling in PostgreSQL:

```python
# Create enum with checkfirst
user_role = postgresql.ENUM('admin', 'client', 'freelancer', 
                            name='userrole', create_type=False)

def upgrade():
    # Create enum type
    user_role.create(op.get_bind(), checkfirst=True)
    
    # Use enum in table
    op.create_table('users',
        sa.Column('role', user_role, nullable=False)
    )

def downgrade():
    op.drop_table('users')
    # Drop enum type
    user_role.drop(op.get_bind(), checkfirst=True)
```

### Data Migrations

For migrations that change data:

```python
from sqlalchemy import table, column

def upgrade():
    # Get connection
    connection = op.get_bind()
    
    # Define table for data migration
    users = table('users',
        column('email'),
        column('normalized_email')
    )
    
    # Update data
    connection.execute(
        users.update().values(
            normalized_email=sa.func.lower(users.c.email)
        )
    )
```

### Index Management

```python
def upgrade():
    # Create index
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create composite index
    op.create_index('ix_projects_status_created', 'projects', 
                   ['status', 'created_at'])

def downgrade():
    op.drop_index('ix_projects_status_created')
    op.drop_index('ix_users_email')
```

## Troubleshooting

### Migration Already Applied

```bash
# Error: Target database is not up to date
# Solution: Check current version
alembic current

# If version is correct, stamp it
alembic stamp head
```

### Migration Conflicts

```bash
# Error: Multiple head revisions found
# Solution: Merge revisions
alembic merge heads -m "Merge migration branches"
```

### Enum Already Exists

```bash
# Error: type "enumname" already exists
# Solution: Use checkfirst=True when creating enums
# Or manually drop: DROP TYPE enumname CASCADE;
```

### Foreign Key Errors

```bash
# Error: Cannot add foreign key constraint
# Solution: Ensure referenced table/column exists first
# Create tables in correct order in migration
```

### Lock Timeout

```bash
# Error: Lock timeout on table
# Solution: 
# 1. Ensure no long-running queries
# 2. Run migration during low-traffic period
# 3. Increase lock timeout:
# SET lock_timeout = '10s';
```

### Rollback Failed

```bash
# If rollback fails:
# 1. Check error message
# 2. Manually fix database if needed
# 3. Force stamp to previous version:
alembic stamp -1

# 4. Manually clean up if necessary
psql -U user -d db -c "DROP TABLE IF EXISTS table_name CASCADE;"
```

### Database Out of Sync

```bash
# Check differences between models and database
alembic revision --autogenerate -m "Check differences"

# Review generated file for differences
# Apply or discard as needed
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Migration tested on local database
- [ ] Migration tested on staging database
- [ ] Rollback tested and documented
- [ ] Database backup scheduled
- [ ] Downtime window planned (if needed)
- [ ] Team notified of deployment
- [ ] Rollback plan documented

### Deployment Steps

```bash
# 1. Backup production database
pg_dump -U user -h prod-db -d amani_prod > backup_pre_migration.sql

# 2. Put app in maintenance mode (optional)
# 3. Stop application
systemctl stop amani-backend

# 4. Run migrations
alembic upgrade head

# 5. Start application
systemctl start amani-backend

# 6. Verify health
curl https://api.yourdomain.com/api/v1/health

# 7. Monitor logs
journalctl -u amani-backend -f

# 8. Run smoke tests
pytest tests/integration/

# 9. Remove maintenance mode
```

### Zero-Downtime Migrations

For large-scale deployments:

1. **Phase 1**: Add new columns (nullable)
2. **Phase 2**: Deploy application code that uses both old and new
3. **Phase 3**: Migrate data from old to new columns
4. **Phase 4**: Deploy application code that only uses new columns
5. **Phase 5**: Drop old columns

## Support

For migration issues:
- Check [Alembic Documentation](https://alembic.sqlalchemy.org/)
- GitHub Issues: https://github.com/praiseunite/amani-backend/issues
- Review logs: `journalctl -u amani-backend`
