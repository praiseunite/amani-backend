# Deployment Guide

Complete guide for deploying Amani Escrow Backend to production environments.

## Table of Contents
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Deployment Options](#deployment-options)
- [Health Checks](#health-checks)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

Before deploying to production, ensure:

### Security
- [ ] All secrets rotated and not committed to version control
- [ ] `.env` file properly configured with production values
- [ ] `FORCE_HTTPS=True` enabled
- [ ] Strong `SECRET_KEY` generated (64+ characters)
- [ ] Proper CORS origins configured (no wildcards)
- [ ] Rate limiting enabled (`RATE_LIMIT_ENABLED=True`)
- [ ] Database credentials secured
- [ ] API keys for third-party services configured

### Database
- [ ] Database migrations tested and documented
- [ ] Rollback procedures documented
- [ ] Database backups configured
- [ ] Connection pooling configured
- [ ] Database indexes optimized

### Application
- [ ] All environment variables documented
- [ ] Health and readiness endpoints tested
- [ ] Logging configured and tested
- [ ] Error tracking configured (optional: Sentry)
- [ ] API documentation accessible only to authorized users

### Testing
- [ ] All tests passing (≥85% coverage)
- [ ] Integration tests run against staging
- [ ] Load testing completed
- [ ] Security scanning completed (Snyk, Bandit)

## Environment Configuration

### Required Environment Variables

```bash
# Application
APP_NAME=Amani Escrow Backend
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Security - CRITICAL: Generate secure values!
SECRET_KEY=<generate-with-python-c-import-secrets-print-secrets-token-hex-32)>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database - Use production credentials
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/amani_prod

# Supabase (if using)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-production-anon-key
SUPABASE_SERVICE_KEY=your-production-service-key

# FinCra Payment Integration
FINCRA_API_KEY=your-production-fincra-api-key
FINCRA_API_SECRET=your-production-fincra-api-secret
FINCRA_BASE_URL=https://api.fincra.com

# CORS - Specify exact origins, no wildcards
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Email Configuration
BREVO_API_KEY=your-production-brevo-api-key
BREVO_FROM_EMAIL=noreply@yourdomain.com
BREVO_FROM_NAME=Amani Escrow
BREVO_SMTP_LOGIN=your-production-smtp-login

# Security
FORCE_HTTPS=True

# Redis (for distributed rate limiting)
REDIS_URL=redis://your-redis-host:6379/0
REDIS_ENABLED=True

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=100
```

### Generating Secure Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Database Setup

### Running Migrations

```bash
# Check current migration status
alembic current

# Run migrations to latest version
alembic upgrade head

# Check migration history
alembic history

# Rollback one migration (if needed)
alembic downgrade -1
```

### Database Connection Pooling

The application uses SQLAlchemy's async connection pooling. Recommended settings:

```python
# In production, configure these in your deployment
pool_size=10          # Number of connections to keep open
max_overflow=20       # Maximum overflow connections
pool_timeout=30       # Timeout for getting a connection
pool_recycle=3600     # Recycle connections after 1 hour
```

## Deployment Options

### Option 1: Docker Deployment

#### Build and Run with Docker

```bash
# Build image
docker build -t amani-backend:latest .

# Run container
docker run -d \
  --name amani-backend \
  -p 8000:8000 \
  --env-file .env \
  amani-backend:latest
```

#### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Fly.io Deployment

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login to Fly.io
flyctl auth login

# Deploy
flyctl deploy

# Set secrets
flyctl secrets set SECRET_KEY=your-secret-key
flyctl secrets set DATABASE_URL=your-database-url
# ... set other secrets

# Check deployment status
flyctl status

# View logs
flyctl logs
```

### Option 3: Traditional Server (Ubuntu/Debian)

#### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL client
sudo apt install -y postgresql-client
```

#### 2. Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/amani-backend
cd /opt/amani-backend

# Clone repository
git clone https://github.com/praiseunite/amani-backend.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure Systemd Service

Create `/etc/systemd/system/amani-backend.service`:

```ini
[Unit]
Description=Amani Escrow Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/amani-backend
Environment="PATH=/opt/amani-backend/venv/bin"
EnvironmentFile=/opt/amani-backend/.env
ExecStart=/opt/amani-backend/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable amani-backend
sudo systemctl start amani-backend
sudo systemctl status amani-backend
```

#### 4. Setup Nginx Reverse Proxy

Create `/etc/nginx/sites-available/amani-backend`:

```nginx
upstream amani_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy settings
    location / {
        proxy_pass http://amani_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /api/v1/health {
        proxy_pass http://amani_backend/api/v1/health;
        access_log off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/amani-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Health Checks

### Health Check Endpoint

```bash
# Check application health
curl https://api.yourdomain.com/api/v1/health
```

Response includes:
- Application status
- Database connectivity
- Migration status
- Current version

### Readiness Probe

```bash
# Check if application is ready to serve traffic
curl https://api.yourdomain.com/api/v1/readiness
```

Use for:
- Kubernetes readiness probes
- Load balancer health checks
- Deployment verification

### Liveness Probe

```bash
# Simple ping check
curl https://api.yourdomain.com/api/v1/ping
```

## Monitoring & Logging

### Application Logs

Logs are written to both console (stdout) and file (`logs/app.log`).

```bash
# View logs (systemd)
sudo journalctl -u amani-backend -f

# View log file
tail -f logs/app.log

# View logs (Docker)
docker logs -f amani-backend
```

### Log Format

Production logs use JSON format for easy parsing:

```json
{
  "timestamp": "2025-11-22 20:00:00",
  "level": "INFO",
  "message": "Request completed",
  "method": "POST",
  "url": "/api/v1/auth/login",
  "status_code": 200
}
```

### Monitoring Recommendations

1. **Uptime Monitoring**: Ping `/api/v1/ping` every 60 seconds
2. **Health Monitoring**: Check `/api/v1/health` every 5 minutes
3. **Database Monitoring**: Monitor connection pool, query performance
4. **Error Tracking**: Integrate Sentry or similar service
5. **Metrics**: Use Prometheus + Grafana for detailed metrics

### Setting Up Sentry (Optional)

```bash
# Install sentry SDK
pip install sentry-sdk[fastapi]

# Add to app/main.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn", environment="production")
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check database connectivity
psql -h your-db-host -U your-db-user -d amani_prod

# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:password@host:5432/database
```

#### Application Won't Start

```bash
# Check logs
sudo journalctl -u amani-backend -n 50

# Check environment variables
sudo systemctl show amani-backend | grep Environment

# Test application manually
cd /opt/amani-backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### High Memory Usage

```bash
# Check worker count (reduce if needed)
# Recommended: 2-4 workers for 1GB RAM

# Monitor memory
watch -n 1 'ps aux | grep uvicorn'
```

#### Rate Limiting Issues

```bash
# Check Redis connection (if using Redis)
redis-cli -h your-redis-host ping

# Verify rate limiting settings
curl -I https://api.yourdomain.com/api/v1/health
# Look for X-RateLimit-* headers
```

### Performance Tuning

1. **Database Connection Pool**: Adjust based on load
2. **Worker Count**: `workers = (2 * CPU cores) + 1`
3. **Redis for Rate Limiting**: Enable in production
4. **CDN**: Use CDN for static assets (if any)
5. **Caching**: Implement caching for frequently accessed data

### Rollback Procedures

```bash
# Rollback database migration
alembic downgrade -1

# Rollback application deployment
git checkout previous-tag
systemctl restart amani-backend

# Docker rollback
docker pull amani-backend:previous-version
docker-compose up -d
```

## Security Checklist

- [ ] HTTPS enforced (`FORCE_HTTPS=True`)
- [ ] Security headers configured (Nginx/CDN)
- [ ] Rate limiting enabled
- [ ] CORS properly configured (no wildcards)
- [ ] Secrets not in version control
- [ ] Database credentials rotated
- [ ] API documentation protected
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies up to date
- [ ] Security scanning enabled (Snyk, Dependabot)

## Support

For issues and questions:
- GitHub Issues: https://github.com/praiseunite/amani-backend/issues
- Documentation: See README.md, SECURITY_NOTICE.md
- Security: See SECURITY_NOTICE.md for reporting vulnerabilities
