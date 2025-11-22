# Monitoring and Observability Runbook

## Overview

This runbook provides operational guidance for monitoring and observability of the Amani Backend application. It covers Prometheus metrics, Grafana dashboards, Sentry error tracking, OpenTelemetry tracing, and alerting.

## Table of Contents

1. [Metrics Collection (Prometheus)](#metrics-collection-prometheus)
2. [Visualization (Grafana)](#visualization-grafana)
3. [Error Tracking (Sentry)](#error-tracking-sentry)
4. [Distributed Tracing (OpenTelemetry)](#distributed-tracing-opentelemetry)
5. [Alerting and Notifications](#alerting-and-notifications)
6. [Common Operations](#common-operations)
7. [Troubleshooting](#troubleshooting)

## Metrics Collection (Prometheus)

### Setup

The application exposes Prometheus metrics at the `/metrics` endpoint.

#### Local Development

```bash
# Start the application with monitoring
docker-compose up -d

# Access Prometheus UI
open http://localhost:9090
```

#### Configuration

Prometheus configuration is in `config/prometheus.yml`. It scrapes metrics from:
- Amani Backend application (`app:8000/metrics`)
- Prometheus itself
- Optional: Node Exporter, Redis Exporter, PostgreSQL Exporter

### Available Metrics

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests (labels: method, endpoint, status)
- `http_request_duration_seconds` - HTTP request latency histogram
- `http_requests_in_progress` - Currently processing requests

#### Database Metrics
- `db_connections_active` - Active database connections
- `db_query_duration_seconds` - Database query duration histogram

#### Business Metrics
- `escrow_transactions_total` - Total escrow transactions
- `user_registrations_total` - Total user registrations
- `kyc_submissions_total` - Total KYC submissions

#### Error Metrics
- `errors_total` - Total errors (labels: error_type, endpoint)

### Querying Metrics

#### Request Rate
```promql
rate(http_requests_total[5m])
```

#### Error Rate
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

#### 95th Percentile Response Time
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Visualization (Grafana)

### Setup

```bash
# Grafana is included in docker-compose
docker-compose up -d grafana

# Access Grafana UI
open http://localhost:3000

# Default credentials
Username: admin
Password: admin
```

### Dashboard

A pre-configured dashboard is available at `config/grafana_dashboard.json` with panels for:
- Request rate
- Response time (95th percentile)
- Error rate
- Active database connections
- Request status distribution
- Business metrics

### Importing Dashboard

1. Log in to Grafana
2. Go to Dashboards → Import
3. Upload `config/grafana_dashboard.json`
4. Select Prometheus as the data source

### Custom Queries

Add custom panels with PromQL queries:

```promql
# Average response time by endpoint
avg by (endpoint) (rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))

# Request rate by status code
sum by (status) (rate(http_requests_total[5m]))
```

## Error Tracking (Sentry)

### Setup

1. Create a Sentry account at https://sentry.io
2. Create a new project for "FastAPI"
3. Copy the DSN (Data Source Name)
4. Add to `.env`:

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of transactions
```

### Features

- **Automatic Error Capture**: All unhandled exceptions are sent to Sentry
- **Performance Monitoring**: Tracks request duration and database queries
- **Breadcrumbs**: Trail of events leading to errors
- **Release Tracking**: Errors tagged with app version
- **User Context**: Associate errors with users (when authenticated)

### Manual Error Capture

```python
from app.core.sentry import capture_exception, add_breadcrumb

# Add breadcrumb
add_breadcrumb(
    message="User attempted payment",
    category="payment",
    level="info",
    data={"amount": 100, "currency": "USD"}
)

# Capture exception with context
try:
    risky_operation()
except Exception as e:
    capture_exception(
        e,
        context={"operation": "payment_processing"},
        user_info={"id": user.id, "email": user.email}
    )
```

### Filtering Errors

Edit `app/core/sentry.py` in the `before_send_handler` function to filter specific errors.

## Distributed Tracing (OpenTelemetry)

### Setup

Enable tracing in `.env`:

```bash
TRACING_ENABLED=True
TRACING_EXPORTER=jaeger  # or otlp, console
```

#### Jaeger (Local Development)

```bash
# Start Jaeger (included in docker-compose)
docker-compose up -d jaeger

# Access Jaeger UI
open http://localhost:16686
```

#### OTLP (Cloud Providers)

For DataDog, Honeycomb, or other OTLP-compatible backends:

```bash
TRACING_ENABLED=True
TRACING_EXPORTER=otlp
OTLP_ENDPOINT=https://your-endpoint:4317
OTLP_HEADERS=api-key=your-api-key
```

### Instrumentation

The application automatically instruments:
- HTTP requests (FastAPI)
- Database queries (SQLAlchemy)
- HTTP client requests (httpx)

### Custom Spans

```python
from app.core.tracing import get_tracer, add_span_attributes

tracer = get_tracer(__name__)

with tracer.start_as_current_span("custom_operation") as span:
    add_span_attributes(
        user_id=user.id,
        operation="payment"
    )
    # Your code here
```

## Alerting and Notifications

### Alert Rules

Alert rules are defined in `config/alert_rules.yml`:
- High error rate
- High response time
- Database connection issues
- High memory/CPU usage
- Disk space low
- Application down
- Slow database queries

### Slack Integration

1. Create a Slack webhook:
   - Go to https://api.slack.com/apps
   - Create new app → Incoming Webhooks
   - Copy webhook URL

2. Add to `.env`:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

3. Send test alert:
```python
from app.core.alerts import send_slack_alert

await send_slack_alert(
    message="Test alert from Amani Backend",
    severity="info",
    context={"test": "value"}
)
```

### PagerDuty Integration

1. Create PagerDuty integration:
   - Go to Services → Add Integration
   - Choose "Events API v2"
   - Copy Integration Key

2. Add to `.env`:
```bash
PAGERDUTY_API_KEY=your-integration-key
PAGERDUTY_SERVICE_ID=your-service-id
```

3. Send test alert:
```python
from app.core.alerts import send_pagerduty_alert

await send_pagerduty_alert(
    summary="Test alert from Amani Backend",
    severity="warning"
)
```

## Common Operations

### View Current Metrics

```bash
# Get current metrics from application
curl http://localhost:8000/metrics

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=http_requests_total'
```

### Check Application Health

```bash
# Health check with database status
curl http://localhost:8000/api/v1/health

# Readiness check
curl http://localhost:8000/api/v1/readiness

# Simple ping
curl http://localhost:8000/api/v1/ping
```

### View Recent Errors in Sentry

1. Log in to Sentry
2. Navigate to Issues
3. Filter by environment, release, or time range

### View Traces in Jaeger

1. Open Jaeger UI: http://localhost:16686
2. Select "amani-backend" service
3. Click "Find Traces"
4. Click on a trace to see detailed span information

## Troubleshooting

### Prometheus Not Scraping Metrics

**Symptom**: No data in Prometheus/Grafana

**Solutions**:
1. Check application is running: `docker ps`
2. Verify metrics endpoint: `curl http://localhost:8000/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Review Prometheus logs: `docker logs amani-prometheus`

### High Memory Usage

**Symptom**: Alert "HighMemoryUsage" triggered

**Investigation**:
1. Check application metrics in Grafana
2. Review application logs: `docker logs amani-backend`
3. Check database connection pool size
4. Look for memory leaks in Sentry

**Actions**:
- Restart application: `docker-compose restart app`
- Review recent code changes
- Check for resource-intensive operations

### High Error Rate

**Symptom**: Alert "HighErrorRate" triggered

**Investigation**:
1. Check error details in Sentry
2. Review error metrics: `rate(http_requests_total{status=~"5.."}[5m])`
3. Check application logs
4. Review database connectivity

**Actions**:
- Fix identified bugs
- Scale up resources if needed
- Check external service dependencies

### Database Connection Issues

**Symptom**: Alert "DatabaseConnectionIssues" triggered

**Investigation**:
1. Check database health: `curl http://localhost:8000/api/v1/health`
2. Review database logs
3. Check connection pool metrics: `db_connections_active`

**Actions**:
- Verify database is running
- Check database credentials
- Review connection pool configuration
- Check network connectivity

### Slow Response Times

**Symptom**: Alert "HighResponseTime" triggered

**Investigation**:
1. Check response time metrics in Grafana
2. Review traces in Jaeger to identify slow operations
3. Check database query performance
4. Review slow query logs

**Actions**:
- Optimize slow queries
- Add database indexes
- Implement caching
- Scale up resources

## Best Practices

1. **Regular Monitoring**: Check dashboards daily
2. **Alert Tuning**: Adjust thresholds based on normal traffic patterns
3. **Documentation**: Keep runbooks updated with new procedures
4. **Testing**: Test alerts and recovery procedures regularly
5. **Correlation**: Use request IDs to correlate logs, traces, and metrics
6. **Retention**: Configure appropriate data retention policies
7. **Security**: Secure Grafana, Prometheus with authentication
8. **Backup**: Regularly backup Grafana dashboards and Prometheus data

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Sentry Documentation](https://docs.sentry.io/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
