# Wallet Registry Runbook

## Overview

The Wallet Registry service provides idempotent and concurrent-safe wallet registration for the Amani backend. This runbook describes the service architecture, operations, and troubleshooting procedures.

## Architecture

### Components

1. **Application Service** (`app/application/services/wallet_registry_service.py`)
   - Implements idempotent registration logic
   - Handles race conditions at the application layer
   - Coordinates with port adapters and audit logging

2. **Port Interface** (`app/ports/wallet_registry.py`)
   - Abstract interface for wallet registry operations
   - Defines contract for storage adapters

3. **Adapters**
   - **In-Memory** (`app/adapters/inmemory/wallet_registry.py`) - For unit tests
   - **SQL** (`app/adapters/sql/wallet_registry.py`) - For production with PostgreSQL

4. **Domain Entity** (`app/domain/entities.py`)
   - `WalletRegistryEntry` - Pure business object

5. **Database Model** (`app/models/wallet_registry.py`)
   - SQLAlchemy ORM model for persistence

## Idempotency Strategy

The service ensures idempotent wallet registration through multiple mechanisms:

### 1. Idempotency Key Check
- Optional `idempotency_key` parameter for duplicate prevention
- Unique constraint on `idempotency_key` column
- Service checks this first before attempting registration

### 2. Provider + Wallet ID Check
- Unique constraint on `(user_id, provider, provider_account_id)`
- Ensures one wallet per user per provider per account
- Service checks this second if no idempotency_key

### 3. Race Condition Handling
- SQL adapter raises `IntegrityError` on constraint violations
- Service catches violations and fetches existing wallet
- Returns existing wallet instead of failing

## Database Schema

### Table: `wallet_registry`

```sql
CREATE TABLE wallet_registry (
    id BIGSERIAL PRIMARY KEY,
    external_id UUID NOT NULL UNIQUE,
    user_id UUID NOT NULL,
    provider wallet_provider NOT NULL,
    provider_account_id VARCHAR(255) NOT NULL,
    provider_customer_id VARCHAR(255),
    idempotency_key VARCHAR(255) UNIQUE,
    metadata JSON,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    
    CONSTRAINT uq_wallet_registry_user_provider_account 
        UNIQUE (user_id, provider, provider_account_id)
);

CREATE INDEX ix_wallet_registry_external_id ON wallet_registry(external_id);
CREATE INDEX ix_wallet_registry_user_id ON wallet_registry(user_id);
CREATE UNIQUE INDEX ix_wallet_registry_idempotency_key 
    ON wallet_registry(idempotency_key) WHERE idempotency_key IS NOT NULL;
```

## Operations

### Registering a Wallet

```python
from uuid import uuid4
from app.domain.entities import WalletProvider
from app.application.services.wallet_registry_service import WalletRegistryService

# Initialize service (usually via dependency injection)
service = WalletRegistryService(
    wallet_registry_port=sql_wallet_registry,
    audit_port=audit_port,
)

# Register wallet
result = await service.register(
    user_id=uuid4(),
    provider=WalletProvider.FINCRA,
    provider_wallet_id="fincra_wallet_123",
    idempotency_key="request_abc123",  # Optional but recommended
    provider_customer_id="customer_456",  # Optional
    metadata={"kyc_verified": True},  # Optional
)
```

### Idempotent Behavior

The service guarantees idempotent behavior:

```python
# First call - creates new wallet
result1 = await service.register(
    user_id=user_id,
    provider=WalletProvider.FINCRA,
    provider_wallet_id="wallet_123",
    idempotency_key="key_1",
)

# Second call - returns existing wallet (same idempotency_key)
result2 = await service.register(
    user_id=user_id,
    provider=WalletProvider.FINCRA,
    provider_wallet_id="wallet_123",
    idempotency_key="key_1",
)

assert result1.id == result2.id  # Same wallet returned
```

## Testing

### Unit Tests

Run unit tests with in-memory adapter:

```bash
pytest tests/unit/test_wallet_registry_idempotency.py -v
```

Unit tests cover:
- New wallet registration
- Idempotent behavior with same idempotency_key
- Idempotent behavior with same provider+wallet
- Different wallets for same provider
- Different providers with same wallet ID
- Metadata and customer ID handling
- Audit event recording

### Integration Tests

Integration tests require a test database:

```bash
# Set test database URL
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test_db"

# Run migrations
alembic upgrade head

# Run integration tests
pytest tests/integration/test_wallet_registry_concurrency.py -v
```

Integration tests cover:
- Concurrent registration with same idempotency_key
- Concurrent registration with same provider+wallet
- Concurrent registration of different wallets
- Sequential idempotent requests

## Troubleshooting

### Common Issues

#### 1. IntegrityError Not Caught

**Symptom**: Service raises IntegrityError instead of returning existing wallet

**Causes**:
- Exception handling not catching specific error types
- Database rollback not happening correctly

**Resolution**:
1. Check service exception handling logic
2. Verify SQL adapter raises IntegrityError correctly
3. Ensure session rollback occurs before retry

#### 2. Duplicate Wallets Created

**Symptom**: Multiple wallet entries for same user+provider+wallet_id

**Causes**:
- Missing unique constraint on database
- Migration not applied
- Race condition not handled properly

**Resolution**:
1. Verify migration applied: `alembic current`
2. Check constraint exists: 
   ```sql
   SELECT conname, contype 
   FROM pg_constraint 
   WHERE conrelid = 'wallet_registry'::regclass;
   ```
3. Re-apply migration if needed: `alembic upgrade head`

#### 3. Idempotency Key Not Working

**Symptom**: Duplicate registrations with same idempotency_key

**Causes**:
- Missing index on idempotency_key
- Service not checking idempotency_key first

**Resolution**:
1. Verify index exists:
   ```sql
   SELECT indexname 
   FROM pg_indexes 
   WHERE tablename = 'wallet_registry';
   ```
2. Check service logic order (should check idempotency_key first)

#### 4. Performance Issues

**Symptom**: Slow wallet registration

**Causes**:
- Missing indexes
- Too many sequential checks
- Database connection pool exhaustion

**Resolution**:
1. Verify all indexes created
2. Monitor database connection pool usage
3. Consider adding read replicas for high-read workloads

## Monitoring

### Key Metrics

1. **Registration Success Rate**
   - Track successful vs failed registrations
   - Alert on drops below 95%

2. **Idempotent Hit Rate**
   - Track how often idempotency prevents duplicates
   - High rate indicates good client behavior

3. **Race Condition Rate**
   - Track IntegrityError catch rate
   - High rate may indicate concurrency issues

4. **Query Performance**
   - Monitor query execution times
   - Alert on p99 > 100ms

### Audit Events

All successful registrations generate audit events:

```json
{
    "action": "register_wallet",
    "user_id": "uuid",
    "resource_type": "wallet_registry",
    "resource_id": "wallet_uuid",
    "details": {
        "provider": "fincra",
        "provider_wallet_id": "wallet_123",
        "idempotency_key": "key_1"
    }
}
```

## Migration Guide

### Applying the Migration

```bash
# Check current version
alembic current

# Apply wallet registry migration
alembic upgrade head

# Verify migration applied
alembic current
# Should show: 20251120_140218 (head)
```

### Rolling Back

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade d8311371c01f
```

## Best Practices

1. **Always Use Idempotency Keys**
   - Generate unique key per client request
   - Use format: `{service}_{timestamp}_{uuid}`
   - Example: `api_20251120_abc123`

2. **Handle Race Conditions**
   - Never assume registration will succeed on first try
   - Always handle IntegrityError gracefully
   - Return existing wallet on conflict

3. **Audit Logging**
   - Service automatically logs successful registrations
   - Monitor audit logs for security and compliance

4. **Testing in Production**
   - Use idempotency keys in production
   - Monitor for duplicate prevention
   - Track race condition resolution

## References

- [Hexagonal Architecture](../../ARCHITECTURE.md)
- [Database Setup](../../DATABASE_SETUP.md)
- [API Implementation](../../API_IMPLEMENTATION.md)
