# Database Migration Runbook

## Overview

This runbook provides step-by-step procedures for managing Alembic database migrations in the Amani Backend application, including verification, rollback, and troubleshooting.

## Prerequisites

- Access to the database (PostgreSQL)
- Python environment with dependencies installed
- DATABASE_URL environment variable configured
- Appropriate database privileges (DDL operations)

## Migration Files

Current migrations (in order):

1. `68db6a7fba94` - Initial migration with user, project, milestone, transaction
2. `db82de06f57d` - Add user role field
3. `4c876238cdeb` - Add OTP fields to user
4. `d8311371c01f` - Add integer primary keys and new tables
5. `20251120_140218` - Create wallet_registry with constraints
6. `20251121_073320` - Create wallet_balance_snapshot table
7. `20251121_081650` - Create wallet_transaction_event table

## Standard Migration Procedures

### Applying Migrations (Upgrade)

#### Production Deployment

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"

# 2. Check current migration state
alembic current

# 3. Review pending migrations
alembic history

# 4. Apply all pending migrations
alembic upgrade head

# 5. Verify migration completed
alembic current
```

#### Staging/Testing

```bash
# Use test database URL
export DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

# Apply migrations
alembic upgrade head
```

### Rolling Back Migrations (Downgrade)

#### Rollback Last Migration

```bash
# 1. Check current state
alembic current

# 2. Downgrade one step
alembic downgrade -1

# 3. Verify rollback
alembic current
```

#### Rollback to Specific Version

```bash
# Rollback to specific migration
alembic downgrade 20251121_073320

# Verify
alembic current
```

#### Complete Rollback (Emergency)

```bash
# WARNING: This will remove all tables and data!
# Only use in development/testing environments

alembic downgrade base
```

## Migration Verification

### Pre-Deployment Verification

Use the automated testing script:

```bash
# Run migration test script
./scripts/test_migrations.sh
```

This script will:
- Verify current migration state
- Apply all migrations
- Test rollback of last migration
- Re-apply last migration
- Show migration history

### Manual Verification Steps

1. **Check Migration Status**
   ```bash
   alembic current
   alembic history
   ```

2. **Verify Database Schema**
   ```sql
   -- Check wallet_registry table
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'wallet_registry';
   
   -- Check wallet_balance_snapshot table
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'wallet_balance_snapshot';
   
   -- Check wallet_transaction_event table
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'wallet_transaction_event';
   ```

3. **Verify Constraints**
   ```sql
   -- Check unique constraints
   SELECT constraint_name, table_name, constraint_type 
   FROM information_schema.table_constraints 
   WHERE table_name IN ('wallet_registry', 'wallet_balance_snapshot', 'wallet_transaction_event');
   
   -- Check indexes
   SELECT indexname, tablename, indexdef 
   FROM pg_indexes 
   WHERE tablename IN ('wallet_registry', 'wallet_balance_snapshot', 'wallet_transaction_event');
   ```

4. **Test Health Endpoint**
   ```bash
   curl http://localhost:8000/api/v1/health
   curl http://localhost:8000/api/v1/readiness
   ```

## Rollback Procedures

### Safe Rollback Process

1. **Prepare for Rollback**
   - Notify team of planned rollback
   - Backup current database state
   - Document reason for rollback

2. **Execute Rollback**
   ```bash
   # Stop application (if possible)
   # This prevents data corruption during rollback
   
   # Rollback migration
   alembic downgrade -1
   
   # Verify rollback completed
   alembic current
   ```

3. **Verify Application State**
   - Restart application
   - Check health endpoint
   - Verify core functionality
   - Monitor error logs

4. **Document Rollback**
   - Record migration version rolled back
   - Document issues encountered
   - Update team on status

### Emergency Rollback

If application is broken and needs immediate fix:

```bash
# 1. Identify problematic migration
alembic current

# 2. Rollback to last known good state
alembic downgrade <version_before_problem>

# 3. Restart application immediately

# 4. Verify basic functionality
curl http://localhost:8000/api/v1/ping

# 5. Investigate issue in lower environment
```

## Testing Migrations Locally

### Setup Local Test Database

```bash
# 1. Start PostgreSQL locally (Docker)
docker run --name test-postgres \
  -e POSTGRES_USER=test_user \
  -e POSTGRES_PASSWORD=test_pass \
  -e POSTGRES_DB=test_db \
  -p 5432:5432 \
  -d postgres:15

# 2. Set environment variable
export DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

# 3. Run migration tests
./scripts/test_migrations.sh
```

### Manual Testing Steps

```bash
# 1. Apply all migrations
alembic upgrade head

# 2. Run integration tests
pytest tests/integration/ -v -m integration

# 3. Test rollback
alembic downgrade -1

# 4. Re-apply
alembic upgrade +1

# 5. Verify with application
python -m app.main
```

## Troubleshooting

### Common Issues

#### Issue: "Can't locate revision identified by"

**Cause**: Migration history is out of sync with database

**Solution**:
```bash
# Check actual database state
alembic current

# Check expected migrations
alembic history

# If database has no alembic_version table, start fresh
alembic stamp head
```

#### Issue: "Target database is not up to date"

**Cause**: Database has pending migrations

**Solution**:
```bash
# Apply pending migrations
alembic upgrade head
```

#### Issue: Migration fails midway

**Cause**: Data constraint violation or SQL error

**Solution**:
```bash
# 1. Check error message for specific issue
alembic upgrade head 2>&1 | tee migration-error.log

# 2. Manually fix data if needed
psql $DATABASE_URL -c "UPDATE table SET column = value WHERE condition;"

# 3. Retry migration
alembic upgrade head

# 4. If still failing, rollback and investigate
alembic downgrade -1
```

#### Issue: Rollback fails

**Cause**: Downgrade logic incomplete or data dependencies

**Solution**:
```bash
# 1. Check the downgrade() function in the migration file
# 2. May need to manually reverse changes:

psql $DATABASE_URL << EOF
-- Example: manually drop constraint
ALTER TABLE wallet_registry DROP CONSTRAINT uq_wallet_registry_user_provider_account;
EOF

# 3. Update alembic_version manually
psql $DATABASE_URL -c "UPDATE alembic_version SET version_num = '<previous_version>';"
```

### Getting Help

1. Check migration file for comments and documentation
2. Review alembic logs: `alembic --help`
3. Consult team lead or database administrator
4. Check application logs for related errors

## Best Practices

1. **Always test migrations in non-production first**
   - Test in local environment
   - Verify in staging environment
   - Review with team before production

2. **Backup before migrations**
   ```bash
   pg_dump $DATABASE_URL > backup-$(date +%Y%m%d-%H%M%S).sql
   ```

3. **Monitor during migration**
   - Watch application logs
   - Monitor database CPU/memory
   - Check for lock contention

4. **Verify after migration**
   - Run health checks
   - Test critical functionality
   - Check integration tests

5. **Document changes**
   - Update this runbook with lessons learned
   - Note any manual interventions needed
   - Record timings for capacity planning

## CI/CD Integration

Migrations are automatically tested in CI:

1. **Pre-merge checks**:
   - Migration up/down tests run on every PR
   - Integration tests verify schema changes
   - Health checks confirm migration success

2. **Deployment**:
   - Migrations run before application deployment
   - Readiness probe verifies migration completion
   - Rollback procedures available if needed

## Monitoring

Key metrics to monitor:

- Migration execution time
- Database connection pool usage
- Query performance post-migration
- Application error rates
- Health/readiness check status

## Migration Approval Checklist

Before merging migration PRs:

- [ ] Migration tested locally with test script
- [ ] Rollback tested and verified
- [ ] Migration reviewed by team member
- [ ] Performance impact assessed
- [ ] Documentation updated
- [ ] CI tests passing
- [ ] Staging deployment successful

## Emergency Contacts

- Database Team: [Contact info]
- On-call Engineer: [Contact info]
- DevOps Lead: [Contact info]

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Project Database Setup Guide](../DATABASE_SETUP.md)
