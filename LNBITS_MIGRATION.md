# LNbits Integration Migration Guide

This guide helps you migrate existing deployments to include the new LNbits Lightning Network integration.

## Overview

The LNbits integration adds Lightning Network payment capabilities alongside the existing FinCra payment provider. This is a **non-breaking change** - existing FinCra functionality remains unchanged.

## What's New

### Added Providers

- **LNbits**: Lightning Network payment provider
- New `WalletProvider.LNBITS` enum value

### New API Endpoints

1. **Lightning Operations** (`/api/v1/lightning/*`):
   - Wallet creation and management
   - Invoice generation (BOLT11)
   - Payment monitoring
   - Balance checking

2. **Bot Features** (`/api/v1/bot/*`):
   - Magic links (claimable cheques)
   - Faucet system
   - Internal transfers
   - Withdrawal PIN protection

### New Dependencies

No new dependencies! The integration uses existing packages:
- `httpx` (already in requirements.txt)
- Python standard library

## Migration Steps

### 1. Update Code (Pull Latest)

```bash
git checkout main
git pull origin main
```

Or merge the integration branch:

```bash
git merge feat/lnbits-integration-migration
```

### 2. Update Environment Variables

Add to your `.env` file:

```env
# LNbits Lightning API
LNBITS_API_KEY=your-lnbits-admin-key-here
LNBITS_BASE_URL=https://legend.lnbits.com
```

**How to get LNbits credentials:**

1. Go to https://legend.lnbits.com (or your LNbits instance)
2. Create a wallet or use existing
3. Copy the **Admin Key** (not Invoice key)
4. Paste as `LNBITS_API_KEY`

**For production:**
- Use your own LNbits instance for better control
- Consider using LNbits extensions for advanced features
- Secure the Admin Key properly (use secrets management)

### 3. Restart Application

```bash
# Docker deployment
docker-compose down
docker-compose up -d

# Manual deployment
systemctl restart amani-backend

# Development
# Stop the server (Ctrl+C) and restart:
uvicorn app.main:app --reload
```

### 4. Verify Integration

Test that endpoints are available:

```bash
# Health check
curl https://your-domain.com/api/v1/health

# Check if Lightning endpoints are available (requires auth)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-domain.com/api/v1/lightning/balance
```

### 5. Database Migration (If Needed)

**Currently**: No database schema changes required. The integration works with existing database structure.

**Future**: If you plan to persist Lightning wallet data (recommended for production), you may want to:

1. Add Lightning wallet tracking table
2. Store magic link metadata
3. Track faucet claims with timestamps
4. Store encrypted withdrawal PINs

Example future migration (not required now):

```sql
-- Lightning wallet tracking
CREATE TABLE lightning_wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    wallet_id VARCHAR(255) NOT NULL,
    wallet_name VARCHAR(255),
    balance_msat BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, wallet_id)
);

-- Magic links (cheques)
CREATE TABLE magic_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id VARCHAR(255) UNIQUE NOT NULL,
    creator_user_id UUID NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    memo TEXT,
    payment_hash VARCHAR(255),
    claimed_by_user_id UUID REFERENCES users(id),
    claimed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Faucet claims
CREATE TABLE faucet_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    claimed_at TIMESTAMP DEFAULT NOW(),
    next_claim_at TIMESTAMP NOT NULL
);

-- Withdrawal PINs (encrypted)
CREATE TABLE withdrawal_pins (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    pin_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Breaking Changes

**None.** This is a fully backward-compatible addition.

Existing functionality:
- ✅ FinCra payment endpoints still work
- ✅ Existing wallet registrations unchanged
- ✅ All authentication mechanisms work as before
- ✅ Database schema remains compatible

## Configuration Changes

### Required

```env
LNBITS_API_KEY=<your-key>
LNBITS_BASE_URL=<your-instance>
```

### Optional

No optional configurations added. Default values are set in `app/core/config.py`:

```python
LNBITS_API_KEY: str = ""  # Empty by default (non-breaking)
LNBITS_BASE_URL: str = "https://legend.lnbits.com"
```

If `LNBITS_API_KEY` is not set, Lightning endpoints will return errors gracefully.

## Testing After Migration

### 1. Basic Health Check

```bash
curl https://your-domain.com/api/v1/health
```

Should return `200 OK` with healthy status.

### 2. Test Lightning Endpoints (Authenticated)

First, login to get a token:

```bash
TOKEN=$(curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')
```

Then test Lightning endpoints:

```bash
# Create wallet
curl -X POST https://your-domain.com/api/v1/lightning/wallet/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_name":"testuser","wallet_name":"Test Wallet"}'

# Get balance
curl -H "Authorization: Bearer $TOKEN" \
  https://your-domain.com/api/v1/lightning/balance

# Create invoice
curl -X POST https://your-domain.com/api/v1/lightning/invoice/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":1000,"memo":"Test"}'
```

### 3. Test Bot Features

```bash
# Claim faucet
curl -X POST https://your-domain.com/api/v1/bot/faucet/claim \
  -H "Authorization: Bearer $TOKEN"

# Create magic link
curl -X POST https://your-domain.com/api/v1/bot/magic-link/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"memo":"Test link","expiry_hours":24}'
```

### 4. Run Automated Tests

```bash
# All tests
pytest

# Just Lightning tests
pytest tests/test_lnbits_client.py tests/test_lnbits_schemas.py

# With coverage
pytest --cov=app --cov-report=html
```

## Rollback Plan

If issues arise, you can safely roll back:

### 1. Revert Code Changes

```bash
# If using git
git revert <commit-hash>

# Or checkout previous version
git checkout <previous-tag>
```

### 2. Remove Environment Variables

Remove or comment out in `.env`:

```env
# LNBITS_API_KEY=...
# LNBITS_BASE_URL=...
```

### 3. Restart Application

```bash
docker-compose restart
# or
systemctl restart amani-backend
```

### 4. Verify

Test that existing FinCra functionality still works:

```bash
curl https://your-domain.com/api/v1/payment/balance \
  -H "Authorization: Bearer $TOKEN"
```

## Common Issues and Solutions

### Issue: "LNbits API key not configured"

**Solution**: Set `LNBITS_API_KEY` in your `.env` file.

```env
LNBITS_API_KEY=your-admin-key-here
```

### Issue: "Request timeout" or "Connection refused"

**Cause**: Cannot reach LNbits instance.

**Solutions**:
1. Check `LNBITS_BASE_URL` is correct
2. Verify LNbits instance is running
3. Check firewall rules allow outbound connections
4. Test connectivity: `curl https://legend.lnbits.com/api/v1/wallet`

### Issue: "Invalid or expired token"

**Cause**: Authentication token issue (not related to Lightning).

**Solution**: Login again to get a fresh token:

```bash
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'
```

### Issue: Import errors after update

**Cause**: Missing dependencies or Python cache issues.

**Solution**:

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Restart application
```

### Issue: Tests failing

**Cause**: Test database not configured or stale cache.

**Solution**:

```bash
# Use test environment
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/test_db"
export SECRET_KEY="test-secret-key"

# Run tests
pytest
```

## Monitoring

### Key Metrics to Monitor

1. **Lightning Endpoint Latency**
   - Monitor `/api/v1/lightning/*` response times
   - LNbits API calls add ~100-500ms latency

2. **Error Rates**
   - Watch for 502 errors (LNbits connectivity)
   - Monitor authentication failures

3. **LNbits Health**
   - Set up alerts for LNbits instance downtime
   - Monitor LNbits node connectivity

### Logging

New logs will appear for Lightning operations:

```json
{
  "message": "Lightning wallet created: wallet123 for user abc-def",
  "level": "INFO",
  "timestamp": "2025-11-24T04:36:45Z"
}
```

```json
{
  "message": "LNbits API error: Insufficient balance",
  "level": "ERROR",
  "timestamp": "2025-11-24T04:36:45Z"
}
```

Filter Lightning logs:

```bash
# Docker
docker-compose logs | grep "Lightning\|LNbits"

# Systemd
journalctl -u amani-backend | grep "Lightning\|LNbits"

# Log file
grep -i "lightning\|lnbits" logs/app.log
```

## Performance Considerations

### API Response Times

- Lightning operations: +100-500ms (LNbits API calls)
- Invoice creation: ~200ms
- Status checks: ~150ms
- Wallet creation: ~300ms

### Caching Recommendations

For production, consider caching:

1. **Wallet details**: Cache for 5-10 seconds
2. **Balance**: Cache for 2-5 seconds
3. **Invoice status**: No caching (real-time needed)

Example with Redis:

```python
# Get balance with caching
cache_key = f"lightning:balance:{user_id}"
cached_balance = await redis.get(cache_key)

if cached_balance:
    return json.loads(cached_balance)

balance = await lnbits_client.get_balance()
await redis.setex(cache_key, 5, json.dumps(balance))
return balance
```

### Rate Limiting

Consider rate limiting Lightning endpoints:

- Invoice creation: 10/minute per user
- Status checks: 60/minute per user
- Faucet claims: 1/day per user (already implemented)

## Security Considerations

### 1. Protect Admin Keys

- Never commit `.env` files
- Use secrets management (AWS Secrets Manager, Vault, etc.)
- Rotate keys periodically

### 2. Withdrawal PINs

Current implementation stores PINs in memory (not persistent). For production:

```python
# Use bcrypt for PIN hashing
import bcrypt

hashed_pin = bcrypt.hashpw(pin.encode(), bcrypt.gensalt())
# Store hashed_pin in database
```

### 3. Magic Link Security

- Links expire after set time (default 24h)
- One-time use only
- Cannot claim own links
- Rate limit creation: Consider 10/hour per user

### 4. Internal Transfers

- Require PIN for large amounts (>10,000 sats)
- Log all transfers for audit
- Rate limit: 20/hour per user

## Production Recommendations

### 1. Self-Host LNbits

For production, self-host LNbits instead of using public instances:

```bash
# Docker deployment
git clone https://github.com/lnbits/lnbits.git
cd lnbits
docker-compose up -d
```

Benefits:
- Full control over uptime
- Better privacy
- Custom extensions
- No rate limits

### 2. Use Dedicated Node

Connect LNbits to your own Lightning node for:
- Better reliability
- Lower fees
- Full sovereignty
- Better liquidity management

### 3. Implement Webhooks

Set up webhook endpoint for real-time payment notifications:

```python
@app.post("/webhooks/lightning/payment")
async def lightning_webhook(payload: dict):
    # Verify webhook signature
    # Process payment notification
    # Update user balance
    pass
```

### 4. Add Monitoring

Use tools like:
- Prometheus for metrics
- Grafana for dashboards
- Sentry for error tracking (already integrated)
- Custom alerts for LNbits downtime

### 5. Backup Strategy

Regularly backup:
- LNbits wallet data
- Admin keys (encrypted)
- Lightning channel state
- Transaction history

## Support

For migration help:

- GitHub Issues: https://github.com/praiseunite/amani-backend/issues
- Documentation: LIGHTNING_INTEGRATION.md
- Email: support@yourdomain.com

## Changelog

### Version 1.1.0 (2025-11-24)

**Added:**
- LNbits Lightning Network integration
- Lightning wallet operations
- Invoice generation and payment monitoring
- Bot features (magic links, faucet, internal transfers)
- Withdrawal PIN protection
- Comprehensive tests and documentation

**Changed:**
- Added `LNBITS` to `WalletProvider` enum
- Updated configuration with LNbits settings
- Extended API with `/lightning/*` and `/bot/*` endpoints

**Fixed:**
- None (new feature addition)

**Security:**
- Added PIN protection for withdrawals
- Magic link security features
- Rate limiting on faucet claims

## Next Steps

After successful migration:

1. Update bot integration to use new endpoints
2. Configure monitoring for Lightning operations
3. Set up webhooks for real-time notifications
4. Consider implementing persistent storage for bot features
5. Review and adjust rate limits based on usage
6. Set up alerts for LNbits connectivity issues

## Appendix: File Changes

### New Files

```
app/core/lnbits.py                    # LNbits client
app/routes/lightning.py               # Lightning endpoints
app/routes/bot.py                     # Bot feature endpoints
app/schemas/lnbits.py                 # Lightning schemas
tests/test_lnbits_client.py          # Client tests
tests/test_lnbits_schemas.py         # Schema tests
LIGHTNING_INTEGRATION.md              # Integration guide
LNBITS_MIGRATION.md                   # This file
```

### Modified Files

```
app/domain/entities.py                # Added LNBITS to WalletProvider
app/core/config.py                    # Added LNBITS configuration
app/main.py                           # Registered new routes
.env.example                          # Added LNBITS variables
```

### No Changes Required

```
app/core/fincra.py                   # Unchanged
app/routes/payment.py                # Unchanged
Database migrations                  # None needed yet
```
