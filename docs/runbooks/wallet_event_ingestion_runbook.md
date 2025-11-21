# Wallet Event Ingestion Runbook

## Overview

The wallet event ingestion system provides idempotent, audit-trailed ingestion of wallet transaction events for historical reconstruction and analysis. This is part of Step 7 of the hexagonal architecture implementation.

## Architecture

### Components

1. **Domain Entity**: `WalletTransactionEvent` - Core event representation
2. **Port Interface**: `WalletEventIngestionPort` - Abstraction for event storage
3. **Application Service**: `WalletEventIngestionService` - Business logic orchestration
4. **Adapters**:
   - `InMemoryWalletEventIngestion` - Testing adapter
   - `SQLWalletEventIngestion` - Production PostgreSQL adapter
5. **API Endpoints**:
   - `POST /api/v1/wallets/{wallet_id}/events/ingest` - Ingest events
   - `GET /api/v1/wallets/{wallet_id}/events` - List events

### Event Types

The system supports the following event types:
- `deposit` - Funds deposited into wallet
- `withdrawal` - Funds withdrawn from wallet
- `transfer_in` - Funds transferred in from another wallet
- `transfer_out` - Funds transferred out to another wallet
- `fee` - Fee charged
- `refund` - Funds refunded
- `hold` - Funds placed on hold
- `release` - Funds released from hold

## Database Schema

### Table: wallet_transaction_event

```sql
CREATE TABLE wallet_transaction_event (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    external_id UUID UNIQUE NOT NULL,
    wallet_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- 'fincra', 'paystack', 'flutterwave'
    event_type VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    provider_event_id VARCHAR(255),
    idempotency_key VARCHAR(255) UNIQUE,
    metadata JSON,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

### Indexes

- `ix_wallet_transaction_event_external_id` - Unique index on external_id
- `ix_wallet_transaction_event_wallet_id` - Index for wallet queries
- `ix_wallet_transaction_event_occurred_at` - Index for time-based queries
- `ix_wallet_transaction_event_provider_event_id` - Index for provider deduplication
- `ix_wallet_transaction_event_idempotency_key` - Unique index for idempotency
- `ix_wallet_transaction_event_provider_provider_event_id` - Composite index for provider+event lookups
- `ix_wallet_transaction_event_wallet_id_occurred_at` - Composite index for efficient listing

## API Usage

### Ingest Event

**Endpoint**: `POST /api/v1/wallets/{wallet_id}/events/ingest`

**Authentication**: HMAC-based authentication required

**Request Body**:
```json
{
  "wallet_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider": "fincra",
  "event_type": "deposit",
  "amount": 100.50,
  "currency": "USD",
  "occurred_at": "2025-11-21T08:00:00Z",
  "provider_event_id": "provider_evt_12345",
  "metadata": {
    "transaction_id": "tx_12345",
    "note": "Customer deposit"
  },
  "idempotency_key": "idem_key_12345"
}
```

**Response**:
```json
{
  "event_id": "456e7890-e89b-12d3-a456-426614174000",
  "wallet_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider": "fincra",
  "event_type": "deposit",
  "amount": 100.50,
  "currency": "USD",
  "provider_event_id": "provider_evt_12345",
  "metadata": {...},
  "occurred_at": "2025-11-21T08:00:00Z",
  "created_at": "2025-11-21T08:00:01Z"
}
```

### List Events

**Endpoint**: `GET /api/v1/wallets/{wallet_id}/events?limit=100&offset=0`

**Authentication**: HMAC-based authentication required

**Query Parameters**:
- `limit` - Maximum events to return (1-1000, default 100)
- `offset` - Number of events to skip (default 0)

**Response**:
```json
{
  "events": [
    {
      "event_id": "456e7890-e89b-12d3-a456-426614174000",
      "wallet_id": "123e4567-e89b-12d3-a456-426614174000",
      "provider": "fincra",
      "event_type": "deposit",
      "amount": 100.50,
      "currency": "USD",
      "provider_event_id": "provider_evt_12345",
      "metadata": {...},
      "occurred_at": "2025-11-21T08:00:00Z",
      "created_at": "2025-11-21T08:00:01Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

## Idempotency

The system ensures idempotent event ingestion through three mechanisms:

1. **event_id (external_id)**: Unique identifier for the event
2. **provider_event_id**: Provider's unique event identifier for deduplication
3. **idempotency_key**: Client-supplied key for request-level idempotency

When duplicate events are detected, the existing event is returned without creating a new entry.

## Concurrency Safety

The SQL adapter uses database unique constraints to ensure race-safe concurrent event ingestion:

- Multiple simultaneous requests with the same `external_id` will result in only one event being created
- Multiple simultaneous requests with the same `provider_event_id` will be deduplicated
- Multiple simultaneous requests with the same `idempotency_key` will be deduplicated

The adapter translates `IntegrityError` exceptions into domain-level `DuplicateEntryError` for clean error handling.

## Monitoring and Metrics

### Audit Events

All successful event ingestions are logged to the audit trail with:
- Action: `ingest_wallet_event`
- Resource Type: `wallet_transaction_event`
- Resource ID: Event ID
- Details: Wallet ID, provider, event type, amount, currency, occurred_at

### Application Logs

Key log messages:
- "Event ingestion success" - Successful new event ingestion
- "Event ingestion duplicate (provider_event_id)" - Duplicate detected by provider_event_id

## Troubleshooting

### Problem: Events Not Being Ingested

**Symptoms**: POST requests to ingest endpoint return errors

**Possible Causes**:
1. Invalid authentication (401)
2. Invalid request body (400)
3. Database connectivity issues (500)

**Resolution**:
1. Verify HMAC authentication headers are correct
2. Validate request body against schema
3. Check database connection and migrations
4. Review application logs for detailed error messages

### Problem: Duplicate Events

**Symptoms**: Multiple events with similar data but different IDs

**Possible Causes**:
1. Not using `provider_event_id` for provider-side deduplication
2. Not using `idempotency_key` for client-side deduplication
3. Race conditions during concurrent ingestion

**Resolution**:
1. Always include `provider_event_id` from the provider's webhook/API
2. Use `idempotency_key` for client-side request retries
3. The system is designed to handle race conditions automatically

### Problem: Slow Event Listing

**Symptoms**: GET requests to list events endpoint are slow

**Possible Causes**:
1. Large number of events without pagination
2. Missing or inefficient database indexes
3. Querying across many wallets

**Resolution**:
1. Use smaller `limit` values (e.g., 50 or 100)
2. Verify indexes exist: `ix_wallet_transaction_event_wallet_id_occurred_at`
3. Ensure migrations have been run: `alembic upgrade head`
4. Consider adding database query monitoring

## Database Migration

### Apply Migration

```bash
# Run migration
alembic upgrade head

# Verify table exists
psql $DATABASE_URL -c "\d wallet_transaction_event"
```

### Rollback Migration

```bash
# Rollback to previous version
alembic downgrade -1

# Verify table dropped
psql $DATABASE_URL -c "\d wallet_transaction_event"
```

## Backfilling Historical Events

To backfill events from provider APIs:

```python
from datetime import datetime
from uuid import uuid4
from app.composition import build_app_components
from app.domain.entities import WalletProvider, WalletEventType

# Get service
components = build_app_components()
service = components["wallet_event_ingestion_service"]

# Ingest historical event
await service.ingest_event(
    wallet_id=uuid4(),  # Your wallet ID
    provider=WalletProvider.FINCRA,
    event_type=WalletEventType.DEPOSIT,
    amount=100.0,
    currency="USD",
    occurred_at=datetime(2025, 1, 1, 12, 0, 0),
    provider_event_id="historical_event_123",
)
```

### Bulk Backfill Script

For bulk backfilling, create a script that:
1. Fetches events from provider API
2. Transforms to `WalletTransactionEvent` format
3. Calls `ingest_event` with `provider_event_id` for deduplication
4. Handles rate limiting and errors gracefully
5. Logs progress and any skipped events

## Testing

### Unit Tests

```bash
# Run wallet event ingestion unit tests
pytest tests/unit/test_wallet_event_ingestion.py -v
```

### Integration Tests

```bash
# Set test database URL
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test_db"

# Run migrations on test database
alembic upgrade head

# Run integration tests
pytest tests/integration/test_wallet_event_ingestion_concurrency.py -v
```

### Manual Testing

```bash
# Start the application
python run_hexagonal.py

# Test ingest endpoint (requires valid HMAC auth)
curl -X POST http://localhost:8000/api/v1/wallets/{wallet_id}/events/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key-ID: your-key-id" \
  -H "X-Signature: hmac-signature" \
  -H "X-Timestamp: timestamp" \
  -d '{
    "wallet_id": "123e4567-e89b-12d3-a456-426614174000",
    "provider": "fincra",
    "event_type": "deposit",
    "amount": 100.0,
    "currency": "USD",
    "occurred_at": "2025-11-21T08:00:00Z",
    "provider_event_id": "test_event_1"
  }'

# Test list endpoint
curl http://localhost:8000/api/v1/wallets/{wallet_id}/events?limit=10 \
  -H "X-API-Key-ID: your-key-id" \
  -H "X-Signature: hmac-signature" \
  -H "X-Timestamp: timestamp"
```

## Security Considerations

1. **Authentication**: All endpoints require HMAC authentication
2. **Authorization**: Verify wallet ownership before ingesting/listing events
3. **Input Validation**: All inputs validated via Pydantic models
4. **SQL Injection**: Using parameterized queries via SQLAlchemy
5. **PII Handling**: Metadata field may contain PII - handle according to data protection policies
6. **Audit Trail**: All ingestions logged for compliance

## Performance Characteristics

### Expected Latencies

- Event ingestion (new): ~10-50ms
- Event ingestion (duplicate): ~5-20ms
- Event listing (100 events): ~20-100ms
- Event listing (with pagination): ~10-50ms per page

### Scalability

- Horizontal scaling: API layer can be scaled horizontally
- Database: Indexes support efficient querying for millions of events
- Throughput: Design supports 1000+ events/second with proper database sizing

## Related Documentation

- [Architecture Documentation](../ARCHITECTURE.md)
- [Wallet Registry Runbook](./wallet_registry_runbook.md)
- [Wallet Balance Sync Documentation](../docs/WALLET_BALANCE_SYNC.md)
