# Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered in the Amani Backend application, covering deployment, database, API, and integration problems.

## Table of Contents

1. [Application Startup Issues](#application-startup-issues)
2. [Database Connection Problems](#database-connection-problems)
3. [Migration Issues](#migration-issues)
4. [API Errors](#api-errors)
5. [Integration Test Failures](#integration-test-failures)
6. [Performance Issues](#performance-issues)
7. [CI/CD Pipeline Issues](#cicd-pipeline-issues)
8. [Health Check Failures](#health-check-failures)

---

## Application Startup Issues

### Issue: Application fails to start with "ModuleNotFoundError"

**Symptoms**: ImportError or ModuleNotFoundError on startup

**Diagnosis**:
```bash
python -c "import app; print(app.__file__)"
```

**Solutions**:
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. Verify Python version:
   ```bash
   python --version  # Should be 3.11+
   ```

3. Check virtual environment:
   ```bash
   which python
   pip list
   ```

---

### Issue: "SECRET_KEY not configured" error

**Symptoms**: Application startup fails with configuration error

**Solutions**:
1. Create `.env` file from example:
   ```bash
   cp .env.example .env
   ```

2. Set required environment variables:
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
   ```

3. Generate secure secret key:
   ```python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

---

## Database Connection Problems

### Issue: "Connection refused" to database

**Symptoms**: Application cannot connect to PostgreSQL

**Diagnosis**:
```bash
# Test database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check if PostgreSQL is running
pg_isready -h localhost -p 5432
```

**Solutions**:

1. **PostgreSQL not running**:
   ```bash
   # Start PostgreSQL (Docker)
   docker start postgres
   
   # Or start local PostgreSQL
   sudo systemctl start postgresql
   ```

2. **Wrong connection string**:
   ```bash
   # Verify DATABASE_URL format
   echo $DATABASE_URL
   # Should be: postgresql+asyncpg://user:pass@host:port/dbname
   ```

3. **Firewall blocking connection**:
   ```bash
   # Check if port is accessible
   nc -zv localhost 5432
   ```

4. **Database doesn't exist**:
   ```bash
   # Create database
   createdb -h localhost -U postgres amani_db
   ```

---

### Issue: "Too many connections" error

**Symptoms**: Database refuses new connections

**Diagnosis**:
```sql
SELECT count(*) FROM pg_stat_activity;
SELECT * FROM pg_stat_activity WHERE datname = 'your_db_name';
```

**Solutions**:

1. **Close idle connections**:
   ```sql
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE datname = 'your_db_name' 
   AND state = 'idle' 
   AND state_change < now() - interval '5 minutes';
   ```

2. **Adjust connection pool**:
   ```python
   # In app/core/database.py
   engine = create_async_engine(
       settings.DATABASE_URL,
       pool_size=5,  # Reduce if needed
       max_overflow=10
   )
   ```

3. **Increase PostgreSQL max_connections**:
   ```sql
   ALTER SYSTEM SET max_connections = 200;
   -- Restart PostgreSQL
   ```

---

## Migration Issues

### Issue: Migration fails with "duplicate key value violates unique constraint"

**Symptoms**: Migration upgrade fails midway

**Diagnosis**:
```bash
# Check current migration state
alembic current

# View migration history
alembic history
```

**Solutions**:

1. **Clean duplicate data before migration**:
   ```sql
   -- Example: Find duplicates in wallet_registry
   SELECT user_id, provider, provider_account_id, COUNT(*) 
   FROM wallet_registry 
   GROUP BY user_id, provider, provider_account_id 
   HAVING COUNT(*) > 1;
   
   -- Remove duplicates (keep one)
   DELETE FROM wallet_registry 
   WHERE id NOT IN (
       SELECT MIN(id) 
       FROM wallet_registry 
       GROUP BY user_id, provider, provider_account_id
   );
   ```

2. **Rollback and retry**:
   ```bash
   alembic downgrade -1
   # Fix data issues
   alembic upgrade head
   ```

---

### Issue: "Can't locate revision" error

**Symptoms**: Alembic can't find migration version

**Solutions**:

1. **Check alembic_version table**:
   ```sql
   SELECT * FROM alembic_version;
   ```

2. **Stamp database with correct version**:
   ```bash
   # If database is at head but alembic doesn't know
   alembic stamp head
   
   # Or stamp specific version
   alembic stamp 20251121_081650
   ```

3. **Reset and reapply migrations** (development only):
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

---

## API Errors

### Issue: 401 Unauthorized errors

**Symptoms**: API requests fail with authentication error

**Solutions**:

1. **Check JWT token**:
   ```bash
   # Verify token is being sent
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/protected-endpoint
   ```

2. **Verify SECRET_KEY matches**:
   ```bash
   echo $SECRET_KEY
   # Must match the key used to generate tokens
   ```

3. **Check token expiration**:
   ```python
   # In python shell
   import jwt
   token = "your.jwt.token"
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(decoded['exp'])  # Expiration timestamp
   ```

---

### Issue: 422 Validation Error

**Symptoms**: Request fails with validation error

**Diagnosis**: Check response body for details

**Solutions**:

1. **Review request payload**:
   ```bash
   # Enable verbose mode
   curl -v -X POST http://localhost:8000/api/v1/endpoint \
     -H "Content-Type: application/json" \
     -d '{"field": "value"}'
   ```

2. **Check API documentation**:
   - Visit http://localhost:8000/docs
   - Review required fields and formats

3. **Validate against schema**:
   ```python
   from app.schemas.your_schema import YourSchema
   data = {"field": "value"}
   validated = YourSchema(**data)
   ```

---

### Issue: 500 Internal Server Error

**Symptoms**: API returns 500 error

**Diagnosis**:
```bash
# Check application logs
tail -f logs/app.log

# Or in Docker
docker logs amani-backend
```

**Solutions**:

1. **Check stack trace in logs**
2. **Verify database connection**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. **Review recent code changes**
4. **Check environment configuration**

---

## Integration Test Failures

### Issue: Integration tests fail with "TEST_DATABASE_URL not set"

**Solutions**:

1. **Set test database URL**:
   ```bash
   export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost/test_db"
   ```

2. **Run tests with environment**:
   ```bash
   TEST_DATABASE_URL="postgresql+asyncpg://..." pytest tests/integration/
   ```

---

### Issue: Integration tests fail with "relation does not exist"

**Symptoms**: Tests fail because database tables don't exist

**Solutions**:

1. **Run migrations first**:
   ```bash
   DATABASE_URL=$TEST_DATABASE_URL alembic upgrade head
   ```

2. **In CI, check migration job ran**:
   - Review GitHub Actions logs
   - Verify PostgreSQL service started

---

### Issue: Concurrency test failures

**Symptoms**: Tests fail intermittently or under load

**Solutions**:

1. **Check for race conditions**:
   ```python
   # Add debugging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Verify idempotency logic**:
   - Check idempotency_key is unique
   - Verify duplicate detection works

3. **Increase test timeouts**:
   ```python
   @pytest.mark.timeout(30)  # Increase timeout
   async def test_concurrent_operation():
       ...
   ```

---

## Performance Issues

### Issue: Slow API responses

**Diagnosis**:
```bash
# Measure response time
time curl http://localhost:8000/api/v1/endpoint

# Check database query times
# In PostgreSQL
SET log_min_duration_statement = 100;  # Log queries > 100ms
```

**Solutions**:

1. **Add database indexes**:
   ```sql
   CREATE INDEX idx_wallet_registry_user_id ON wallet_registry(user_id);
   ```

2. **Enable connection pooling**:
   - Already configured in `app/core/database.py`
   - Adjust pool_size if needed

3. **Profile slow queries**:
   ```sql
   EXPLAIN ANALYZE SELECT ...;
   ```

4. **Check N+1 queries**:
   - Use SQLAlchemy eager loading
   - Review API endpoint queries

---

### Issue: High memory usage

**Diagnosis**:
```bash
# Monitor memory
top -p $(pgrep -f "uvicorn")

# Check connection pool
SELECT count(*) FROM pg_stat_activity;
```

**Solutions**:

1. **Reduce connection pool size**
2. **Enable result streaming for large queries**
3. **Add pagination to list endpoints**

---

## CI/CD Pipeline Issues

### Issue: CI build fails on lint step

**Symptoms**: Black or Flake8 failures

**Solutions**:

1. **Run formatters locally**:
   ```bash
   black app/ tests/
   ```

2. **Fix lint issues**:
   ```bash
   flake8 app/ tests/
   ```

3. **Auto-fix common issues**:
   ```bash
   black app/ tests/
   autopep8 --in-place --recursive app/ tests/
   ```

---

### Issue: CI integration tests fail

**Symptoms**: Tests pass locally but fail in CI

**Solutions**:

1. **Check PostgreSQL service**:
   - Verify service started in GitHub Actions
   - Check health check passes

2. **Review environment variables**:
   - Ensure all required vars set in CI
   - Check for typos in workflow file

3. **Check migration step**:
   ```yaml
   # In .github/workflows/ci.yml
   - name: Run Alembic migrations
     env:
       DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
     run: alembic upgrade head
   ```

---

### Issue: Coverage below threshold

**Symptoms**: CI fails due to low test coverage

**Solutions**:

1. **Run coverage locally**:
   ```bash
   pytest --cov=app --cov-report=term-missing --cov-fail-under=85
   ```

2. **Identify uncovered code**:
   ```bash
   pytest --cov=app --cov-report=html
   open htmlcov/index.html
   ```

3. **Add missing tests** for uncovered code

---

## Health Check Failures

### Issue: /health endpoint returns unhealthy

**Symptoms**: Health check shows "unhealthy" status

**Diagnosis**:
```bash
curl http://localhost:8000/api/v1/health | jq .
```

**Solutions**:

1. **Database check failing**:
   ```bash
   # Test database connection
   psql $DATABASE_URL -c "SELECT 1;"
   ```

2. **Migrations not applied**:
   ```bash
   alembic upgrade head
   ```

3. **Check individual health checks**:
   ```json
   {
     "checks": {
       "database": {"status": "unhealthy", "message": "..."},
       "migrations": {"status": "unhealthy", "message": "..."}
     }
   }
   ```

---

### Issue: /readiness endpoint fails

**Symptoms**: Readiness check fails, pod not ready

**Solutions**:

1. **Check required tables exist**:
   ```sql
   SELECT tablename FROM pg_tables 
   WHERE schemaname = 'public' 
   AND tablename IN ('users', 'wallet_registry', 'wallet_balance_snapshot', 'wallet_transaction_event');
   ```

2. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Review readiness check logs**:
   ```bash
   curl http://localhost:8000/api/v1/readiness | jq .
   ```

---

## Getting More Help

### Debug Mode

Enable debug mode for more verbose logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python -m app.main
```

### Useful Commands

```bash
# Check application version
curl http://localhost:8000/api/v1/ | jq .version

# Test database connectivity
python -c "from app.core.database import engine; import asyncio; asyncio.run(engine.connect())"

# List all migrations
alembic history

# Check current migration
alembic current
```

### Logs and Monitoring

- Application logs: `logs/app.log`
- Database logs: Check PostgreSQL logs
- CI logs: GitHub Actions workflow logs

### Contact Support

- Development Team: [Contact info]
- Database Admin: [Contact info]
- DevOps Team: [Contact info]

### Additional Resources

- [README.md](../../README.md)
- [Migration Runbook](./migration_runbook.md)
- [Database Setup Guide](../DATABASE_SETUP.md)
- [API Documentation](http://localhost:8000/docs)
