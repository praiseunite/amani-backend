# API Documentation

Complete API reference for Amani Escrow Backend with request/response examples.

## Table of Contents
- [Authentication](#authentication)
- [Health & Status](#health--status)
- [User Management](#user-management)
- [Projects](#projects)
- [Milestones](#milestones)
- [Escrow & Transactions](#escrow--transactions)
- [KYC Verification](#kyc-verification)
- [Wallet Operations](#wallet-operations)
- [Lightning Network](#lightning-network)
- [Bot Features](#bot-features)
- [Error Handling](#error-handling)

## Base URL

```
Development: http://localhost:8000
Production: https://api.yourdomain.com
```

All endpoints are prefixed with `/api/v1`.

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Register User

Create a new user account.

**Endpoint**: `POST /api/v1/auth/signup`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "phone_number": "+2348012345678",
  "role": "client"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone_number": "+2348012345678",
  "role": "client",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-11-22T20:00:00Z"
}
```

### Login

Authenticate and receive access token.

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "client"
  }
}
```

### Get Current User

Get authenticated user's information.

**Endpoint**: `GET /api/v1/auth/me`

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone_number": "+2348012345678",
  "role": "client",
  "is_active": true,
  "is_verified": true,
  "kyc_status": "approved",
  "created_at": "2025-11-22T20:00:00Z"
}
```

### Change Password

Update user password.

**Endpoint**: `POST /api/v1/auth/change-password`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

## Health & Status

### Root Endpoint

Basic API information.

**Endpoint**: `GET /api/v1/`

**Response** (200 OK):
```json
{
  "message": "Hello World! Welcome to Amani Escrow Backend",
  "app": "Amani Escrow Backend",
  "version": "1.0.0",
  "environment": "production"
}
```

### Health Check

Comprehensive system health check.

**Endpoint**: `GET /api/v1/health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-11-22T20:00:00Z",
  "app": "Amani Escrow Backend",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "migrations": {
      "status": "healthy",
      "message": "Migrations applied",
      "current_version": "001_initial_schema"
    }
  }
}
```

### Readiness Probe

Check if system is ready to serve traffic.

**Endpoint**: `GET /api/v1/readiness`

**Response** (200 OK):
```json
{
  "ready": true,
  "timestamp": "2025-11-22T20:00:00Z",
  "checks": {
    "database": "ready",
    "table_users": "ready",
    "table_wallet_registry": "ready",
    "table_wallet_balance_snapshot": "ready",
    "table_wallet_transaction_event": "ready"
  }
}
```

### Ping

Simple liveness check.

**Endpoint**: `GET /api/v1/ping`

**Response** (200 OK):
```json
{
  "message": "pong"
}
```

## Projects

### Create Project

Create a new escrow project.

**Endpoint**: `POST /api/v1/projects`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "title": "Website Development Project",
  "description": "Full-stack website development with payment integration",
  "amount": 500000.00,
  "currency": "NGN",
  "deadline": "2026-01-31T23:59:59Z",
  "buyer_id": "client-user-id-here",
  "seller_id": "freelancer-user-id-here"
}
```

**Response** (201 Created):
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "Website Development Project",
  "description": "Full-stack website development with payment integration",
  "amount": 500000.00,
  "currency": "NGN",
  "status": "draft",
  "deadline": "2026-01-31T23:59:59Z",
  "buyer_id": "client-user-id",
  "seller_id": "freelancer-user-id",
  "created_at": "2025-11-22T20:00:00Z",
  "updated_at": "2025-11-22T20:00:00Z"
}
```

### List Projects

Get user's projects with pagination.

**Endpoint**: `GET /api/v1/projects?page=1&limit=10&status=active`

**Headers**:
```
Authorization: Bearer <token>
```

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10, max: 100)
- `status` (optional): Filter by status (draft, active, completed, etc.)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "650e8400-e29b-41d4-a716-446655440000",
      "title": "Website Development Project",
      "amount": 500000.00,
      "currency": "NGN",
      "status": "active",
      "created_at": "2025-11-22T20:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10,
  "pages": 1
}
```

### Get Project Details

Get detailed project information.

**Endpoint**: `GET /api/v1/projects/{project_id}`

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "Website Development Project",
  "description": "Full-stack website development with payment integration",
  "amount": 500000.00,
  "currency": "NGN",
  "status": "active",
  "deadline": "2026-01-31T23:59:59Z",
  "buyer": {
    "id": "buyer-id",
    "full_name": "John Client",
    "email": "client@example.com"
  },
  "seller": {
    "id": "seller-id",
    "full_name": "Jane Developer",
    "email": "developer@example.com"
  },
  "milestones": [
    {
      "id": "milestone-id",
      "title": "Phase 1: Design",
      "amount": 150000.00,
      "status": "completed"
    }
  ],
  "created_at": "2025-11-22T20:00:00Z",
  "updated_at": "2025-11-22T20:00:00Z"
}
```

## KYC Verification

### Submit KYC

Submit KYC information for verification.

**Endpoint**: `POST /api/v1/kyc/submit`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "kyc_type": "kyc",
  "nin": "12345678901",
  "bvn": "22234567890",
  "date_of_birth": "1990-01-15",
  "address": "123 Main Street, Lagos",
  "city": "Lagos",
  "state": "Lagos",
  "country": "Nigeria",
  "security_code": "123456"
}
```

**Response** (201 Created):
```json
{
  "id": "kyc-id-here",
  "user_id": "user-id",
  "kyc_type": "kyc",
  "status": "pending",
  "submitted_at": "2025-11-22T20:00:00Z",
  "message": "KYC submitted successfully. Your submission is under review."
}
```

### Check KYC Status

Get KYC verification status.

**Endpoint**: `GET /api/v1/kyc/status`

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "id": "kyc-id",
  "user_id": "user-id",
  "kyc_type": "kyc",
  "status": "approved",
  "submitted_at": "2025-11-22T20:00:00Z",
  "reviewed_at": "2025-11-23T10:00:00Z",
  "approval_code": "ABC123"
}
```

## Wallet Operations

### Register Wallet

Register a new wallet for a user.

**Endpoint**: `POST /api/v1/wallets/register`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "user_id": "user-id-here",
  "provider": "fincra",
  "provider_account_id": "fincra-account-id",
  "currency": "NGN",
  "account_name": "John Doe",
  "account_number": "1234567890"
}
```

**Response** (201 Created):
```json
{
  "wallet_id": "wallet-id-here",
  "user_id": "user-id",
  "provider": "fincra",
  "currency": "NGN",
  "status": "active",
  "created_at": "2025-11-22T20:00:00Z"
}
```

### Sync Wallet Balance

Synchronize wallet balance with provider.

**Endpoint**: `POST /api/v1/wallets/{wallet_id}/sync-balance`

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "wallet_id": "wallet-id",
  "balance": 50000.00,
  "currency": "NGN",
  "provider": "fincra",
  "as_of": "2025-11-22T20:00:00Z",
  "synced_at": "2025-11-22T20:00:05Z"
}
```

## Lightning Network

Lightning Network integration via LNbits for Bitcoin micropayments. See [LIGHTNING_INTEGRATION.md](LIGHTNING_INTEGRATION.md) for complete guide.

### Create Lightning Wallet

Create a new Lightning wallet for a user.

**Endpoint**: `POST /api/v1/lightning/wallet/create`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "user_name": "john_doe",
  "wallet_name": "John's Wallet"
}
```

**Response** (201 Created):
```json
{
  "id": "wallet123abc",
  "name": "John's Wallet",
  "user": "john_doe",
  "adminkey": "admin_key_here",
  "inkey": "invoice_key_here",
  "balance_msat": 0
}
```

### Create Lightning Invoice

Generate a Lightning payment request (BOLT11).

**Endpoint**: `POST /api/v1/lightning/invoice/create`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "amount": 1000,
  "memo": "Payment for service",
  "unit": "sat",
  "expiry": 3600
}
```

**Response** (201 Created):
```json
{
  "payment_hash": "0123456789abcdef...",
  "payment_request": "lnbc10u1p3...",
  "checking_id": "check123"
}
```

### Check Invoice Status

Check payment status of a Lightning invoice.

**Endpoint**: `POST /api/v1/lightning/invoice/check`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "payment_hash": "0123456789abcdef..."
}
```

**Response** (200 OK):
```json
{
  "checking_id": "check123",
  "pending": false,
  "amount": 1000000,
  "memo": "Payment for service",
  "time": 1637683200,
  "preimage": "proof_of_payment",
  "payment_hash": "0123456789abcdef..."
}
```

### Get Lightning Balance

Get current Lightning wallet balance.

**Endpoint**: `GET /api/v1/lightning/balance`

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "balance": 500000,
  "currency": "msat"
}
```

Note: Balance is in millisatoshis (msat). 1 satoshi = 1,000 millisatoshis.

## Bot Features

Special endpoints for bot integration. Designed for https://github.com/praiseunite/bitbot.

### Create Magic Link (Cheque)

Create a claimable Bitcoin cheque that can be shared via link.

**Endpoint**: `POST /api/v1/bot/magic-link/create`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "amount": 1000,
  "memo": "Gift for you!",
  "expiry_hours": 24
}
```

**Response** (201 Created):
```json
{
  "link_id": "abc123def456",
  "magic_link": "/api/v1/bot/magic-link/claim/abc123def456",
  "amount": 1000,
  "memo": "Gift for you!",
  "expires_at": "2025-11-25T04:36:45Z",
  "created_at": "2025-11-24T04:36:45Z"
}
```

### Claim Magic Link

Claim a magic link created by another user.

**Endpoint**: `POST /api/v1/bot/magic-link/claim/{link_id}`

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "success": true,
  "amount": 1000,
  "payment_hash": "0123456789abcdef..."
}
```

### Claim Faucet

Claim small amount from faucet (once per 24 hours).

**Endpoint**: `POST /api/v1/bot/faucet/claim`

**Headers**:
```
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "success": true,
  "amount": 100,
  "next_claim_at": "2025-11-25T04:36:45Z"
}
```

### Internal Transfer

Transfer sats between platform users instantly.

**Endpoint**: `POST /api/v1/bot/transfer/internal`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "recipient_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 1000,
  "memo": "Thanks!",
  "pin": "1234"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "amount": 1000,
  "fee": 0,
  "payment_hash": "0123456789abcdef..."
}
```

### Set Withdrawal PIN

Set a security PIN for withdrawals.

**Endpoint**: `POST /api/v1/bot/withdrawal/pin/set`

**Headers**:
```
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "pin": "1234"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Withdrawal PIN set successfully"
}
```

## Error Handling

All errors follow a standardized format:

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400,
    "details": {
      "field": "Additional error details",
      "errors": []
    },
    "path": "/api/v1/endpoint"
  }
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | BAD_REQUEST | Invalid request data |
| 401 | UNAUTHORIZED | Authentication required |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource conflict (duplicate) |
| 422 | VALIDATION_ERROR | Input validation failed |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |
| 503 | SERVICE_UNAVAILABLE | Service temporarily unavailable |

### Example: Validation Error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "status": 422,
    "details": {
      "errors": [
        {
          "field": "email",
          "message": "value is not a valid email address",
          "type": "value_error.email"
        },
        {
          "field": "password",
          "message": "ensure this value has at least 8 characters",
          "type": "value_error.any_str.min_length"
        }
      ]
    },
    "path": "/api/v1/auth/signup"
  }
}
```

### Example: Unauthorized Error

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token",
    "status": 401,
    "path": "/api/v1/auth/me"
  }
}
```

### Example: Rate Limit Error

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "status": 429,
    "details": {
      "retry_after": 60
    },
    "path": "/api/v1/endpoint"
  }
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse.

**Default Limits**:
- 60 requests per minute per IP
- Burst size: 100 requests

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1637683200
```

## Pagination

List endpoints support pagination with the following parameters:

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)

**Response Format**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 10,
  "pages": 10
}
```

## Filtering & Sorting

Many list endpoints support filtering and sorting:

**Example**:
```
GET /api/v1/projects?status=active&sort=created_at&order=desc
```

## Testing with cURL

### Example: Login Request

```bash
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

### Example: Authenticated Request

```bash
curl -X GET https://api.yourdomain.com/api/v1/auth/me \
  -H "Authorization: Bearer your-jwt-token-here"
```

### Example: Create Project

```bash
curl -X POST https://api.yourdomain.com/api/v1/projects \
  -H "Authorization: Bearer your-jwt-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Website Development Project",
    "description": "Full-stack website development",
    "amount": 500000.00,
    "currency": "NGN",
    "deadline": "2026-01-31T23:59:59Z"
  }'
```

## Interactive API Documentation

The API provides interactive documentation using Swagger UI and ReDoc:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all available endpoints
- View request/response schemas
- Test endpoints directly from the browser
- Generate code snippets

> **Note**: In production, API documentation is disabled by default for security. Set `DEBUG=True` to enable it in development.

## Webhooks (Coming Soon)

Webhooks will allow your application to receive real-time notifications for events such as:
- Payment completed
- Milestone approved
- KYC status changed
- Transaction failed

## Support

For API support and questions:
- GitHub Issues: https://github.com/praiseunite/amani-backend/issues
- Email: support@yourdomain.com
- Documentation: See README.md, DEPLOYMENT.md
