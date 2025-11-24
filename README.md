# Amani Escrow Backend

[![CI Pipeline](https://github.com/praiseunite/amani-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/praiseunite/amani-backend/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/praiseunite/amani-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/praiseunite/amani-backend)

A secure, high-performance FastAPI backend for the Amani escrow platform with FinCra and Lightning Network (LNbits) payment integration.

## Features

- 🚀 **FastAPI Framework**: High-performance async API with automatic OpenAPI documentation
- 🔒 **Security First**: HTTPS enforcement, security headers, comprehensive audit trails
- 🛡️ **Rate Limiting**: Redis-based distributed rate limiting with automatic fallback
- ✅ **Input Validation**: Advanced validation with XSS, SQL injection, and path traversal protection
- 🔐 **Authentication System**: JWT tokens, password hashing, Supabase Auth integration, role-based access control
- 📊 **PostgreSQL/Supabase**: Async SQLAlchemy integration with connection pooling
- 📝 **Structured Logging**: JSON-formatted logs with request IDs for easy parsing and audit trails
- 🌐 **CORS Configured**: Cross-origin resource sharing support
- 🚨 **Error Handling**: Custom exception handlers with standardized error responses
- ⚡ **Async Support**: Built for high concurrency and scalability
- 💳 **FinCra Integration**: Traditional payment processing integration
- ⚡ **Lightning Network**: LNbits integration for Bitcoin Lightning payments
- 🤖 **Bot Features**: Magic links, faucet, internal transfers, PIN protection
- 🔄 **API Versioning**: Versioned API endpoints for backward compatibility
- 📈 **Monitoring & Observability**: Prometheus metrics, Grafana dashboards, Sentry error tracking, OpenTelemetry tracing
- 🔔 **Alerting**: Slack and PagerDuty integration for critical alerts
- 💾 **Backup & Recovery**: Automated database backup scripts and disaster recovery procedures

## Project Structure

```
amani-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── audit.py       # Audit trail system
│   │   ├── auth.py        # Authentication utilities
│   │   ├── config.py      # Environment configuration
│   │   ├── database.py    # Database connection and session management
│   │   ├── exceptions.py  # Custom exception handlers
│   │   ├── logging.py     # Structured logging setup
│   │   ├── rate_limit.py  # Rate limiting middleware
│   │   ├── security.py    # Security middleware and utilities
│   │   └── validation.py  # Input validation utilities
│   ├── models/              # SQLAlchemy models
│   │   └── __init__.py
│   ├── routes/              # API route handlers
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoints
│   └── schemas/             # Pydantic schemas
│       └── __init__.py
├── logs/                    # Application logs (auto-created)
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Example environment configuration
├── .gitignore              # Git ignore file
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database (or Supabase account)
- pip package manager

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/praiseunite/amani-backend.git
   cd amani-backend
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and update with your actual credentials
   ```

5. **Run the application**

   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or use the built-in run command:

   ```bash
   python app/main.py
   ```

6. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Hello World: http://localhost:8000/api/v1/
   - Health Check: http://localhost:8000/api/v1/health

## Environment Configuration

Copy `.env.example` to `.env` and configure the following:

### Required Variables

- `SECRET_KEY`: Secret key for JWT tokens (generate a secure random string)
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql+asyncpg://user:pass@host:port/db`)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anonymous key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key

### Optional Variables

- `FINCRA_API_KEY`: FinCra API key for payment integration
- `FINCRA_API_SECRET`: FinCra API secret
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `FORCE_HTTPS`: Enable HTTPS enforcement in production

### Rate Limiting Configuration

- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting (default: True)
- `RATE_LIMIT_PER_MINUTE`: Maximum requests per minute (default: 60)
- `RATE_LIMIT_BURST_SIZE`: Maximum burst size (default: 100)

### Redis Configuration (Optional)

- `REDIS_ENABLED`: Enable Redis for distributed rate limiting (default: False)
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)

### Monitoring and Observability

- `SENTRY_DSN`: Sentry error tracking DSN (get from https://sentry.io)
- `SENTRY_TRACES_SAMPLE_RATE`: Percentage of transactions to trace (default: 0.1)
- `TRACING_ENABLED`: Enable OpenTelemetry distributed tracing (default: False)
- `TRACING_EXPORTER`: Tracing backend (options: otlp, console)
- `SLACK_WEBHOOK_URL`: Slack webhook for alerts
- `PAGERDUTY_API_KEY`: PagerDuty integration key for critical alerts

## API Endpoints

### Health & Status

- `GET /api/v1/` - Hello World endpoint
- `GET /api/v1/health` - Comprehensive health check with database and migration status
- `GET /api/v1/readiness` - Readiness probe for deployment orchestration
- `GET /api/v1/ping` - Simple ping/pong for basic liveness checks
- `GET /metrics` - Prometheus metrics endpoint for monitoring

#### Health Endpoint Details

The `/health` endpoint provides comprehensive system status:

```bash
curl http://localhost:8000/api/v1/health
```

Response includes:
- Application status and version
- Database connectivity check
- Migration status verification
- Current migration version

#### Readiness Endpoint Details

The `/readiness` endpoint verifies the system is ready to serve traffic:

```bash
curl http://localhost:8000/api/v1/readiness
```

Checks:
- Database connection
- Required tables exist (users, wallet_registry, wallet_balance_snapshot, wallet_transaction_event)
- Post-migration state validation

Use this endpoint for:
- Kubernetes readiness probes
- Load balancer health checks
- Deployment verification

### Authentication

- `POST /api/v1/auth/signup` - Register a new user
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/magic-link` - Request magic link (passwordless auth)
- `GET /api/v1/auth/me` - Get current user info
- `PUT /api/v1/auth/me` - Update user profile
- `POST /api/v1/auth/change-password` - Change password

### Project Management

- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects` - List user's projects (paginated)
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete draft project

### Milestone Management

- `POST /api/v1/milestones` - Create a new milestone
- `GET /api/v1/milestones` - List milestones (paginated, filterable)
- `GET /api/v1/milestones/{id}` - Get milestone details
- `PUT /api/v1/milestones/{id}` - Update milestone
- `POST /api/v1/milestones/{id}/submit` - Submit milestone for approval
- `POST /api/v1/milestones/{id}/approve` - Approve or reject milestone

### Escrow & Transactions

- `POST /api/v1/escrow/hold` - Hold funds in escrow
- `POST /api/v1/escrow/release` - Release escrow funds
- `GET /api/v1/escrow/transactions` - List transactions (paginated)
- `GET /api/v1/escrow/transactions/{id}` - Get transaction details

### KYC Verification

- `POST /api/v1/kyc/submit` - Submit KYC information
- `GET /api/v1/kyc/status` - Get KYC submission status
- `POST /api/v1/kyc/resubmit/{kyc_id}` - Resubmit rejected KYC

### Lightning Network (LNbits)

- `POST /api/v1/lightning/wallet/create` - Create Lightning wallet
- `GET /api/v1/lightning/wallet/details` - Get wallet details
- `POST /api/v1/lightning/invoice/create` - Generate Lightning invoice
- `POST /api/v1/lightning/invoice/check` - Check payment status
- `POST /api/v1/lightning/invoice/decode` - Decode BOLT11 invoice
- `POST /api/v1/lightning/payment/send` - Pay Lightning invoice
- `GET /api/v1/lightning/balance` - Get wallet balance

### Bot Features

- `POST /api/v1/bot/magic-link/create` - Create claimable cheque
- `POST /api/v1/bot/magic-link/claim/{id}` - Claim magic link
- `POST /api/v1/bot/faucet/claim` - Claim from faucet
- `POST /api/v1/bot/transfer/internal` - Internal user transfer
- `POST /api/v1/bot/withdrawal/pin/set` - Set withdrawal PIN
- `POST /api/v1/bot/withdrawal/pin/verify` - Verify PIN
- `DELETE /api/v1/bot/withdrawal/pin` - Remove PIN

**See [AUTHENTICATION.md](AUTHENTICATION.md) for complete authentication documentation.**

**See [LIGHTNING_INTEGRATION.md](LIGHTNING_INTEGRATION.md) for Lightning Network integration guide.**

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With specific log level
uvicorn app.main:app --reload --log-level debug
```

### Running in Production

```bash
# Using Uvicorn with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Security Features

The application implements comprehensive security hardening:

- **HTTPS Enforcement**: Automatic redirect to HTTPS in production
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS
- **Rate Limiting**: Token bucket algorithm with Redis support for distributed limiting
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Advanced validation with XSS, SQL injection, and path traversal protection
- **Audit Trails**: Comprehensive logging of sensitive operations
- **Error Handling**: Secure error responses that don't leak sensitive information
- **Trusted Host Middleware**: Prevents host header attacks
- **Password Hashing**: bcrypt for secure password storage
- **JWT Authentication**: Secure token-based authentication with role-based access control

**See [SECURITY.md](SECURITY.md) for detailed security documentation.**

- **JWT Authentication**: Token-based authentication ready

## Database

The application uses async SQLAlchemy with PostgreSQL:

- **Connection Pooling**: Configured with pool_size=10, max_overflow=20
- **Async Sessions**: Full async/await support
- **Supabase Integration**: Ready for Supabase PostgreSQL
- **Migrations**: Alembic ready for database migrations

## Logging

Structured JSON logging for production with human-readable format for development:

- **Console Logging**: Formatted output to stdout
- **File Logging**: JSON logs stored in `logs/app.log`
- **Request Tracking**: All HTTP requests logged with metadata
- **Error Tracking**: Detailed error logging for debugging

## Database

The application uses async SQLAlchemy with PostgreSQL (Supabase):

- **4 Core Models**: User, Project, Milestone, Transaction
- **Async Support**: Full async/await with asyncpg
- **Connection Pooling**: Configured with pool_size=10, max_overflow=20
- **Row-Level Security**: Supabase RLS policies for data protection
- **Migrations**: Alembic for schema management
- **Relationships**: Fully mapped with foreign keys and cascade operations

**See [DATABASE_SETUP.md](DATABASE_SETUP.md) for complete setup guide.**

## CI/CD Pipeline

The project includes a comprehensive CI/CD pipeline with GitHub Actions:

### Pipeline Jobs

1. **Linting** - Code quality checks
   - Black code formatting (enforced)
   - Flake8 linting (enforced)
   - Build fails if checks don't pass

2. **Unit Tests** - Fast, isolated tests
   - Tests domain logic, ports, and application services
   - No external dependencies required
   - Coverage requirement: ≥85%

3. **Integration Tests** - Database-backed tests
   - PostgreSQL service provisioned automatically
   - Alembic migrations run before tests
   - Tests wallet registry, balance sync, event ingestion
   - Validates idempotency and concurrency handling
   - Tests database constraints

4. **API Tests** - API endpoint tests
   - FastAPI route testing
   - Request/response validation

5. **Migration Tests** - Database migration validation
   - Tests migration upgrade to head
   - Tests rollback (downgrade -1)
   - Verifies re-application works
   - Validates migration history

6. **Docker Build** - Container image building
   - Runs only if all tests pass
   - Uses build cache for efficiency

### Coverage Reporting

- Codecov integration for coverage tracking
- Separate coverage reports for unit, integration, and API tests
- Minimum 85% coverage required for unit tests
- CI badge shows current build status

### Running CI Locally

Simulate CI environment locally:

```bash
# Run linting
black --check app/ tests/
flake8 app/ tests/

# Run unit tests
pytest tests/unit/ -v --cov=app --cov-fail-under=85

# Run integration tests (requires database)
export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
alembic upgrade head
pytest tests/integration/ -v -m integration
```

**See [CI_CD.md](CI_CD.md) for complete CI/CD documentation.**

## Testing

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all unit tests (fast, no database required)
pytest tests/unit/ -v -m "unit"

# Run API tests
pytest tests/api/ -v

# Run integration tests (requires database)
export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
pytest tests/integration/ -v -m "integration"

# Run all tests with coverage
pytest tests/ --cov=app --cov-report=html
```

### Database Testing Setup

#### Local Database Setup

1. **Start PostgreSQL with Docker**:
   ```bash
   docker run --name test-postgres \
     -e POSTGRES_USER=test_user \
     -e POSTGRES_PASSWORD=test_pass \
     -e POSTGRES_DB=test_db \
     -p 5432:5432 \
     -d postgres:15
   ```

2. **Set environment variable**:
   ```bash
   export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
   ```

3. **Run migrations**:
   ```bash
   DATABASE_URL=$TEST_DATABASE_URL alembic upgrade head
   ```

4. **Run integration tests**:
   ```bash
   pytest tests/integration/ -v -m "integration"
   ```

#### CI Database Setup

The CI pipeline automatically:
- Provisions PostgreSQL service container
- Runs migrations before tests
- Executes integration tests with real database
- Tests migration rollback scenarios

See `.github/workflows/ci.yml` for configuration.

#### Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests (in-memory, no database)
- `@pytest.mark.integration` - Integration tests (require database)

#### Testing Migrations

Use the automated migration testing script:

```bash
# Set test database URL
export DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

# Run migration tests
./scripts/test_migrations.sh
```

This script tests:
- Migration upgrade to head
- Migration rollback
- Re-application of migrations
- Migration history verification

### Coverage Requirements

- Minimum coverage: **85%**
- CI enforces coverage requirements
- View detailed coverage: `htmlcov/index.html`

## Next Steps

1. ✅ ~~Define database models in `app/models/`~~
2. ✅ ~~Set up database migrations with Alembic~~
3. ✅ ~~Implement authentication and authorization~~
4. ✅ ~~Create Pydantic schemas in `app/schemas/`~~
5. ✅ ~~Implement CRUD operations in `app/crud/`~~
6. ✅ ~~Implement business logic routes in `app/routes/`~~
7. ✅ ~~Configure CI/CD pipeline~~
8. ✅ ~~Add comprehensive integration tests~~
9. ✅ ~~Implement health and readiness probes~~
10. ✅ ~~Add monitoring and observability (Prometheus, Sentry, OpenTelemetry)~~
11. Integrate FinCra payment APIs
12. Add comprehensive end-to-end tests

## Monitoring and Observability

The application includes comprehensive monitoring and observability features:

### Prometheus Metrics

- **Metrics Endpoint**: `GET /metrics`
- **Available Metrics**:
  - HTTP request count, duration, and errors
  - Database connection pool status
  - Business metrics (transactions, registrations, KYC)
  - Error tracking by type and endpoint

### Grafana Dashboards

Pre-configured dashboards available in `config/grafana_dashboard.json`:
- Request rate and response times
- Error rates and types
- Database performance
- Business metrics visualization

```bash
# Start monitoring stack
docker-compose up -d prometheus grafana

# Access Grafana
open http://localhost:3000  # admin/admin
```

### Sentry Error Tracking

Automatic error capture and performance monitoring:
- Unhandled exceptions
- Performance traces
- User context
- Release tracking

Configure in `.env`:
```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
```

### OpenTelemetry Tracing

Distributed tracing with OTLP exporter:
- Automatic instrumentation of FastAPI, SQLAlchemy, and httpx
- Trace context propagation
- Custom span creation

### Alerting

Configured alerts for:
- High error rates
- Slow response times
- Database issues
- Resource exhaustion

Notifications via:
- Slack webhooks
- PagerDuty

### Backup and Recovery

Automated database backup scripts:

```bash
# Create backup
./scripts/backup_database.sh

# Restore from backup
./scripts/restore_database.sh backups/amani_backup_YYYYMMDD_HHMMSS.sql.gz
```

## Operational Runbooks

Detailed operational guides are available in `docs/runbooks/`:

- **[Migration Runbook](docs/runbooks/migration_runbook.md)** - Database migration procedures, verification, and rollback
- **[Troubleshooting Guide](docs/runbooks/troubleshooting_guide.md)** - Solutions to common issues and problems
- **[Monitoring Runbook](docs/runbooks/monitoring_runbook.md)** - Monitoring setup and operations
- **[Incident Response Checklist](docs/runbooks/incident_response_checklist.md)** - Structured incident response procedures
- **[Backup and Disaster Recovery](docs/runbooks/backup_disaster_recovery.md)** - Backup procedures and disaster recovery
- **[Post-Deployment Monitoring](docs/runbooks/post_deployment_monitoring.md)** - Post-deployment monitoring guide
- **[Wallet Registry Runbook](docs/runbooks/wallet_registry_runbook.md)** - Wallet registry operations and maintenance
- **[Wallet Event Ingestion Runbook](docs/runbooks/wallet_event_ingestion_runbook.md)** - Event ingestion procedures

### Quick References

**Run Migrations**:
```bash
alembic upgrade head
```

**Test Migrations**:
```bash
./scripts/test_migrations.sh
```

**Check Health**:
```bash
curl http://localhost:8000/api/v1/health
```

**Get Metrics**:
```bash
curl http://localhost:8000/metrics
```

**Run Tests**:
```bash
pytest tests/ --cov=app
```

**Create Backup**:
```bash
./scripts/backup_database.sh
```

## Additional Documentation

- [API Implementation Guide](API_IMPLEMENTATION.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Authentication Guide](AUTHENTICATION.md)
- [Security Documentation](SECURITY.md)
- [Database Setup Guide](DATABASE_SETUP.md)
- [CI/CD Documentation](CI_CD.md)

## License

Copyright © 2024 Amani Platform. All rights reserved.
