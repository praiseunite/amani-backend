"""
# Wallet Registry Runbook

## Purpose
Procedures for deploying migrations, verifying idempotency indices, and recovering from duplicate registration errors.

## Apply migration
1. Take DB backup.
2. Run alembic upgrade head against staging/test DB and validate the table exists:
   SELECT id, provider, provider_wallet_id FROM wallet_registry LIMIT 5;

## Verify unique indices
- Provider+provider_wallet_id index:
  SELECT * FROM wallet_registry WHERE provider='lnbits' AND provider_wallet_id='w_abc';
- Idempotency index:
  SELECT * FROM wallet_registry WHERE idempotency_key='key-1';

## Recovering duplicates
- If duplicates are discovered due to a bug, identify canonical record and remove duplicates after stakeholder approval.
- Ensure audit log contained enough info to map duplicates to requests.

## Misc
- Monitor unique index violations in logs and alert on repeated occurrences.
"""