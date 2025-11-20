# Phase 3: HTTP Controllers and HMAC Service Auth

This PR implements Phase 3 of the hexagonal architecture refactoring, adding HTTP controllers (FastAPI) with HMAC service authentication while maintaining business logic in the application/domain layers.

## Implementation Summary

### New Components Added

#### Application Layer
- `BotLinkUseCase` - Consume link token and link provider ID
- `RegisterWalletUseCase` - Idempotent wallet registration
- `GetUserStatusUseCase` - Get user status from repository
- `BotLinkService` - Domain service for bot linking
- `WalletRegistryService` - Domain service for wallet registration with idempotency

#### Ports & Adapters
- `ApiKeyPort` - Interface for loading API key secrets
- `InMemoryApiKeyRepository` - In-memory adapter for testing

#### HTTP Layer (FastAPI)
- `app/api/app.py` - FastAPI app factory with dependency wiring
- `app/api/deps/hmac_auth.py` - HMAC verification middleware
- `app/api/controllers/link_tokens.py` - POST /api/v1/link_tokens/create
- `app/api/controllers/bot_link.py` - POST /api/v1/bot/link (HMAC auth)
- `app/api/controllers/wallets.py` - POST /api/v1/wallets/register (HMAC auth)
- `app/api/controllers/users.py` - GET /api/v1/users/{id}/status

#### Composition Root
- Updated `app/composition.py` with `build_app_components()` and `build_fastapi_app()`
- Wires all dependencies for in-memory (testing) and production modes

#### Testing
- `tests/api/test_bot_link.py` - Tests for bot link endpoint with HMAC auth
- `tests/api/test_wallets_register.py` - Tests for wallet registration (idempotency)
- `tests/api/test_users_status.py` - Tests for user status endpoint
- `tests/api/test_link_tokens.py` - Tests for link token creation
- All tests use FastAPI TestClient with in-memory adapters (no DB/Redis required)

#### CI/CD
- Updated `.github/workflows/ci.yml` to run API tests separately

#### Local Development
- `run_hexagonal.py` - Entrypoint to run the new hexagonal API locally

## API Endpoints

### 1. Create Link Token
```bash
POST /api/v1/link_tokens/create
```

**Request:**
```bash
curl -X POST http://127.0.0.1:8001/api/v1/link_tokens/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "provider": "fincra"
  }'
```

**Response:**
```json
{
  "token": "abc123def456...",
  "expires_at": "2024-11-20T14:00:00",
  "provider": "fincra"
}
```

### 2. Bot Link (HMAC Auth Required)
```bash
POST /api/v1/bot/link
```

**Request:**
```bash
# Generate HMAC signature
KEY_ID="test-bot-key"
SECRET="test-secret"
TIMESTAMP=$(date +%s)
MESSAGE="${KEY_ID}:${TIMESTAMP}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -X POST http://127.0.0.1:8001/api/v1/bot/link \
  -H "Content-Type: application/json" \
  -H "X-API-KEY-ID: $KEY_ID" \
  -H "X-API-TIMESTAMP: $TIMESTAMP" \
  -H "X-API-SIGNATURE: $SIGNATURE" \
  -d '{
    "token": "abc123def456...",
    "provider_account_id": "fincra-account-123"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Bot linked successfully"
}
```

### 3. Register Wallet (HMAC Auth Required)
```bash
POST /api/v1/wallets/register
```

**Request:**
```bash
# Use same HMAC headers as above
curl -X POST http://127.0.0.1:8001/api/v1/wallets/register \
  -H "Content-Type: application/json" \
  -H "X-API-KEY-ID: $KEY_ID" \
  -H "X-API-TIMESTAMP: $TIMESTAMP" \
  -H "X-API-SIGNATURE: $SIGNATURE" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "provider": "fincra",
    "provider_account_id": "fincra-account-123",
    "provider_customer_id": "customer-456",
    "metadata": {"source": "bot"}
  }'
```

**Response:**
```json
{
  "wallet_id": "789e4567-e89b-12d3-a456-426614174111",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider": "fincra",
  "provider_account_id": "fincra-account-123",
  "is_active": true
}
```

### 4. Get User Status
```bash
GET /api/v1/users/{id}/status
```

**Request:**
```bash
curl -X GET http://127.0.0.1:8001/api/v1/users/123e4567-e89b-12d3-a456-426614174000/status
```

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "client",
  "is_active": true,
  "is_verified": false
}
```

## HMAC Authentication

Service-to-service endpoints require HMAC authentication:

**Required Headers:**
- `X-API-KEY-ID`: API key identifier
- `X-API-TIMESTAMP`: Unix timestamp (must be within 5-minute window)
- `X-API-SIGNATURE`: HMAC-SHA256 signature

**Signature Calculation:**
```
message = "{KEY_ID}:{TIMESTAMP}"
signature = HMAC-SHA256(secret, message)
```

**Python Example:**
```python
import hmac
import hashlib
from datetime import datetime

key_id = "test-bot-key"
secret = "test-secret"
timestamp = int(datetime.utcnow().timestamp())

message = f"{key_id}:{timestamp}".encode("utf-8")
signature = hmac.new(
    secret.encode("utf-8"),
    message,
    hashlib.sha256
).hexdigest()

headers = {
    "X-API-KEY-ID": key_id,
    "X-API-TIMESTAMP": str(timestamp),
    "X-API-SIGNATURE": signature,
}
```

## Running Locally

### Run New Hexagonal API
```bash
# Install dependencies
pip install -r requirements.txt

# Run the new API on port 8001
python run_hexagonal.py
```

### Run Tests
```bash
# Run all tests
pytest tests/unit/ tests/api/ -v

# Run only API tests
pytest tests/api/ -v

# Run with coverage
pytest tests/unit/ tests/api/ --cov=app --cov-report=html
```

## Architecture Notes

### Separation of Concerns
- **Controllers**: Lightweight HTTP adapters, no business logic
- **Use Cases**: Application-level orchestration
- **Domain Services**: Business logic and policies
- **Ports**: Interfaces for external dependencies
- **Adapters**: Implementations of ports (in-memory for tests)

### Idempotency
The wallet registration endpoint is idempotent - calling it multiple times with the same user_id and provider returns the same wallet entry.

### Security
- HMAC signatures use constant-time comparison (`secrets.compare_digest`)
- Timestamp validation prevents replay attacks
- 5-minute window for request timestamps
- All audit events are logged

### Testing Strategy
- Unit tests use in-memory adapters
- No database or Redis required for tests
- FastAPI TestClient for HTTP-level testing
- All endpoints have comprehensive test coverage

## Backward Compatibility

This PR is fully additive:
- No changes to existing endpoints or production behavior
- Old FastAPI app in `app/main.py` remains unchanged
- New endpoints are isolated under `/api/v1/` namespace
- No database schema changes

## CI/CD Updates

Updated GitHub Actions workflow to run API tests separately:
```yaml
- name: Run unit tests
  run: pytest tests/unit/ -v
  
- name: Run API tests
  run: pytest tests/api/ -v
```

## Next Steps

Future enhancements could include:
- Real database adapters for production
- API key management UI
- Rate limiting per API key
- Webhook support for async notifications
- OpenTelemetry tracing
