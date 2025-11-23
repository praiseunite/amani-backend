# Incident Response Checklist

## Overview

This checklist provides a structured approach to handling incidents in the Amani Backend application. Follow these steps to quickly identify, resolve, and learn from incidents.

## Incident Severity Levels

### P0 - Critical
- Complete service outage
- Data loss or corruption
- Security breach
- Financial transaction failures

**Response Time**: Immediate (within 15 minutes)

### P1 - High
- Major feature unavailable
- Significant performance degradation
- Affecting multiple users
- Payment processing delays

**Response Time**: Within 1 hour

### P2 - Medium
- Minor feature unavailable
- Intermittent errors
- Affecting small user subset
- Non-critical performance issues

**Response Time**: Within 4 hours

### P3 - Low
- Cosmetic issues
- Non-urgent bugs
- Feature requests
- Documentation updates

**Response Time**: Within 1 business day

---

## Incident Response Process

### Phase 1: Detection and Triage (5-10 minutes)

- [ ] **Incident Detected**
  - Source: Alert, monitoring, user report, team member
  - Time detected: ___________
  - Detected by: ___________

- [ ] **Create Incident Channel**
  - Create dedicated Slack channel: `#incident-YYYY-MM-DD-description`
  - Invite relevant team members
  - Pin important information

- [ ] **Initial Assessment**
  - [ ] What is broken?
  - [ ] What is the user impact?
  - [ ] How many users affected?
  - [ ] Is data at risk?
  - [ ] Is this a security issue?

- [ ] **Assign Severity Level**
  - Severity: P0 / P1 / P2 / P3
  - Reasoning: ___________

- [ ] **Designate Incident Commander**
  - Who: ___________
  - Responsibilities: Coordinate response, make decisions, communicate

- [ ] **Initial Communication**
  - [ ] Notify team in incident channel
  - [ ] Update status page (if applicable)
  - [ ] Notify stakeholders (for P0/P1)

---

### Phase 2: Investigation (15-30 minutes)

- [ ] **Gather Context**
  - [ ] Check recent deployments: `git log --oneline -10`
  - [ ] Review recent code changes affecting area
  - [ ] Check if related to infrastructure changes
  - [ ] Review similar past incidents

- [ ] **Check Monitoring Systems**
  - [ ] Grafana dashboards: http://localhost:3000
    - Request rate anomalies?
    - Error rate spikes?
    - Response time increases?
    - Database connection issues?
  
  - [ ] Prometheus alerts: http://localhost:9090
    - Which alerts fired?
    - When did they start?
  
  - [ ] Sentry errors: https://sentry.io
    - New error types?
    - Error frequency?
    - Stack traces?
  
  - [ ] Jaeger traces: http://localhost:16686
    - Slow operations?
    - Failed service calls?

- [ ] **Check Application Health**
  ```bash
  # Health check
  curl http://localhost:8000/api/v1/health
  
  # Readiness check
  curl http://localhost:8000/api/v1/readiness
  ```

- [ ] **Review Application Logs**
  ```bash
  # Docker logs
  docker logs amani-backend --tail 100 --follow
  
  # Check for errors
  docker logs amani-backend | grep -i error | tail -20
  
  # Filter by request ID
  docker logs amani-backend | grep "request_id: <ID>"
  ```

- [ ] **Check Database**
  ```bash
  # Connection test
  psql $DATABASE_URL -c "SELECT 1;"
  
  # Check active connections
  psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
  
  # Check long-running queries
  psql $DATABASE_URL -c "SELECT pid, now() - query_start as duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 10;"
  ```

- [ ] **Check Dependencies**
  - [ ] Redis: `redis-cli ping`
  - [ ] Database: Connection pool status
  - [ ] External APIs: FinCra status
  - [ ] Supabase: Service status

- [ ] **Document Findings**
  - Root cause hypothesis: ___________
  - Supporting evidence: ___________
  - Related systems: ___________

---

### Phase 3: Mitigation (Variable)

- [ ] **Immediate Actions**
  
  Choose appropriate action(s):
  
  - [ ] **Rollback Deployment**
    ```bash
    # Rollback to previous version
    git checkout <previous-commit>
    docker-compose build app
    docker-compose up -d app
    ```
  
  - [ ] **Restart Services**
    ```bash
    # Restart application
    docker-compose restart app
    
    # Restart all services
    docker-compose restart
    ```
  
  - [ ] **Scale Resources**
    ```bash
    # Increase container resources
    docker-compose up -d --scale app=3
    ```
  
  - [ ] **Kill Long-Running Queries**
    ```sql
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
    WHERE pid = <process_id>;
    ```
  
  - [ ] **Clear Redis Cache**
    ```bash
    redis-cli FLUSHALL
    ```
  
  - [ ] **Enable Maintenance Mode**
    - Update load balancer to show maintenance page
    - Or: Add maintenance mode in application
  
  - [ ] **Database Restore** (if data corruption)
    ```bash
    ./scripts/restore_database.sh backups/latest_backup.sql.gz
    ```

- [ ] **Verify Mitigation**
  - [ ] Check metrics returned to normal
  - [ ] Test affected functionality
  - [ ] Confirm with monitoring tools
  - [ ] Get user confirmation (if applicable)

---

### Phase 4: Communication

- [ ] **Internal Updates**
  - [ ] Update incident channel every 15-30 minutes
  - [ ] Include: Status, actions taken, next steps
  - [ ] Tag relevant team members

- [ ] **External Communication** (For P0/P1)
  - [ ] Update status page
  - [ ] Send email to affected users
  - [ ] Post on social media (if appropriate)
  - [ ] Update support ticket system

- [ ] **Stakeholder Updates**
  - [ ] Notify management
  - [ ] Update SLA tracking
  - [ ] Document business impact

---

### Phase 5: Resolution and Recovery

- [ ] **Implement Permanent Fix**
  - [ ] Create feature branch
  - [ ] Write tests reproducing issue
  - [ ] Implement fix
  - [ ] Run tests: `pytest tests/`
  - [ ] Code review
  - [ ] Deploy to staging
  - [ ] Verify fix in staging
  - [ ] Deploy to production

- [ ] **Monitoring**
  - [ ] Watch metrics for 1-2 hours after fix
  - [ ] Set up specific alerts for this issue
  - [ ] Confirm no recurrence

- [ ] **Declare Resolution**
  - Time resolved: ___________
  - Duration: ___________
  - Resolution: ___________

---

### Phase 6: Post-Incident Review (Within 48 hours)

- [ ] **Schedule Post-Mortem Meeting**
  - Date/Time: ___________
  - Attendees: ___________
  - Duration: 60 minutes

- [ ] **Prepare Post-Mortem Document**
  
  Include:
  - [ ] Incident timeline
  - [ ] Root cause analysis
  - [ ] Impact assessment (users, revenue, data)
  - [ ] What went well
  - [ ] What went wrong
  - [ ] Action items with owners

- [ ] **Create Action Items**
  - [ ] Short-term fixes (completed)
  - [ ] Long-term improvements
  - [ ] Process improvements
  - [ ] Documentation updates
  - [ ] Monitoring improvements

- [ ] **Update Documentation**
  - [ ] Update runbooks
  - [ ] Add to troubleshooting guide
  - [ ] Update alert thresholds
  - [ ] Update recovery procedures

- [ ] **Share Learnings**
  - [ ] Send post-mortem to team
  - [ ] Present in team meeting
  - [ ] Update incident response process if needed

---

## Quick Reference Commands

### Application Status
```bash
# Check if running
docker ps | grep amani-backend

# View logs
docker logs amani-backend -f

# Health check
curl http://localhost:8000/api/v1/health
```

### Database Operations
```bash
# Quick connection test
psql $DATABASE_URL -c "SELECT 1;"

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Kill all connections
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"
```

### Backup and Restore
```bash
# Create backup
./scripts/backup_database.sh

# Restore from backup
./scripts/restore_database.sh backups/amani_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Monitoring
```bash
# View Prometheus metrics
curl http://localhost:8000/metrics

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=http_requests_total'

# Check alert status
curl http://localhost:9090/api/v1/alerts
```

---

## Emergency Contacts

| Role | Name | Contact | Backup |
|------|------|---------|--------|
| On-Call Engineer | _______ | _______ | _______ |
| Tech Lead | _______ | _______ | _______ |
| DevOps Lead | _______ | _______ | _______ |
| Product Manager | _______ | _______ | _______ |
| CTO | _______ | _______ | _______ |

---

## Service Dependencies

| Service | Status Page | Documentation | Contact |
|---------|------------|---------------|---------|
| Database (Supabase) | https://status.supabase.com | [DB Setup](../DATABASE_SETUP.md) | support@supabase.com |
| Payment (FinCra) | Contact FinCra | Internal docs | support@fincra.com |
| Monitoring (Sentry) | https://status.sentry.io | [Monitoring](monitoring_runbook.md) | - |

---

## Post-Incident Metrics

Track these metrics for each incident:
- Time to detect (alert to acknowledgment)
- Time to mitigate (acknowledgment to workaround)
- Time to resolve (acknowledgment to permanent fix)
- Mean Time To Recovery (MTTR)
- User impact (number of affected users)
- Revenue impact
- False alarm rate

---

## Notes

- Keep this checklist updated based on lessons learned
- Customize severity levels based on your SLAs
- Add automation for common recovery actions
- Practice incident response regularly (game days)
- Keep emergency contact information current
