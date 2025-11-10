# Security Features Documentation

This document describes the security hardening features implemented in the Amani Escrow Backend.

## Table of Contents

1. [HTTPS Enforcement](#https-enforcement)
2. [CORS Configuration](#cors-configuration)
3. [Rate Limiting](#rate-limiting)
4. [Input Validation](#input-validation)
5. [Audit Trails](#audit-trails)
6. [Security Headers](#security-headers)
7. [API Versioning](#api-versioning)
8. [Error Handling](#error-handling)
9. [Logging](#logging)

---

## HTTPS Enforcement

The application enforces HTTPS connections in production environments.

### Configuration

Set in `.env`:
```env
FORCE_HTTPS=True
ENVIRONMENT=production
```

### Features

- Automatic HTTP to HTTPS redirection in production
- Support for X-Forwarded-Proto header (for reverse proxies)
- 307 Temporary Redirect status code for proper HTTP method preservation

### Implementation

The `HTTPSRedirectMiddleware` class in `app/core/security.py` handles HTTPS enforcement.

---

## CORS Configuration

Cross-Origin Resource Sharing (CORS) is properly configured to allow requests from trusted origins.

### Configuration

Set allowed origins in `.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000,https://app.amani.com,https://www.amani.com
```

### Features

- Whitelist of allowed origins
- Support for credentials
- Configurable allowed methods and headers

---

## Rate Limiting

The application implements rate limiting to prevent abuse and protect against DDoS attacks.

### Configuration

Set in `.env`:
```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=100

# Optional: Redis for distributed rate limiting
REDIS_ENABLED=True
REDIS_URL=redis://localhost:6379/0
```

### Features

- **Token Bucket Algorithm**: Fair and flexible rate limiting
- **Redis Support**: Distributed rate limiting across multiple instances
- **In-Memory Fallback**: Automatic fallback if Redis is unavailable
- **Per-Client Tracking**: Rate limits tracked by IP address
- **Exempt Paths**: Health check and documentation endpoints are exempt
- **Rate Limit Headers**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

### Usage

Rate limiting is automatically applied to all non-exempt endpoints. Clients exceeding the limit receive a 429 Too Many Requests response.

### Implementation

- `RateLimiter`: In-memory token bucket implementation
- `RedisRateLimiter`: Redis-based token bucket implementation
- `RateLimitMiddleware`: FastAPI middleware for rate limiting

---

## Input Validation

Advanced input validation protects against various injection attacks and ensures data integrity.

### Features

#### Security Validations

- **SQL Injection Prevention**: Detects and blocks SQL keywords in user input
- **XSS Prevention**: Detects and blocks script tags and JavaScript
- **Path Traversal Prevention**: Blocks directory traversal attempts
- **HTML Escaping**: Automatic HTML entity encoding

#### Data Validations

- **Name Validation**: Letters, spaces, hyphens, apostrophes only
- **Phone Number Validation**: International format validation
- **Slug Validation**: URL-safe strings
- **Amount Validation**: Currency amounts with decimal precision
- **List Input Validation**: Validates lists with size and content checks

### Usage

```python
from app.core.validation import InputValidator, create_string_validator
from pydantic import BaseModel, field_validator

class UserInput(BaseModel):
    name: str
    description: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return InputValidator.validate_name(v)
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        validator = create_string_validator(
            min_length=10,
            max_length=500,
            check_xss=True,
            check_sql_injection=True
        )
        return validator(v)
```

### Implementation

Located in `app/core/validation.py`:
- `ValidationPatterns`: Common regex patterns for validation
- `InputValidator`: Static methods for various validation types
- `create_string_validator`: Factory function for custom validators

---

## Audit Trails

Comprehensive audit logging tracks sensitive operations for security and compliance.

### Features

- **Structured Logging**: JSON-formatted audit logs
- **Action Categories**: Authentication, authorization, payments, data access, security events
- **Contextual Information**: User ID, IP address, user agent, timestamps
- **Severity Levels**: INFO, WARNING, ERROR, CRITICAL

### Auditable Actions

#### Authentication
- USER_LOGIN, USER_LOGOUT, USER_REGISTER
- PASSWORD_CHANGE, PASSWORD_RESET
- EMAIL_VERIFICATION

#### Authorization
- PERMISSION_GRANTED, PERMISSION_DENIED
- ROLE_CHANGED

#### Projects & Milestones
- PROJECT_CREATED, PROJECT_UPDATED, PROJECT_DELETED
- MILESTONE_CREATED, MILESTONE_COMPLETED

#### Payments
- PAYMENT_INITIATED, PAYMENT_COMPLETED, PAYMENT_FAILED
- FUNDS_DEPOSITED, FUNDS_RELEASED, FUNDS_REFUNDED

#### Security
- RATE_LIMIT_EXCEEDED, UNAUTHORIZED_ACCESS
- SUSPICIOUS_ACTIVITY

#### Data
- DATA_EXPORTED, DATA_DELETED

### Usage

```python
from app.core.audit import AuditLogger, AuditAction, audit_log

# Authentication audit
AuditLogger.log_authentication(
    action=AuditAction.USER_LOGIN,
    user_id=user.id,
    user_email=user.email,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    success=True
)

# Payment audit
AuditLogger.log_payment(
    action=AuditAction.PAYMENT_INITIATED,
    user_id=user.id,
    user_email=user.email,
    amount=100.50,
    currency="USD",
    transaction_id="txn_123",
    ip_address=request.client.host,
    success=True
)

# Quick audit logging
audit_log(
    action=AuditAction.PROJECT_CREATED,
    user_id=user.id,
    user_email=user.email,
    resource_id=project.id
)
```

### Implementation

Located in `app/core/audit.py`:
- `AuditAction`: Enumeration of auditable actions
- `AuditLevel`: Severity levels
- `AuditLogger`: Centralized audit logging
- `audit_log`: Convenience function

---

## Security Headers

Security headers are automatically added to all responses.

### Headers

- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
- **X-Frame-Options**: `DENY` - Prevents clickjacking
- **X-XSS-Protection**: `1; mode=block` - Enables XSS filtering
- **Strict-Transport-Security**: `max-age=31536000; includeSubDomains` - Forces HTTPS

### Implementation

Handled by `HTTPSRedirectMiddleware` in `app/core/security.py`.

---

## API Versioning

All API endpoints are versioned to support backward compatibility.

### Current Version

All endpoints are prefixed with `/api/v1/`.

### Examples

- `/api/v1/health` - Health check endpoint
- `/api/v1/auth/signup` - User registration
- `/api/v1/projects` - Project management

### Future Versions

When breaking changes are needed, a new version (e.g., `/api/v2/`) can be introduced while maintaining the old version for backward compatibility.

---

## Error Handling

Custom exception handlers provide consistent, secure error responses.

### Features

- **Standardized Format**: All errors follow the same JSON structure
- **Security**: Internal error details are not exposed to clients
- **Logging**: All errors are logged with context
- **HTTP Status Codes**: Proper status codes for different error types

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400,
    "details": {
      "additional": "context"
    },
    "path": "/api/v1/endpoint"
  }
}
```

### Custom Exception Classes

- `BadRequestError` (400)
- `UnauthorizedError` (401)
- `ForbiddenError` (403)
- `NotFoundError` (404)
- `ConflictError` (409)
- `ValidationErrorException` (422)
- `RateLimitError` (429)
- `ServiceUnavailableError` (503)

### Usage

```python
from app.core.exceptions import NotFoundError, BadRequestError

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = await get_project_by_id(project_id)
    if not project:
        raise NotFoundError(f"Project {project_id} not found")
    return project
```

### Implementation

Located in `app/core/exceptions.py`:
- Custom exception classes
- Exception handlers
- Error response formatting

---

## Logging

Structured logging provides comprehensive observability and audit trails.

### Configuration

Set in `.env`:
```env
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Features

- **Structured JSON Logging**: Machine-readable log format
- **Multiple Outputs**: Console and file logging
- **Context**: Rich contextual information (request, user, etc.)
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Log Format

JSON format in production:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "name": "app.routes.auth",
  "levelname": "INFO",
  "message": "User logged in successfully",
  "user_id": "uuid",
  "ip_address": "192.168.1.1"
}
```

Human-readable format in development:
```
2024-01-15 10:30:00 - app.routes.auth - INFO - User logged in successfully
```

### Implementation

Located in `app/core/logging.py`:
- `setup_logging()`: Configures logging system
- JSON formatter for production
- Simple formatter for development

---

## Security Best Practices

### For Developers

1. **Always Validate Input**: Use Pydantic schemas and validation utilities
2. **Log Security Events**: Use audit logging for sensitive operations
3. **Handle Errors Properly**: Use custom exception classes
4. **Test Security Features**: Write tests for validation and security checks
5. **Keep Dependencies Updated**: Regularly update security-sensitive packages

### For Deployment

1. **Enable HTTPS**: Always use HTTPS in production
2. **Configure Redis**: Use Redis for distributed rate limiting
3. **Set Strong Secrets**: Use strong, random SECRET_KEY values
4. **Configure CORS**: Only allow trusted origins
5. **Monitor Logs**: Regularly review audit logs for suspicious activity
6. **Rate Limit Configuration**: Adjust rate limits based on usage patterns

---

## Testing

All security features have comprehensive test coverage.

### Running Tests

```bash
# Run all security tests
pytest tests/test_audit.py tests/test_validation.py tests/test_exceptions.py -v

# Run all tests
pytest tests/ -v
```

### Test Files

- `tests/test_audit.py` - Audit logging tests
- `tests/test_validation.py` - Input validation tests
- `tests/test_exceptions.py` - Exception handling tests
- `tests/test_rate_limiter.py` - Rate limiting tests

---

## Troubleshooting

### Redis Connection Issues

If Redis is unavailable, the system automatically falls back to in-memory rate limiting:

```
WARNING - Failed to connect to Redis: Connection refused. Falling back to in-memory rate limiting.
```

To resolve:
1. Check Redis is running: `redis-cli ping`
2. Verify `REDIS_URL` in `.env`
3. Check network connectivity

### Rate Limit Exceeded

Users receiving 429 errors should:
1. Check the `Retry-After` header
2. Implement exponential backoff
3. Contact support if legitimate traffic is being blocked

### Validation Errors

422 Validation Error responses include detailed error information:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": {
      "errors": [
        {
          "field": "email",
          "message": "value is not a valid email address",
          "type": "value_error.email"
        }
      ]
    }
  }
}
```

---

## Additional Resources

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Redis Rate Limiting](https://redis.io/topics/rate-limiting)
