# Monitoring and Observability Guide

## Overview

This guide provides a comprehensive overview of the monitoring and observability features implemented in the Amani Backend application. It covers metrics collection, visualization, error tracking, distributed tracing, alerting, and operational procedures.

## Table of Contents

1. [Architecture](#architecture)
2. [Quick Start](#quick-start)
3. [Prometheus Metrics](#prometheus-metrics)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Sentry Error Tracking](#sentry-error-tracking)
6. [OpenTelemetry Tracing](#opentelemetry-tracing)
7. [Alerting and Notifications](#alerting-and-notifications)
8. [Request Tracing](#request-tracing)
9. [Backup and Recovery](#backup-and-recovery)
10. [Best Practices](#best-practices)

---

## Architecture

The monitoring stack consists of:

```
┌─────────────────┐
│  FastAPI App    │
│  ┌───────────┐  │
│  │ Metrics   │──┼──► Prometheus ──► Grafana
│  │ Middleware│  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Request   │──┼──► Logs (JSON)
│  │ ID        │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Sentry    │──┼──► Sentry.io
│  │ SDK       │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │ OpenTel   │──┼──► Jaeger/DataDog
│  │ Tracing   │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Alerts    │──┼──► Slack/PagerDuty
│  └───────────┘  │
└─────────────────┘
```

---

## Quick Start

### Local Development with Docker Compose

```bash
# Start the full monitoring stack
docker-compose up -d

# Services will be available at:
# - Application: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - Jaeger: http://localhost:16686
```

### Environment Configuration

Add to your `.env` file:

```bash
# Sentry Error Tracking
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/789012
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

# OpenTelemetry Tracing
TRACING_ENABLED=True
TRACING_EXPORTER=otlp
OTLP_ENDPOINT=http://localhost:4317

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PAGERDUTY_API_KEY=your-integration-key
```

---

## Prometheus Metrics

### Metrics Endpoint

All metrics are exposed at:
```
GET /metrics
```

### Available Metrics

#### HTTP Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `http_requests_total` | Counter | Total HTTP requests | method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency | method, endpoint |
| `http_requests_in_progress` | Gauge | Requests being processed | method, endpoint |

#### Database Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `db_connections_active` | Gauge | Active DB connections | - |
| `db_query_duration_seconds` | Histogram | Query duration | operation |

#### Business Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `escrow_transactions_total` | Counter | Escrow transactions | type, status |
| `user_registrations_total` | Counter | User registrations | - |
| `kyc_submissions_total` | Counter | KYC submissions | status |

#### Error Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `errors_total` | Counter | Application errors | error_type, endpoint |

### Custom Metrics

To add custom metrics to your code:

```python
from app.core.metrics import (
    escrow_transactions_total,
    kyc_submissions_total,
    user_registrations_total,
)

# Increment counters
user_registrations_total.inc()
escrow_transactions_total.labels(type="hold", status="success").inc()
kyc_submissions_total.labels(status="pending").inc()
```

### PromQL Queries

#### Request Rate
```promql
rate(http_requests_total[5m])
```

#### Error Rate
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

#### 95th Percentile Response Time
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Average Response Time by Endpoint
```promql
avg by (endpoint) (rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))
```

---

## Grafana Dashboards

### Setup

1. Access Grafana at http://localhost:3000
2. Login with `admin`/`admin`
3. Add Prometheus as data source:
   - URL: http://prometheus:9090
4. Import dashboard from `config/grafana_dashboard.json`

### Dashboard Panels

The pre-configured dashboard includes:

1. **Request Rate**: Real-time request volume by endpoint
2. **Response Time (95th percentile)**: Latency tracking
3. **Error Rate**: HTTP 5xx errors by endpoint
4. **Active Database Connections**: Connection pool status
5. **Request Status Distribution**: Pie chart of status codes
6. **Requests In Progress**: Current load
7. **Database Query Duration**: Query performance
8. **Business Metrics**: Transactions, registrations, KYC submissions
9. **Error Types**: Categorized error tracking

### Creating Custom Dashboards

1. Click "+" → "Dashboard"
2. Add panel with PromQL query
3. Configure visualization
4. Save dashboard

Example panel configuration:
```json
{
  "targets": [
    {
      "expr": "rate(http_requests_total[5m])",
      "legendFormat": "{{method}} {{endpoint}}"
    }
  ]
}
```

---

## Sentry Error Tracking

### Features

- **Automatic Error Capture**: All unhandled exceptions
- **Performance Monitoring**: Transaction traces
- **Breadcrumbs**: Trail of events before errors
- **Release Tracking**: Errors tagged with version
- **User Context**: Associate errors with users

### Integration

Sentry is automatically initialized in `app/main.py`:

```python
from app.core.sentry import init_sentry

init_sentry()  # Called on startup
```

### Manual Error Capture

```python
from app.core.sentry import capture_exception, add_breadcrumb

# Add breadcrumb
add_breadcrumb(
    message="Processing payment",
    category="payment",
    level="info",
    data={"amount": 100, "currency": "USD"}
)

# Capture exception with context
try:
    process_payment()
except PaymentError as e:
    capture_exception(
        e,
        context={"payment_id": payment_id},
        user_info={"id": user.id, "email": user.email}
    )
```

### Configuration

Set in `.env`:
```bash
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/789012
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of transactions
```

### Filtering Errors

Edit `app/core/sentry.py` → `before_send_handler()`:

```python
def before_send_handler(event, hint):
    # Filter out health check errors
    if "request" in event and event["request"].get("url", "").endswith("/health"):
        return None
    
    # Don't send 404 errors
    if event.get("exception", {}).get("values", [{}])[0].get("type") == "NotFound":
        return None
    
    return event
```

---

## OpenTelemetry Tracing

### Features

- **Automatic Instrumentation**: FastAPI, SQLAlchemy, httpx
- **Distributed Tracing**: Track requests across services
- **Custom Spans**: Add application-specific traces
- **Multiple Exporters**: OTLP, Console

### Configuration

Enable in `.env`:
```bash
TRACING_ENABLED=True
TRACING_EXPORTER=otlp
OTLP_ENDPOINT=http://localhost:4317
```

For cloud providers (DataDog, Honeycomb):
```bash
OTLP_ENDPOINT=https://api.datadoghq.com:4317
OTLP_HEADERS=dd-api-key=your-api-key
```

### Custom Spans

```python
from app.core.tracing import get_tracer, add_span_attributes

tracer = get_tracer(__name__)

with tracer.start_as_current_span("process_transaction") as span:
    add_span_attributes(
        transaction_id=tx_id,
        user_id=user_id,
        amount=amount
    )
    
    # Your code here
    result = process_transaction(tx_id)
    
    add_span_attributes(result_status=result.status)
```

### Viewing Traces

#### Jaeger (Local)
```bash
# Jaeger is included in docker-compose
open http://localhost:16686

# Select "amani-backend" service
# Click "Find Traces"
```

#### DataDog (Cloud)
1. Go to APM → Traces
2. Filter by service: `amani-backend`
3. Click on a trace to view details

---

## Alerting and Notifications

### Alert Rules

Configured in `config/alert_rules.yml`:

- **HighErrorRate**: Error rate > 5% for 5 minutes
- **HighResponseTime**: p95 response time > 2 seconds
- **DatabaseConnectionIssues**: No active DB connections
- **HighMemoryUsage**: Memory usage > 90%
- **HighCPUUsage**: CPU usage > 80%
- **DiskSpaceLow**: Disk space < 10%
- **ApplicationDown**: Application not responding
- **SlowDatabaseQueries**: Query time > 1 second

### Slack Notifications

```python
from app.core.alerts import send_slack_alert

await send_slack_alert(
    message="High error rate detected",
    severity="critical",
    context={
        "error_rate": "12%",
        "endpoint": "/api/v1/transactions"
    }
)
```

### PagerDuty Notifications

```python
from app.core.alerts import send_pagerduty_alert

await send_pagerduty_alert(
    summary="Database connection failed",
    severity="critical",
    context={
        "database": "production",
        "error": str(error)
    }
)
```

### Multi-Channel Alerts

```python
from app.core.alerts import send_alert

results = await send_alert(
    message="Critical system error",
    severity="critical",
    context={"component": "payment_processor"},
    channels=["slack", "pagerduty"]
)
```

---

## Request Tracing

### Request ID Middleware

Every request gets a unique ID for correlation:

```python
# Automatically added to all requests
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000

# In logs
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "url": "/api/v1/transactions",
  "status_code": 200
}
```

### Using Request IDs

```python
from app.core.request_id import get_request_id

@router.post("/transactions")
async def create_transaction(request: Request):
    request_id = get_request_id(request)
    logger.info(f"Processing transaction", extra={"request_id": request_id})
```

### Tracing a Request

Find all logs for a request:
```bash
docker logs amani-backend | grep "550e8400-e29b-41d4-a716-446655440000"
```

---

## Backup and Recovery

### Automated Backups

```bash
# Manual backup
./scripts/backup_database.sh

# Output: backups/amani_backup_20250122_143000.sql.gz
```

### Automated Daily Backups

Add to crontab:
```bash
0 2 * * * cd /path/to/amani-backend && ./scripts/backup_database.sh
```

### Restore from Backup

```bash
./scripts/restore_database.sh backups/amani_backup_20250122_143000.sql.gz
```

### Backup to Cloud

```bash
# AWS S3
aws s3 sync backups/ s3://your-bucket/amani-backups/

# Google Cloud Storage
gsutil -m rsync -r backups/ gs://your-bucket/amani-backups/
```

See [Backup and Disaster Recovery Guide](docs/runbooks/backup_disaster_recovery.md) for details.

---

## Best Practices

### 1. Monitor Continuously

- Check Grafana dashboard daily
- Review Sentry errors weekly
- Tune alert thresholds monthly

### 2. Use Request IDs

Always include request IDs in logs:
```python
logger.info("Operation completed", extra={"request_id": request_id})
```

### 3. Add Custom Metrics

Track business-specific metrics:
```python
from prometheus_client import Counter

payment_failures = Counter(
    "payment_failures_total",
    "Payment processing failures",
    ["payment_provider", "error_type"]
)

payment_failures.labels(provider="fincra", error_type="timeout").inc()
```

### 4. Set Appropriate Alert Thresholds

- Start conservative (reduce false positives)
- Adjust based on normal traffic patterns
- Review and tune regularly

### 5. Document Incidents

- Use incident response checklist
- Write post-mortems
- Update runbooks

### 6. Test Recovery Procedures

- Test backups monthly
- Practice rollback procedures
- Run disaster recovery drills

### 7. Correlate Data

Use request IDs to correlate:
- Application logs
- Sentry errors
- Distributed traces
- Prometheus metrics

### 8. Monitor External Dependencies

- FinCra API status
- Supabase/Database
- Redis
- Email service

### 9. Secure Monitoring Endpoints

```python
# Add authentication to /metrics if exposed publicly
@router.get("/metrics")
async def metrics(credentials: HTTPBasicCredentials = Depends(security)):
    # Verify credentials
    return Response(content=get_metrics(), media_type="text/plain")
```

### 10. Keep Documentation Updated

- Update runbooks after incidents
- Document new metrics
- Update alert descriptions

---

## Troubleshooting

### Metrics Not Appearing

1. Check `/metrics` endpoint is accessible
2. Verify Prometheus can scrape the endpoint
3. Check Prometheus targets: http://localhost:9090/targets
4. Review Prometheus logs: `docker logs amani-prometheus`

### Sentry Not Receiving Errors

1. Verify `SENTRY_DSN` is set correctly
2. Test with manual error: `capture_exception(Exception("test"))`
3. Check Sentry project DSN matches
4. Review Sentry quota limits

### Traces Not Showing in Jaeger

1. Verify `TRACING_ENABLED=True`
2. Check Jaeger is running: `docker ps | grep jaeger`
3. Test with simple trace
4. Review OpenTelemetry logs

### Alerts Not Firing

1. Check alert rules are loaded in Prometheus
2. Verify alertmanager is running
3. Test with manual alert
4. Check notification channel configuration

---

## Additional Resources

- [Monitoring Runbook](docs/runbooks/monitoring_runbook.md) - Detailed operational procedures
- [Incident Response Checklist](docs/runbooks/incident_response_checklist.md) - Incident handling
- [Post-Deployment Monitoring](docs/runbooks/post_deployment_monitoring.md) - After deployment checks
- [Backup and Disaster Recovery](docs/runbooks/backup_disaster_recovery.md) - Backup procedures

---

## Support

For monitoring issues:
1. Check runbooks in `docs/runbooks/`
2. Review application logs
3. Check monitoring system status pages:
   - Sentry: https://status.sentry.io
   - DataDog: https://status.datadoghq.com

---

*This guide is maintained by the DevOps team. Last updated: January 2025*
