# Lightning Network Integration Guide

This guide covers the LNbits Lightning Network integration in the Amani backend, providing bot developers with all the tools needed to integrate Lightning payments.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Lightning Endpoints](#lightning-endpoints)
- [Bot Features](#bot-features)
- [Integration with bitbot](#integration-with-bitbot)
- [Examples](#examples)
- [Error Handling](#error-handling)

## Overview

The Amani backend provides full Lightning Network integration via LNbits, enabling:

- **Lightning Wallets**: Create and manage Lightning wallets for users
- **Invoice Generation**: Create BOLT11 payment requests
- **Payment Monitoring**: Check invoice status and payment confirmations
- **Bot Features**: Magic links, faucet, internal transfers, and PIN protection

All endpoints are authenticated and follow REST principles.

## Setup

### 1. LNbits Configuration

Add to your `.env` file:

```env
# LNbits Lightning API
LNBITS_API_KEY=your-lnbits-admin-key-here
LNBITS_BASE_URL=https://legend.lnbits.com
```

To get your LNbits credentials:

1. Visit your LNbits instance (e.g., https://legend.lnbits.com)
2. Create a wallet
3. Copy the **Admin Key** (not the Invoice key)
4. Use the Admin Key as `LNBITS_API_KEY`

### 2. Dependencies

All required dependencies are included in `requirements.txt`. The integration uses:

- `httpx` for async HTTP requests
- Native LNbits REST API (no additional packages needed)

## Lightning Endpoints

Base path: `/api/v1/lightning`

All endpoints require authentication via Bearer token.

### Create Lightning Wallet

Create a new Lightning wallet for a user.

```http
POST /api/v1/lightning/wallet/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_name": "john_doe",
  "wallet_name": "John's Lightning Wallet"
}
```

**Response:**

```json
{
  "id": "wallet123abc",
  "name": "John's Lightning Wallet",
  "user": "john_doe",
  "adminkey": "admin_key_here",
  "inkey": "invoice_key_here",
  "balance_msat": 0
}
```

### Get Wallet Details

Retrieve wallet information and current balance.

```http
GET /api/v1/lightning/wallet/details
Authorization: Bearer <token>
```

**Response:**

```json
{
  "id": "wallet123abc",
  "name": "John's Lightning Wallet",
  "balance": 500000
}
```

Note: Balance is in **millisatoshis** (msat). 1 satoshi = 1,000 millisatoshis.

### Create Invoice

Generate a Lightning invoice (payment request).

```http
POST /api/v1/lightning/invoice/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 1000,
  "memo": "Payment for service",
  "unit": "sat",
  "expiry": 3600,
  "webhook": "https://your-app.com/webhook"
}
```

**Response:**

```json
{
  "payment_hash": "0123456789abcdef...",
  "payment_request": "lnbc10u1p3...",
  "checking_id": "check123",
  "lnurl_response": null
}
```

The `payment_request` is the BOLT11 invoice that can be paid by any Lightning wallet.

### Check Invoice Status

Monitor payment status of an invoice.

```http
POST /api/v1/lightning/invoice/check
Authorization: Bearer <token>
Content-Type: application/json

{
  "payment_hash": "0123456789abcdef..."
}
```

**Response:**

```json
{
  "checking_id": "check123",
  "pending": false,
  "amount": 1000000,
  "fee": 0,
  "memo": "Payment for service",
  "time": 1637683200,
  "bolt11": "lnbc10u1p3...",
  "preimage": "preimage_proof",
  "payment_hash": "0123456789abcdef...",
  "expiry": 1637686800,
  "wallet_id": "wallet123abc",
  "webhook": "https://your-app.com/webhook",
  "webhook_status": 200
}
```

Key fields:
- `pending`: `false` means payment is complete
- `preimage`: Proof of payment (only present when paid)
- `amount`: Amount in millisatoshis

### Decode Invoice

Decode a BOLT11 invoice to see details before paying.

```http
POST /api/v1/lightning/invoice/decode
Authorization: Bearer <token>
Content-Type: application/json

{
  "payment_request": "lnbc10u1p3..."
}
```

**Response:**

```json
{
  "payment_hash": "0123456789abcdef...",
  "amount_msat": 1000000,
  "description": "Payment for service",
  "payee": "03abc...def",
  "date": 1637683200,
  "expiry": 3600
}
```

### Pay Invoice

Pay a Lightning invoice.

```http
POST /api/v1/lightning/payment/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "bolt11": "lnbc10u1p3...",
  "out": true
}
```

**Response:** Same as check invoice status, with payment details.

### Get Balance

Get current wallet balance.

```http
GET /api/v1/lightning/balance
Authorization: Bearer <token>
```

**Response:**

```json
{
  "balance": 500000,
  "currency": "msat"
}
```

## Bot Features

Base path: `/api/v1/bot`

These endpoints provide bot-specific functionality for the bitbot integration.

### Magic Links (Cheques)

Create claimable Bitcoin "cheques" that can be shared via links.

#### Create Magic Link

```http
POST /api/v1/bot/magic-link/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 1000,
  "memo": "Gift for Bob",
  "expiry_hours": 24
}
```

**Response:**

```json
{
  "link_id": "abc123def456",
  "magic_link": "/api/v1/bot/magic-link/claim/abc123def456",
  "amount": 1000,
  "memo": "Gift for Bob",
  "expires_at": "2025-11-25T04:36:45Z",
  "created_at": "2025-11-24T04:36:45Z"
}
```

#### Claim Magic Link

```http
POST /api/v1/bot/magic-link/claim/{link_id}
Authorization: Bearer <token>
```

**Response:**

```json
{
  "success": true,
  "amount": 1000,
  "payment_hash": "0123456789abcdef..."
}
```

**Notes:**
- Links expire after the specified hours (default 24h)
- Users cannot claim their own links
- Links can only be claimed once

### Faucet

Allow users to claim small amounts periodically for testing/playing.

```http
POST /api/v1/bot/faucet/claim
Authorization: Bearer <token>
```

**Response:**

```json
{
  "success": true,
  "amount": 100,
  "next_claim_at": "2025-11-25T04:36:45Z"
}
```

**Notes:**
- Rate limited to once per 24 hours per user
- Fixed amount of 100 sats per claim
- Returns 429 if claimed too recently

### Internal Transfers

Transfer sats between platform users without Lightning invoices.

```http
POST /api/v1/bot/transfer/internal
Authorization: Bearer <token>
Content-Type: application/json

{
  "recipient_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 1000,
  "memo": "Thanks for the help!",
  "pin": "1234"
}
```

**Response:**

```json
{
  "success": true,
  "amount": 1000,
  "fee": 0,
  "payment_hash": "0123456789abcdef..."
}
```

**Notes:**
- No fees for internal transfers
- Instant transfer between wallets
- PIN required if user has enabled withdrawal protection
- Cannot transfer to yourself

### Withdrawal PIN

Set a PIN to protect withdrawals and transfers.

#### Set PIN

```http
POST /api/v1/bot/withdrawal/pin/set
Authorization: Bearer <token>
Content-Type: application/json

{
  "pin": "1234"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Withdrawal PIN set successfully"
}
```

#### Verify PIN

```http
POST /api/v1/bot/withdrawal/pin/verify
Authorization: Bearer <token>
Content-Type: application/json

{
  "pin": "1234"
}
```

**Response:**

```json
{
  "success": true,
  "message": "PIN verified successfully"
}
```

#### Remove PIN

```http
DELETE /api/v1/bot/withdrawal/pin
Authorization: Bearer <token>
```

**Response:**

```json
{
  "success": true,
  "message": "Withdrawal PIN removed successfully"
}
```

## Integration with bitbot

The bitbot (https://github.com/praiseunite/bitbot) should connect exclusively via these API endpoints. No direct database or LNbits access is needed.

### Typical Bot Flow

1. **User Registration**: When a user first interacts with the bot, create a Lightning wallet:
   ```
   POST /api/v1/lightning/wallet/create
   ```

2. **Receiving Payment**: Generate an invoice for the user to pay:
   ```
   POST /api/v1/lightning/invoice/create
   ```

3. **Payment Monitoring**: Poll for payment status:
   ```
   POST /api/v1/lightning/invoice/check
   ```

4. **Sending Payment**: To pay a user's invoice or withdraw:
   ```
   POST /api/v1/lightning/payment/send
   ```

5. **Balance Check**: Show user their balance:
   ```
   GET /api/v1/lightning/balance
   ```

6. **Internal Transfers**: For user-to-user tips/transfers:
   ```
   POST /api/v1/bot/transfer/internal
   ```

### Bot Configuration

The bot should store:
- Backend API URL
- User authentication tokens (from login endpoint)
- User's Lightning wallet IDs (from wallet creation)

## Examples

### Python Example: Create Invoice and Monitor

```python
import httpx
import asyncio

async def create_and_monitor_invoice():
    base_url = "https://api.yourdomain.com/api/v1"
    token = "your-jwt-token"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # Create invoice
        invoice_response = await client.post(
            f"{base_url}/lightning/invoice/create",
            json={
                "amount": 1000,
                "memo": "Test payment",
                "unit": "sat"
            },
            headers=headers
        )
        invoice_data = invoice_response.json()
        payment_hash = invoice_data["payment_hash"]
        
        print(f"Invoice: {invoice_data['payment_request']}")
        
        # Monitor payment
        while True:
            status_response = await client.post(
                f"{base_url}/lightning/invoice/check",
                json={"payment_hash": payment_hash},
                headers=headers
            )
            status_data = status_response.json()
            
            if not status_data["pending"]:
                print("Payment received!")
                print(f"Preimage: {status_data['preimage']}")
                break
            
            await asyncio.sleep(2)  # Check every 2 seconds

asyncio.run(create_and_monitor_invoice())
```

### JavaScript Example: Create Magic Link

```javascript
const createMagicLink = async () => {
  const response = await fetch('https://api.yourdomain.com/api/v1/bot/magic-link/create', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer your-jwt-token',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      amount: 1000,
      memo: 'Gift!',
      expiry_hours: 24
    })
  });
  
  const data = await response.json();
  console.log(`Share this link: ${data.magic_link}`);
  return data;
};
```

### cURL Example: Internal Transfer

```bash
curl -X POST https://api.yourdomain.com/api/v1/bot/transfer/internal \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": 1000,
    "memo": "Thanks!",
    "pin": "1234"
  }'
```

## Error Handling

All endpoints return standardized errors:

### Common Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| 400 | BAD_REQUEST | Invalid request data |
| 401 | UNAUTHORIZED | Missing or invalid authentication |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found (e.g., magic link) |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests (e.g., faucet) |
| 502 | BAD_GATEWAY | LNbits API error |

### Example Error Response

```json
{
  "error": {
    "code": "BAD_GATEWAY",
    "message": "Invoice creation failed: Insufficient balance",
    "status": 502,
    "path": "/api/v1/lightning/invoice/create"
  }
}
```

### Handling LNbits Errors

When LNbits returns an error, the backend wraps it with context:

```json
{
  "error": {
    "code": "BAD_GATEWAY",
    "message": "LNbits API error: Wallet not found",
    "status": 502
  }
}
```

Common LNbits errors:
- **Insufficient balance**: Not enough sats to create invoice/payment
- **Invalid invoice**: BOLT11 invoice is malformed or expired
- **Wallet not found**: Invalid wallet ID or API key

## Best Practices

1. **Always check invoice status**: Don't assume payment is complete without checking
2. **Handle expiry**: Invoices expire (default 1 hour), generate new ones if needed
3. **Store payment hashes**: Keep track of payment hashes for verification
4. **Use webhooks**: Configure webhooks for real-time payment notifications
5. **Rate limiting**: Implement exponential backoff for status checks
6. **Error recovery**: Gracefully handle temporary LNbits outages
7. **Security**: Never share admin keys, use environment variables
8. **Testing**: Use test mode or small amounts for development
9. **PIN protection**: Encourage users to set PINs for large balances
10. **Balance checks**: Verify balance before attempting payments

## Migration from Direct LNbits

If you're migrating from direct LNbits integration:

1. **Replace LNbits client**: Use backend API endpoints instead
2. **Authentication**: Use backend JWT tokens instead of LNbits API keys
3. **Wallet management**: Backend handles wallet creation/storage
4. **Error handling**: Adapt to backend's error format
5. **Features**: Leverage bot-specific features (magic links, faucet, etc.)

### Before (Direct LNbits):

```python
from lnbits import LNbitsClient

client = LNbitsClient(api_key="...")
invoice = client.create_invoice(amount=1000)
```

### After (Backend API):

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://api.yourdomain.com/api/v1/lightning/invoice/create",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 1000, "unit": "sat"}
    )
    invoice = response.json()
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/praiseunite/amani-backend/issues
- Documentation: See README.md and API_REFERENCE.md
- Test endpoints: Use `/docs` in development mode for interactive testing
