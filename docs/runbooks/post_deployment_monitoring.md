# Post-Deployment Monitoring Guide

## Overview

This guide provides procedures for monitoring the Amani Backend application after deployment to ensure it's operating correctly and catch issues early.

## Table of Contents

1. [Initial Deployment Checklist](#initial-deployment-checklist)
2. [First 15 Minutes](#first-15-minutes)
3. [First Hour](#first-hour)
4. [First 24 Hours](#first-24-hours)
5. [Ongoing Monitoring](#ongoing-monitoring)
6. [Key Metrics to Watch](#key-metrics-to-watch)
7. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Initial Deployment Checklist

Before deploying:

- [ ] **Backup Database**
  ```bash
  ./scripts/backup_database.sh
  ```

- [ ] **Review Changes**
  ```bash
  git log --oneline -10
  git diff HEAD~1
  ```

- [ ] **Test in Staging**
  - [ ] All tests pass
  - [ ] Manual smoke tests complete
  - [ ] Load tests successful (if applicable)

- [ ] **Communication**
  - [ ] Notify team of deployment
  - [ ] Create deployment channel in Slack
  - [ ] Have rollback plan ready

- [ ] **Monitoring Setup**
  - [ ] Grafana dashboard open
  - [ ] Prometheus alerts configured
  - [ ] Sentry open in browser
  - [ ] Application logs ready

---

## First 15 Minutes

### Immediate Checks (Within 1 minute)

1. **Verify Deployment Success**
   ```bash
   # Check if application started
   docker ps | grep amani-backend
   
   # Or for Kubernetes
   kubectl get pods -l app=amani-backend
   ```

2. **Health Check**
   ```bash
   curl https://api.amani.com/api/v1/health
   
   # Expected response:
   # {
   #   "status": "healthy",
   #   "app": "Amani Escrow Backend",
   #   "version": "1.0.0",
   #   "checks": {
   #     "database": {"status": "healthy"},
   #     "migrations": {"status": "healthy"}
   #   }
   # }
   ```

3. **Readiness Check**
   ```bash
   curl https://api.amani.com/api/v1/readiness
   
   # Should return: {"ready": true}
   ```

### Quick Monitoring Review (5 minutes)

4. **Check Application Logs**
   ```bash
   # Docker
   docker logs amani-backend --tail 100
   
   # Kubernetes
   kubectl logs -l app=amani-backend --tail=100
   
   # Look for:
   # - "Starting Amani Escrow Backend..."
   # - "Database initialized successfully"
   # - No ERROR or CRITICAL logs
   ```

5. **Check Error Rate in Grafana**
   - Open: http://grafana.your-domain.com/d/amani-backend
   - Panel: "Error Rate"
   - Should be: Near 0% or matching baseline

6. **Check Response Times**
   - Panel: "Response Time (95th percentile)"
   - Should be: < 500ms for most endpoints

7. **Check Sentry for New Errors**
   - Open: https://sentry.io/organizations/your-org/issues/
   - Filter: Last 15 minutes
   - Should see: No new critical errors

### Test Critical User Flows (10 minutes)

8. **Authentication Flow**
   ```bash
   # Login test
   curl -X POST https://api.amani.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   
   # Should return: 200 OK with access_token
   ```

9. **Database Operations**
   ```bash
   # Test a read operation
   curl https://api.amani.com/api/v1/projects \
     -H "Authorization: Bearer <token>"
   
   # Should return: 200 OK with project list
   ```

10. **Test Key Business Operation** (e.g., transaction)
    - Use API or web interface
    - Verify operation completes successfully
    - Check logs for any errors

---

## First Hour

### Detailed Metrics Analysis (15 minutes)

11. **Request Rate Analysis**
    - Check: Is traffic being routed correctly?
    - Compare: Current vs. pre-deployment baseline
    - Alert if: Traffic drops significantly (possible routing issue)

12. **Database Connections**
    ```bash
    # Check active connections metric
    curl http://localhost:9090/api/v1/query?query=db_connections_active
    
    # Should be: Within normal range (e.g., 5-20)
    ```

13. **Memory and CPU Usage**
    - Check: System metrics in Grafana
    - Look for: Memory leaks (steadily increasing memory)
    - Look for: CPU spikes

### Application Behavior (30 minutes)

14. **Review All Endpoints**
    ```bash
    # Get metrics by endpoint
    curl http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])
    ```
    - Check: All critical endpoints responding
    - Verify: Response times acceptable

15. **Database Query Performance**
    ```bash
    # Check slow queries
    psql $DATABASE_URL -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
    ```
    - Look for: Queries > 1 second
    - Action: Add indexes if needed

16. **Check Background Jobs** (if applicable)
    - Wallet balance sync
    - Event ingestion
    - Email sending
    - Verify: Jobs running on schedule

### User Feedback (15 minutes)

17. **Monitor Support Channels**
    - Check: Slack, email, support tickets
    - Look for: User-reported issues
    - Priority: P0/P1 issues

18. **Review User Analytics** (if available)
    - Active users count
    - User actions (registrations, transactions)
    - Error rates by user

---

## First 24 Hours

### Regular Check-ins

Perform these checks every 2-4 hours:

19. **Metrics Dashboard Review**
    - [ ] Error rate < 1%
    - [ ] Response time < 500ms (95th percentile)
    - [ ] Database connections stable
    - [ ] No memory leaks
    - [ ] No CPU anomalies

20. **Log Analysis**
    ```bash
    # Count errors in last hour
    docker logs amani-backend --since 1h | grep -i error | wc -l
    
    # Check for specific error patterns
    docker logs amani-backend --since 1h | grep -i "connection refused\|timeout\|500"
    ```

21. **Sentry Review**
    - Check: New error types
    - Review: Error frequency
    - Action: Create tickets for non-critical issues

### Performance Validation

22. **Compare to Baseline**
    - Request rate: ± 20% of normal
    - Response time: ± 30% of normal
    - Error rate: < 2x normal

23. **Database Health**
    ```bash
    # Check database size growth
    psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
    
    # Check table sizes
    psql $DATABASE_URL -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
    ```

24. **Integration Tests**
    - Payment processing (FinCra)
    - Email sending
    - External API calls
    - Verify: All integrations working

---

## Ongoing Monitoring

### Daily Tasks

25. **Morning Health Check** (5 minutes)
    - [ ] Check Grafana dashboard
    - [ ] Review overnight errors in Sentry
    - [ ] Check alert notifications
    - [ ] Review backup completion

26. **Log Review** (10 minutes)
    ```bash
    # Check for patterns in last 24 hours
    docker logs amani-backend --since 24h | grep -i error > /tmp/errors_24h.log
    
    # Analyze error patterns
    cat /tmp/errors_24h.log | cut -d: -f1-2 | sort | uniq -c | sort -rn | head -20
    ```

27. **Performance Trend Analysis**
    - Compare: Today vs. yesterday
    - Look for: Gradual degradation
    - Action: Optimize if needed

### Weekly Tasks

28. **Capacity Planning Review**
    - Database growth rate
    - Traffic trends
    - Resource utilization
    - Action: Scale up if needed

29. **Alert Tuning**
    - Review: False positive alerts
    - Adjust: Alert thresholds
    - Add: New alerts based on incidents

30. **Backup Verification**
    ```bash
    # List recent backups
    ls -lh backups/ | tail -10
    
    # Test restore (in test environment)
    ./scripts/restore_database.sh backups/latest_backup.sql.gz
    ```

---

## Key Metrics to Watch

### Critical Metrics (Monitor Continuously)

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate | > 5% | Investigate immediately |
| Response Time (p95) | > 2 seconds | Check slow queries |
| Database Connections | > 80% pool size | Investigate connection leaks |
| CPU Usage | > 80% | Scale up or optimize |
| Memory Usage | > 90% | Investigate memory leaks |
| Disk Space | < 10% free | Clean up or expand |

### Business Metrics

| Metric | Normal Range | Action |
|--------|-------------|--------|
| Registrations/hour | 10-100 | Alert if < 5 or > 500 |
| Transactions/hour | 50-500 | Alert if < 10 or > 1000 |
| KYC Submissions/day | 20-200 | Alert if < 5 |
| API Calls/minute | 100-1000 | Alert if drops > 50% |

### Performance Metrics

| Metric | Target | Action |
|--------|--------|--------|
| Response Time (p50) | < 100ms | Optimize if > 200ms |
| Response Time (p95) | < 500ms | Investigate if > 1s |
| Response Time (p99) | < 1s | Review slow queries |
| Database Query Time | < 100ms | Add indexes if > 500ms |

---

## Common Issues and Solutions

### Issue: High Error Rate

**Symptoms**: Error rate > 5%, Sentry showing many errors

**Investigation**:
1. Check Sentry for error details
2. Review application logs
3. Check database connectivity
4. Verify external service status

**Solutions**:
- Fix bugs and redeploy
- Rollback if necessary
- Scale up resources
- Restart application

### Issue: Slow Response Times

**Symptoms**: Response time > 2 seconds, user complaints

**Investigation**:
1. Check database query performance
2. Review traces in Jaeger
3. Check CPU/memory usage
4. Look for external API timeouts

**Solutions**:
- Optimize slow queries
- Add database indexes
- Implement caching
- Scale up resources

### Issue: Database Connection Pool Exhausted

**Symptoms**: Errors about "too many connections", timeouts

**Investigation**:
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check long-running queries
psql $DATABASE_URL -c "SELECT pid, now() - query_start as duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 10;"
```

**Solutions**:
- Kill long-running queries
- Increase connection pool size
- Fix connection leaks in code
- Restart application

### Issue: Memory Leak

**Symptoms**: Memory usage steadily increasing

**Investigation**:
1. Check memory metrics in Grafana
2. Review recent code changes
3. Check for unclosed resources

**Solutions**:
- Restart application (temporary)
- Profile memory usage
- Fix memory leak in code
- Scale up memory (temporary)

### Issue: Deployment Rollback Needed

**When to rollback**:
- Error rate > 10%
- Critical functionality broken
- Database corruption risk
- Security vulnerability

**Rollback procedure**:
```bash
# 1. Stop current deployment
docker-compose stop app

# 2. Checkout previous version
git checkout <previous-commit>

# 3. Rebuild and restart
docker-compose build app
docker-compose up -d app

# 4. Verify
curl http://localhost:8000/api/v1/health

# 5. If database changes, restore backup
./scripts/restore_database.sh backups/pre_deployment_backup.sql.gz
```

---

## Monitoring Checklist Template

Use this checklist for each deployment:

### Pre-Deployment
- [ ] Backup created
- [ ] Changes reviewed
- [ ] Staging tests passed
- [ ] Team notified
- [ ] Monitoring ready

### First 15 Minutes
- [ ] Deployment successful
- [ ] Health checks passing
- [ ] No errors in logs
- [ ] Metrics normal
- [ ] Critical flows tested

### First Hour
- [ ] Traffic routing correct
- [ ] All endpoints responding
- [ ] Database performing well
- [ ] No user complaints
- [ ] Integrations working

### First 24 Hours
- [ ] Error rate acceptable
- [ ] Performance stable
- [ ] No memory leaks
- [ ] Backups successful
- [ ] No critical issues

### Sign-off
- Deployment completed by: _____________
- Date/Time: _____________
- Issues encountered: _____________
- Actions taken: _____________
- Status: ✅ Success / ⚠️ Issues / ❌ Rollback

---

## Additional Resources

- [Monitoring Runbook](monitoring_runbook.md)
- [Incident Response Checklist](incident_response_checklist.md)
- [Backup and Disaster Recovery](backup_disaster_recovery.md)
- [Troubleshooting Guide](troubleshooting_guide.md)

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| On-Call Engineer | _______ | _______ |
| Tech Lead | _______ | _______ |
| DevOps Lead | _______ | _______ |

---

*Keep this guide updated based on deployment experiences and lessons learned.*
