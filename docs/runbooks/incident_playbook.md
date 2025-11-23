# Incident Playbook for Amani Backend

This document provides step-by-step procedures for responding to common incidents in the Amani Backend application.

## Table of Contents

1. [General Incident Response](#general-incident-response)
2. [Deployment Failures](#deployment-failures)
3. [Application Crashes](#application-crashes)
4. [Database Issues](#database-issues)
5. [Performance Degradation](#performance-degradation)
6. [Security Incidents](#security-incidents)
7. [Rollback Procedures](#rollback-procedures)

---

## General Incident Response

### Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **P0** | Critical - Complete outage | Immediate | Application down, database unavailable |
| **P1** | High - Major feature broken | < 15 minutes | Authentication failing, payments broken |
| **P2** | Medium - Feature degraded | < 1 hour | Slow response times, intermittent errors |
| **P3** | Low - Minor issue | < 4 hours | Cosmetic bugs, non-critical features |

### Initial Response Steps

1. **Acknowledge the incident**
   - Acknowledge in PagerDuty/monitoring system
   - Post in incident channel (Slack #incidents)
   - Assign incident commander

2. **Assess the situation**
   - Check monitoring dashboards (Grafana)
   - Review recent deployments
   - Check error tracking (Sentry)
   - Review application logs

3. **Communicate**
   - Notify stakeholders
   - Update status page if applicable
   - Set up incident bridge call if needed

4. **Investigate**
   - Gather evidence
   - Form hypothesis
   - Test hypothesis

5. **Mitigate**
   - Implement fix or workaround
   - Consider rollback if deployment-related

6. **Verify**
   - Confirm issue is resolved
   - Run smoke tests
   - Monitor metrics

7. **Document**
   - Record timeline of events
   - Document actions taken
   - Schedule post-mortem

---

## Deployment Failures

### Symptoms
- CI/CD pipeline fails
- Application won't start after deployment
- Health checks failing
- 502/503 errors

### Investigation Steps

1. **Check CI/CD logs**
   ```bash
   # View GitHub Actions logs
   gh run view <run-id> --log-failed
   
   # Or check directly in GitHub UI
   ```

2. **Check application logs**
   ```bash
   # Docker
   docker logs amani-backend --tail 100
   
   # Kubernetes
   kubectl logs -l app=amani-backend --tail=100
   
   # Fly.io
   flyctl logs
   ```

3. **Check health endpoints**
   ```bash
   curl https://api.amani.com/api/v1/health
   curl https://api.amani.com/api/v1/readiness
   ```

### Resolution Steps

#### Option 1: Fix Forward
If the issue is minor and quickly fixable:

```bash
# Make the fix
git add .
git commit -m "fix: resolve deployment issue"
git push origin main

# Monitor deployment
gh run watch
```

#### Option 2: Rollback
If the issue is complex or time-sensitive:

```bash
# Automated rollback
./scripts/rollback.sh v1.2.3 --auto-confirm

# Or manual rollback
git revert HEAD
git push origin main

# Monitor rollback
watch -n 2 'curl -s https://api.amani.com/api/v1/health | jq .status'
```

### Post-Deployment Verification

```bash
# Check version
curl https://api.amani.com/api/v1/version | jq .

# Run smoke tests
pytest tests/smoke/ -v

# Monitor for 15 minutes
# Check error rate in Grafana
# Review Sentry for new errors
```

---

## Application Crashes

### Symptoms
- Application container/pod restarting
- 502 Bad Gateway errors
- Crash loops

### Investigation Steps

1. **Check recent restarts**
   ```bash
   # Docker
   docker ps -a | grep amani-backend
   
   # Kubernetes
   kubectl get pods -l app=amani-backend
   kubectl describe pod <pod-name>
   ```

2. **Review crash logs**
   ```bash
   # Get logs from crashed container
   docker logs <container-id> --tail 200
   kubectl logs <pod-name> --previous
   ```

3. **Check resource usage**
   ```bash
   # Docker
   docker stats amani-backend
   
   # Kubernetes
   kubectl top pod -l app=amani-backend
   ```

### Resolution Steps

1. **If memory leak suspected**
   ```bash
   # Restart application
   docker restart amani-backend
   
   # Or for Kubernetes
   kubectl rollout restart deployment/amani-backend
   
   # Monitor memory usage
   # Investigate memory leak in code
   ```

2. **If configuration issue**
   ```bash
   # Check environment variables
   docker exec amani-backend env | grep -E '(DATABASE|REDIS|SECRET)'
   
   # Verify configuration
   # Update if needed
   # Restart application
   ```

3. **If code bug**
   ```bash
   # Review error in Sentry
   # Identify problematic code
   # Deploy hotfix or rollback
   ```

---

## Database Issues

### Symptoms
- Database connection errors
- Slow queries
- Connection pool exhausted
- Migration failures

### Investigation Steps

1. **Check database connectivity**
   ```bash
   # From application server
   psql $DATABASE_URL -c "SELECT 1;"
   
   # Check connection pool
   curl https://api.amani.com/api/v1/health | jq .checks.database
   ```

2. **Check database metrics**
   ```sql
   -- Active connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Long-running queries
   SELECT pid, now() - query_start as duration, query 
   FROM pg_stat_activity 
   WHERE state = 'active' AND now() - query_start > interval '1 minute';
   
   -- Database size
   SELECT pg_size_pretty(pg_database_size(current_database()));
   ```

3. **Check for locks**
   ```sql
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

### Resolution Steps

1. **Connection pool exhausted**
   ```bash
   # Increase pool size (temporary)
   # Update DATABASE_POOL_SIZE environment variable
   # Restart application
   
   # Investigate connection leaks in code
   ```

2. **Slow query**
   ```sql
   -- Kill long-running query (if safe)
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE pid = <problem_pid>;
   
   -- Analyze and optimize query
   EXPLAIN ANALYZE <slow_query>;
   ```

3. **Migration failure**
   ```bash
   # Check current migration version
   alembic current
   
   # If migration is partially applied
   # Review migration file
   # Consider manual intervention or rollback
   alembic downgrade -1
   
   # Fix issue and re-apply
   alembic upgrade head
   ```

---

## Performance Degradation

### Symptoms
- High response times
- Increased error rates
- CPU/Memory spikes
- Database query slowness

### Investigation Steps

1. **Check application metrics**
   - Open Grafana dashboard
   - Review response time percentiles (p50, p95, p99)
   - Check error rate trends
   - Review request volume

2. **Check distributed traces**
   - Open Jaeger UI
   - Identify slow traces
   - Find bottlenecks in service calls

3. **Review errors**
   - Open Sentry
   - Look for new error patterns
   - Check error frequency

### Resolution Steps

1. **High CPU/Memory**
   ```bash
   # Scale horizontally (add more instances)
   # Docker Compose
   docker-compose up -d --scale app=3
   
   # Kubernetes
   kubectl scale deployment amani-backend --replicas=5
   
   # Identify resource-intensive code paths
   # Optimize or add caching
   ```

2. **Database bottleneck**
   ```bash
   # Enable query caching
   # Add database indexes
   # Optimize slow queries
   # Consider read replicas
   ```

3. **External service timeout**
   ```bash
   # Increase timeout values
   # Add circuit breakers
   # Implement retry logic with backoff
   # Consider async processing
   ```

---

## Security Incidents

### Symptoms
- Unusual authentication patterns
- Suspicious activity in audit logs
- Security scanner alerts
- Data breach notification

### Investigation Steps

1. **Review security logs**
   ```bash
   # Check audit logs
   grep "UNAUTHORIZED_ACCESS\|SUSPICIOUS_ACTIVITY" logs/app.log
   
   # Review authentication attempts
   grep "USER_LOGIN.*success.*false" logs/app.log | tail -100
   ```

2. **Check for vulnerabilities**
   ```bash
   # Run security scan
   trivy image amani-backend:latest
   
   # Check dependencies
   safety check
   bandit -r app/
   ```

3. **Review access patterns**
   - Check rate limiting logs
   - Review API access patterns
   - Identify affected accounts

### Resolution Steps

1. **Suspected breach**
   ```bash
   # Immediately rotate all secrets
   # Force password reset for affected users
   # Block suspicious IP addresses
   # Notify security team and legal
   # Preserve evidence
   ```

2. **Vulnerability discovered**
   ```bash
   # Assess severity and exploitability
   # Apply security patch immediately
   # Deploy hotfix if critical
   # Scan for signs of exploitation
   # Notify users if data exposed
   ```

3. **DDoS attack**
   ```bash
   # Enable aggressive rate limiting
   # Block attacking IP ranges
   # Enable CDN/WAF if available
   # Contact infrastructure provider
   ```

---

## Rollback Procedures

### Automated Rollback

```bash
# List available versions
docker images amani-backend --format "{{.Tag}}"

# Rollback to specific version
./scripts/rollback.sh v1.2.3

# Rollback without confirmation (CI/CD)
./scripts/rollback.sh v1.2.3 --auto-confirm
```

### Manual Rollback

#### Docker

```bash
# Stop current container
docker stop amani-backend
docker rm amani-backend

# Pull previous version
docker pull amani-backend:v1.2.3

# Start with previous version
docker run -d \
  --name amani-backend \
  -p 8000:8000 \
  --env-file .env \
  amani-backend:v1.2.3

# Verify
curl http://localhost:8000/api/v1/health
```

#### Kubernetes

```bash
# Rollback to previous revision
kubectl rollout undo deployment/amani-backend

# Rollback to specific revision
kubectl rollout undo deployment/amani-backend --to-revision=3

# Check rollout status
kubectl rollout status deployment/amani-backend

# Verify
kubectl get pods -l app=amani-backend
curl https://api.amani.com/api/v1/health
```

#### Fly.io

```bash
# List releases
flyctl releases list

# Rollback to previous
flyctl releases rollback --yes

# Verify
curl https://api.amani.com/api/v1/health
```

### Database Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Verify
alembic current
```

### Post-Rollback Steps

1. **Verify health**
   ```bash
   curl https://api.amani.com/api/v1/health | jq .
   curl https://api.amani.com/api/v1/version | jq .
   ```

2. **Run smoke tests**
   ```bash
   pytest tests/smoke/ -v
   ```

3. **Monitor metrics**
   - Check error rate (should decrease)
   - Check response time (should improve)
   - Monitor for 15-30 minutes

4. **Communicate**
   - Update incident status
   - Notify stakeholders
   - Document reason for rollback

---

## Post-Incident Review

After resolving an incident, conduct a blameless post-mortem:

### Template

```markdown
## Incident Summary
- **Date**: YYYY-MM-DD
- **Duration**: X hours
- **Severity**: P0/P1/P2/P3
- **Impact**: What was affected

## Timeline
- HH:MM - Incident detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Incident resolved

## Root Cause
Detailed explanation of what caused the incident

## Resolution
What was done to resolve the incident

## Action Items
- [ ] Prevention: How to prevent similar incidents
- [ ] Detection: How to detect earlier
- [ ] Response: How to respond faster
- [ ] Documentation: What to update

## Lessons Learned
What did we learn from this incident?
```

---

## Emergency Contacts

| Role | Contact | When to Escalate |
|------|---------|------------------|
| On-Call Engineer | PagerDuty | P0, P1 incidents |
| Engineering Lead | Slack/Phone | P0 incidents |
| Security Team | security@amani.com | Security incidents |
| Database Admin | DBA on-call | Database issues |

---

## Additional Resources

- [Monitoring Runbook](./monitoring_runbook.md)
- [Deployment Guide](../DEPLOYMENT.md)
- [Security Documentation](../SECURITY.md)
- [CI/CD Documentation](../CI_CD.md)
