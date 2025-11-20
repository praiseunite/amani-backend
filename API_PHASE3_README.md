# Phase 3: API Endpoints Documentation

## Overview

This phase implements REST API endpoints for the Amani backend using FastAPI with hexagonal architecture. All business logic remains in the application/domain layers, with controllers acting as lightweight adapters.

## New Endpoints

### 1. Create Link Token
**POST** `/api/v1/link_tokens/create`

Creates a temporary link token for connecting external wallets.

**Request:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider": "fincra"
}
```

**Response (201 Created):**
```json
{
  "token": "abc123...",
  "expires_at": "2025-11-20T14:00:00",
  "provider": "fincra"
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/v1/link_tokens/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "provider": "fincra"
  }'
```

---

### 2. Link Bot/Provider
**POST** `/api/v1/bot/link`

Links a provider account using a link token. **Requires HMAC authentication.**

**Request:**
```json
{
  "token": "abc123...",
  "provider_account_id": "acc_xyz789",
  "provider_customer_id": "cust_456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "wallet_id": "987e6543-e21b-43d2-b654-123456789012",
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**curl Example (with HMAC):**
```bash
#!/bin/bash

# Configuration
API_KEY_ID="your-api-key-id"
API_SECRET="your-api-secret"
TIMESTAMP=$(date +%s)
METHOD="POST"
PATH="/api/v1/bot/link"
BODY='{"token":"abc123...","provider_account_id":"acc_xyz789","provider_customer_id":"cust_456"}'

# Generate HMAC signature
MESSAGE="${METHOD}${PATH}${TIMESTAMP}${BODY}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_SECRET" | cut -d' ' -f2)

# Make request
curl -X POST http://localhost:8000/api/v1/bot/link \
  -H "Content-Type: application/json" \
  -H "X-API-KEY-ID: $API_KEY_ID" \
  -H "X-API-TIMESTAMP: $TIMESTAMP" \
  -H "X-API-SIGNATURE: $SIGNATURE" \
  -d "$BODY"
```

---

### 3. Register Wallet
**POST** `/api/v1/wallets/register`

Registers a wallet (idempotent operation). **Requires HMAC authentication.**

**Request:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider": "fincra",
  "provider_account_id": "acc_xyz789",
  "provider_customer_id": "cust_456"
}
```

**Response (200 OK):**
```json
{
  "wallet_id": "987e6543-e21b-43d2-b654-123456789012",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider": "fincra",
  "is_active": true
}
```

**curl Example (with HMAC):**
```bash
#!/bin/bash

API_KEY_ID="your-api-key-id"
API_SECRET="your-api-secret"
TIMESTAMP=$(date +%s)
METHOD="POST"
PATH="/api/v1/wallets/register"
BODY='{"user_id":"123e4567-e89b-12d3-a456-426614174000","provider":"fincra","provider_account_id":"acc_xyz789"}'

MESSAGE="${METHOD}${PATH}${TIMESTAMP}${BODY}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_SECRET" | cut -d' ' -f2)

curl -X POST http://localhost:8000/api/v1/wallets/register \
  -H "Content-Type: application/json" \
  -H "X-API-KEY-ID: $API_KEY_ID" \
  -H "X-API-TIMESTAMP: $TIMESTAMP" \
  -H "X-API-SIGNATURE: $SIGNATURE" \
  -d "$BODY"
```

---

### 4. Get User Status
**GET** `/api/v1/users/{user_id}/status`

Retrieves user status information.

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "role": "client",
  "is_active": true,
  "is_verified": true
}
```

**curl Example:**
```bash
curl http://localhost:8000/api/v1/users/123e4567-e89b-12d3-a456-426614174000/status
```

---

## HMAC Authentication

Endpoints marked with "Requires HMAC authentication" need the following headers:

- **X-API-KEY-ID**: Your API key identifier
- **X-API-TIMESTAMP**: Unix timestamp (must be within 5 minutes of server time)
- **X-API-SIGNATURE**: HMAC-SHA256 signature

### Signature Generation

The signature is computed as:
```
HMAC-SHA256(secret, METHOD + PATH + TIMESTAMP + BODY)
```

Example in Python:
```python
import hmac
import hashlib
import time

method = "POST"
path = "/api/v1/bot/link"
timestamp = str(int(time.time()))
body = '{"token":"abc123...","provider_account_id":"acc_xyz"}'

message = f"{method}{path}{timestamp}{body}"
signature = hmac.new(
    secret.encode('utf-8'),
    message.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

---

## Running Tests Locally

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run All Tests
```bash
# Run all tests with coverage
pytest

# Run only unit tests
pytest tests/unit/ -v

# Run only API tests
pytest tests/api/ -v

# Run with coverage report
pytest tests/api/ -v --cov=app.api --cov-report=term
```

### Run Specific Test Files
```bash
# Test link token creation
pytest tests/api/test_link_tokens.py -v

# Test bot linking
pytest tests/api/test_bot_link.py -v

# Test wallet registration
pytest tests/api/test_wallets_register.py -v

# Test user status
pytest tests/api/test_users_status.py -v
```

### Run Specific Test Cases
```bash
# Run a specific test
pytest tests/api/test_bot_link.py::TestBotLinkAPI::test_bot_link_success -v

# Run tests matching a pattern
pytest tests/api/ -k "hmac" -v
```

---

## Running the API Server Locally

### Development Mode
```bash
# Using uvicorn directly
uvicorn app.api.app:app --reload --host 0.0.0.0 --port 8000

# Or use the factory function
python -c "from app.api.app import build_fastapi_app; import uvicorn; app = build_fastapi_app(); uvicorn.run(app, host='0.0.0.0', port=8000)"
```

### Access API Documentation
Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Architecture Notes

### Hexagonal Architecture (Clean Architecture)

This implementation follows hexagonal architecture principles:

1. **Domain Layer** (`app/domain/`): Pure business logic and entities
2. **Application Layer** (`app/application/use_cases/`): Use cases orchestrating business logic
3. **Ports** (`app/ports/`): Interfaces for external systems
4. **Adapters** (`app/adapters/`): Implementations of ports
5. **Controllers** (`app/api/controllers/`): HTTP adapters (FastAPI routes)

### Key Design Decisions

- **Controllers are lightweight**: No business logic in controllers, only request/response handling
- **Dependency injection**: Composition root (`app/composition.py`) wires dependencies
- **In-memory adapters for tests**: No external dependencies (DB, Redis) required for API tests
- **HMAC authentication**: Secure service-to-service authentication
- **Idempotency**: Wallet registration is idempotent (safe to retry)

### Testing Strategy

- **Unit tests** (`tests/unit/`): Test domain services and business logic
- **API tests** (`tests/api/`): Test HTTP endpoints using FastAPI TestClient with in-memory adapters
- **No mocking of domain layer**: Tests use real implementations with in-memory storage

---

## CI/CD

Tests run automatically on push/PR via GitHub Actions:
```yaml
# .github/workflows/ci.yml runs:
- Unit tests (domain, ports, application layers)
- API tests (controllers, HMAC auth)
- Linting (black, flake8)
- Docker build
```

---

## Troubleshooting

### Common Issues

**HMAC signature mismatch:**
- Ensure timestamp is current (within 5 minutes)
- Check that body matches exactly (including whitespace)
- Verify secret is correct

**Link token invalid:**
- Tokens expire after 60 minutes
- Tokens can only be consumed once
- Check token string is copied correctly

**User not found:**
- Ensure user exists in the system
- Check UUID format is valid

---

## Next Steps

Potential future enhancements:
- Add database adapters (PostgreSQL/SQLAlchemy)
- Add Redis adapters for caching
- Implement user authentication for non-HMAC endpoints
- Add rate limiting
- Add API key management endpoints
- Add webhook notifications
