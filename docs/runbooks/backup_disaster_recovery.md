# Backup and Disaster Recovery Guide

## Overview

This guide provides procedures for backing up the Amani Backend application data and recovering from various disaster scenarios.

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Backup Procedures](#backup-procedures)
3. [Restore Procedures](#restore-procedures)
4. [Disaster Scenarios](#disaster-scenarios)
5. [Testing and Validation](#testing-and-validation)
6. [Automation](#automation)

---

## Backup Strategy

### What We Back Up

1. **Database** (Primary)
   - PostgreSQL database containing all application data
   - User accounts, projects, milestones, transactions
   - Wallet registry, balances, events

2. **Application Logs** (Secondary)
   - Stored in `logs/` directory
   - Rotated daily, kept for 30 days

3. **Configuration** (Version Controlled)
   - Application configuration files in Git
   - Environment-specific settings documented

### Backup Schedule

| Backup Type | Frequency | Retention | Storage Location |
|-------------|-----------|-----------|------------------|
| Full Database | Daily at 2 AM UTC | 30 days | S3/Cloud Storage |
| Database Snapshot | Before migrations | 7 days | Local/Cloud |
| Transaction Logs | Continuous (if enabled) | 7 days | Cloud Storage |
| Application Logs | Daily | 30 days | Local/Cloud |

### Backup Retention Policy

- **Daily backups**: Keep for 30 days
- **Weekly backups**: Keep for 3 months (every Sunday)
- **Monthly backups**: Keep for 1 year (first of month)
- **Critical backups**: Keep indefinitely (pre-major-release, pre-migration)

### Recovery Time Objective (RTO)

Target time to restore service:
- **Database corruption**: 15 minutes (restore from backup)
- **Complete infrastructure loss**: 2 hours (rebuild infrastructure + restore)
- **Data center failure**: 4 hours (switch to DR site + restore)

### Recovery Point Objective (RPO)

Maximum acceptable data loss:
- **Production**: 24 hours (daily backups)
- **Critical operations**: 5 minutes (with transaction logs)

---

## Backup Procedures

### Manual Database Backup

Use the provided backup script:

```bash
# Basic backup to default location (./backups)
./scripts/backup_database.sh

# Backup to specific directory
./scripts/backup_database.sh /path/to/backup/directory

# What it does:
# 1. Reads DATABASE_URL from .env
# 2. Creates compressed backup with timestamp
# 3. Removes backups older than 30 days
# 4. Reports backup size
```

### Manual Backup to Cloud Storage

#### AWS S3
```bash
# Create backup
./scripts/backup_database.sh

# Upload to S3
aws s3 cp backups/amani_backup_$(date +%Y%m%d)_*.sql.gz \
  s3://your-backup-bucket/database/

# Verify upload
aws s3 ls s3://your-backup-bucket/database/
```

#### Google Cloud Storage
```bash
# Create backup
./scripts/backup_database.sh

# Upload to GCS
gsutil cp backups/amani_backup_$(date +%Y%m%d)_*.sql.gz \
  gs://your-backup-bucket/database/

# Verify upload
gsutil ls gs://your-backup-bucket/database/
```

#### Azure Blob Storage
```bash
# Create backup
./scripts/backup_database.sh

# Upload to Azure
az storage blob upload \
  --account-name youraccountname \
  --container-name backups \
  --name amani_backup_$(date +%Y%m%d)_*.sql.gz \
  --file backups/amani_backup_$(date +%Y%m%d)_*.sql.gz
```

### Pre-Migration Backup

**Always** create a backup before running migrations:

```bash
# Create labeled backup
./scripts/backup_database.sh ./backups
mv backups/amani_backup_*.sql.gz backups/pre_migration_$(date +%Y%m%d_%H%M%S).sql.gz

# Run migrations
alembic upgrade head

# Verify
curl http://localhost:8000/api/v1/health
```

### Configuration Backup

Configuration is version-controlled in Git:

```bash
# Ensure all config changes are committed
git status
git add .
git commit -m "Update configuration"
git push
```

---

## Restore Procedures

### Database Restore

Use the provided restore script:

```bash
# Restore from backup file
./scripts/restore_database.sh backups/amani_backup_20250122_020000.sql.gz

# What it does:
# 1. Confirms you want to proceed (destructive operation)
# 2. Decompresses backup if needed
# 3. Terminates existing database connections
# 4. Restores database from backup
# 5. Verifies table count
# 6. Reminds you to run migrations if needed
```

### Step-by-Step Manual Restore

If the script fails or you need manual control:

```bash
# 1. Stop application
docker-compose stop app

# 2. Decompress backup
gunzip backups/amani_backup_20250122_020000.sql.gz

# 3. Terminate database connections
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '<dbname>' AND pid <> pg_backend_pid();"

# 4. Restore database
pg_restore \
  --host=<host> \
  --port=<port> \
  --username=<user> \
  --dbname=<dbname> \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  --verbose \
  backups/amani_backup_20250122_020000.sql

# 5. Run migrations (if needed)
alembic upgrade head

# 6. Start application
docker-compose start app

# 7. Verify
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/readiness
```

### Point-in-Time Recovery (If Transaction Logs Enabled)

```bash
# 1. Restore base backup
./scripts/restore_database.sh backups/base_backup.sql.gz

# 2. Apply transaction logs up to target time
pg_waldump <wal_file> | psql $DATABASE_URL

# 3. Verify data
psql $DATABASE_URL -c "SELECT MAX(created_at) FROM transactions;"
```

---

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms**: Application errors, data inconsistencies, failed queries

**Recovery Steps**:

1. **Stop application** to prevent further corruption
   ```bash
   docker-compose stop app
   ```

2. **Assess damage**
   ```bash
   psql $DATABASE_URL -c "SELECT pg_database_size(current_database());"
   ```

3. **Restore from latest backup**
   ```bash
   ./scripts/restore_database.sh backups/amani_backup_<latest>.sql.gz
   ```

4. **Verify data integrity**
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM transactions;"
   ```

5. **Start application**
   ```bash
   docker-compose start app
   curl http://localhost:8000/api/v1/health
   ```

**Expected Downtime**: 15-30 minutes

---

### Scenario 2: Accidental Data Deletion

**Symptoms**: Missing records, user reports of lost data

**Recovery Steps**:

1. **Identify scope**
   - What was deleted?
   - When did it occur?
   - Which tables affected?

2. **Stop further changes**
   ```bash
   docker-compose stop app
   ```

3. **Find appropriate backup**
   ```bash
   # List recent backups
   ls -lh backups/ | tail -10
   ```

4. **Extract deleted data** from backup
   ```bash
   # Restore to temporary database
   createdb temp_restore
   pg_restore -d temp_restore backups/amani_backup_<before_deletion>.sql.gz
   
   # Extract deleted records
   psql temp_restore -c "COPY (SELECT * FROM users WHERE id IN (<deleted_ids>)) TO STDOUT;" | \
   psql $DATABASE_URL -c "COPY users FROM STDIN;"
   
   # Drop temporary database
   dropdb temp_restore
   ```

5. **Verify restoration**
   ```bash
   psql $DATABASE_URL -c "SELECT * FROM users WHERE id IN (<deleted_ids>);"
   ```

6. **Resume operations**
   ```bash
   docker-compose start app
   ```

**Expected Downtime**: 30-60 minutes

---

### Scenario 3: Complete Infrastructure Loss

**Symptoms**: Server unreachable, data center down, cloud region failure

**Recovery Steps**:

1. **Provision new infrastructure**
   ```bash
   # Use Infrastructure as Code (Terraform, CloudFormation, etc.)
   terraform apply
   ```

2. **Deploy application**
   ```bash
   git clone https://github.com/praiseunite/amani-backend.git
   cd amani-backend
   cp .env.example .env
   # Edit .env with new credentials
   docker-compose up -d
   ```

3. **Restore database**
   ```bash
   # Download latest backup from cloud storage
   aws s3 cp s3://your-backup-bucket/database/latest.sql.gz backups/
   
   # Restore
   ./scripts/restore_database.sh backups/latest.sql.gz
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Verify all services**
   ```bash
   curl http://new-host:8000/api/v1/health
   curl http://new-host:8000/api/v1/readiness
   ```

6. **Update DNS** to point to new infrastructure

7. **Monitor closely** for 24-48 hours

**Expected Downtime**: 2-4 hours

---

### Scenario 4: Failed Migration

**Symptoms**: Application won't start after migration, database errors

**Recovery Steps**:

1. **Stop application**
   ```bash
   docker-compose stop app
   ```

2. **Rollback migration**
   ```bash
   alembic downgrade -1
   ```

3. **If rollback fails, restore pre-migration backup**
   ```bash
   ./scripts/restore_database.sh backups/pre_migration_*.sql.gz
   ```

4. **Verify database state**
   ```bash
   psql $DATABASE_URL -c "SELECT version_num FROM alembic_version;"
   ```

5. **Fix migration script** and test in staging

6. **Re-run migration**
   ```bash
   alembic upgrade head
   ```

7. **Start application**
   ```bash
   docker-compose start app
   ```

**Expected Downtime**: 15-30 minutes

---

## Testing and Validation

### Monthly Backup Testing

Perform these tests monthly to ensure backups are viable:

1. **Backup Creation Test**
   ```bash
   ./scripts/backup_database.sh /tmp/test_backup
   ls -lh /tmp/test_backup/
   ```

2. **Backup Integrity Test**
   ```bash
   # Verify backup file is not corrupted
   gunzip -t /tmp/test_backup/amani_backup_*.sql.gz
   echo $?  # Should be 0
   ```

3. **Restore Test** (Use test environment)
   ```bash
   # Restore to test database
   export DATABASE_URL="postgresql+asyncpg://test:test@localhost/test_restore"
   ./scripts/restore_database.sh /tmp/test_backup/amani_backup_*.sql.gz
   
   # Verify data
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   ```

4. **Document Results**
   - Date tested: ___________
   - Backup size: ___________
   - Restore time: ___________
   - Issues found: ___________

### Disaster Recovery Drill

Perform annually:

1. Schedule DR drill (inform team)
2. Simulate complete infrastructure loss
3. Follow recovery procedures
4. Time each step
5. Document issues and improvements
6. Update procedures based on learnings

---

## Automation

### Automated Daily Backups

#### Using Cron (Linux)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/amani-backend && ./scripts/backup_database.sh /path/to/backups

# Add upload to cloud storage
0 3 * * * aws s3 sync /path/to/backups s3://your-backup-bucket/database/
```

#### Using systemd Timer (Linux)

Create `/etc/systemd/system/amani-backup.service`:
```ini
[Unit]
Description=Amani Database Backup

[Service]
Type=oneshot
ExecStart=/path/to/amani-backend/scripts/backup_database.sh /path/to/backups
User=amani
Group=amani
```

Create `/etc/systemd/system/amani-backup.timer`:
```ini
[Unit]
Description=Daily Amani Backup

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable amani-backup.timer
sudo systemctl start amani-backup.timer
```

#### Using GitHub Actions (Cloud)

See `.github/workflows/backup.yml` for automated backups triggered on schedule.

### Backup Monitoring

Add alerts for backup failures:

```python
# In backup script, send alert on failure
from app.core.alerts import send_slack_alert

if backup_failed:
    await send_slack_alert(
        message="Database backup failed!",
        severity="critical",
        context={"backup_file": backup_path}
    )
```

---

## Backup Checklist

Use this checklist for manual backups:

- [ ] Backup created successfully
- [ ] Backup compressed
- [ ] Backup size verified (not 0 bytes)
- [ ] Backup uploaded to cloud storage
- [ ] Old backups cleaned up
- [ ] Backup integrity tested
- [ ] Backup documented in log

---

## Additional Resources

- [Database Setup Guide](../DATABASE_SETUP.md)
- [Migration Runbook](migration_runbook.md)
- [Incident Response Checklist](incident_response_checklist.md)
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)

---

## Emergency Contacts

| Service | Contact | Phone | Email |
|---------|---------|-------|-------|
| Database (Supabase) | Support | - | support@supabase.com |
| DevOps Team | On-Call | _______ | _______ |
| AWS Support | - | - | aws-support@ |

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-01-22 | 1.0 | Initial version | System |
