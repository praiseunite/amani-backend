# Wallet Balance Synchronization

## Overview

The Wallet Balance Synchronization feature provides idempotent, concurrent-safe synchronization of wallet balances from third-party payment providers. This is Step 6 in the hexagonal architecture implementation.

## Architecture

Following hexagonal (ports & adapters) architecture:

### Domain Layer
- **WalletBalanceSnapshot**: Entity representing a wallet balance at a specific point in time
  - Fields: wallet_id, provider, balance, currency, external_balance_id, as_of, metadata, created_at

### Application Layer
- **WalletBalanceSyncService**: Orchestrates balance synchronization
  - Implements idempotency by checking for existing snapshots
  - Handles race conditions and duplicate requests
  - Records audit events for new syncs
  
### Port Interfaces
- **WalletBalanceSyncPort**: Interface for balance snapshot operations
  - `sync_balance(wallet_id, idempotency_key)`: Sync wallet balance
  - `get_latest(wallet_id)`: Get latest snapshot
  - `get_by_external_id(external_balance_id)`: Get by provider event ID
  - `save_snapshot(snapshot, idempotency_key)`: Save new snapshot
  - `get_by_idempotency_key(idempotency_key)`: Get by idempotency key

- **WalletProviderPort**: Interface for fetching balances from providers
  - `fetch_balance(wallet_id, provider, provider_account_id)`: Fetch current balance

### Adapters
- **InMemory**: For testing
  - InMemoryWalletBalanceSync
  - InMemoryWalletProvider (mock provider)
  
- **SQL**: For production (PostgreSQL)
  - SQLWalletBalanceSync
  - (Provider adapter to be implemented per provider)

### API Layer
- `POST /api/v1/wallets/{wallet_id}/sync-balance`: Sync wallet balance
- `GET /api/v1/wallets/{wallet_id}/balance`: Get latest balance

## Database Schema

### wallet_balance_snapshot Table

```sql
CREATE TABLE wallet_balance_snapshot (
    id BIGSERIAL PRIMARY KEY,
    external_id UUID NOT NULL UNIQUE,
    wallet_id UUID NOT NULL,
    provider ENUM('fincra', 'paystack', 'flutterwave') NOT NULL,
    balance NUMERIC(20, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    external_balance_id VARCHAR(255) UNIQUE,
    as_of TIMESTAMP NOT NULL,
    metadata JSON,
    idempotency_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMP NOT NULL,
    
    CONSTRAINT uq_wallet_balance_snapshot_wallet_id_as_of 
        UNIQUE (wallet_id, as_of)
);

-- Indexes
CREATE INDEX ix_wallet_balance_snapshot_wallet_id ON wallet_balance_snapshot(wallet_id);
CREATE INDEX ix_wallet_balance_snapshot_provider ON wallet_balance_snapshot(provider);
CREATE UNIQUE INDEX ix_wallet_balance_snapshot_external_balance_id 
    ON wallet_balance_snapshot(external_balance_id) 
    WHERE external_balance_id IS NOT NULL;
CREATE UNIQUE INDEX ix_wallet_balance_snapshot_idempotency_key 
    ON wallet_balance_snapshot(idempotency_key) 
    WHERE idempotency_key IS NOT NULL;
```

## Idempotency Guarantees

The service ensures idempotent balance synchronization through multiple mechanisms:

1. **Idempotency Key**: Client-provided key to prevent duplicate syncs
   - Checked first before fetching from provider
   - Returns existing snapshot if found

2. **External Balance ID**: Provider-specific balance event ID
   - Checked after fetching from provider
   - Prevents duplicate snapshots from same provider event

3. **Wallet ID + Timestamp**: Unique constraint on (wallet_id, as_of)
   - Prevents multiple snapshots at exact same time
   - Handles edge case race conditions

4. **Race Condition Handling**: Catches `DuplicateEntryError` and fetches existing snapshot

## Usage Examples

### Sync Balance via API

```bash
# Sync wallet balance
curl -X POST http://localhost:8000/api/v1/wallets/{wallet_id}/sync-balance

# Sync with idempotency key
curl -X POST "http://localhost:8000/api/v1/wallets/{wallet_id}/sync-balance?idempotency_key=idem_123"

# Get latest balance
curl -X GET http://localhost:8000/api/v1/wallets/{wallet_id}/balance
```

### Programmatic Usage

```python
from app.application.services.wallet_balance_sync_service import WalletBalanceSyncService

# Sync balance
snapshot = await service.sync_balance(
    wallet_id=wallet_id,
    idempotency_key="optional_key"
)

# Get latest balance
latest = await service.get_latest_balance(wallet_id=wallet_id)
```

## Testing

### Unit Tests
- Test idempotent sync with same idempotency key
- Test idempotent sync with same external_balance_id
- Test creating new snapshots on balance changes
- Test not creating snapshots when balance unchanged
- Test audit event recording
- Coverage: 10 tests, all passing

### Integration Tests
- Test concurrent syncs with same idempotency key
- Test concurrent syncs with same external_balance_id
- Test race condition handling
- Test concurrent syncs for different wallets
- Test provider fetch optimization
- Coverage: 7 tests, all passing

### API Tests
- Test sync endpoint with/without idempotency key
- Test get balance endpoint
- Test multiple syncs with balance changes
- Coverage: 5 tests, all passing

## Troubleshooting

### Balance not syncing
1. Check if provider adapter is configured correctly
2. Verify wallet exists in wallet_registry
3. Check audit logs for sync attempts
4. Look for provider API errors

### Duplicate snapshots
- Should not happen due to unique constraints
- Check if external_balance_id is being set correctly
- Verify idempotency keys are unique per request

### Race condition errors
- Service handles these automatically by fetching existing snapshot
- If errors persist, check database constraint configuration

## Metrics & Monitoring

The service records audit events for:
- New balance syncs (action: "sync_balance")
- Includes: wallet_id, provider, balance, currency, external_balance_id, idempotency_key

Recommended metrics to track:
- Sync attempt rate
- Sync success rate
- Sync latency
- Duplicate request rate (idempotent returns)
- Provider API failure rate

## Migration

To apply the database migration:

```bash
# Run migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Future Enhancements

1. **Provider Adapters**: Implement real provider adapters (Fincra, Paystack, Flutterwave)
2. **Scheduled Sync**: Background job to sync balances periodically
3. **Webhooks**: Listen to provider balance change events
4. **Balance History**: Query historical balances for analytics
5. **Alerts**: Alert on significant balance changes or discrepancies
