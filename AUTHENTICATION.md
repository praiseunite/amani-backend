# Authentication System Documentation

## Overview

The Amani Backend implements a comprehensive authentication system with the following features:

- **JWT (JSON Web Token)** authentication for API access
- **Password-based authentication** with bcrypt hashing
- **Supabase Auth integration** for Magic Link (passwordless) authentication
- **Role-based access control (RBAC)** with three roles: admin, client, freelancer
- **Secure password requirements** (minimum 8 characters, uppercase, lowercase, digit)
- **Protected routes** with middleware and dependency injection

## User Roles

The system supports three user roles with different access levels:

- **Admin**: Full system access, can manage all resources
- **Client**: Can create projects, hire freelancers, manage their projects as buyers
- **Freelancer**: Can work on projects, manage their projects as sellers

## API Endpoints

### Authentication Endpoints

All authentication endpoints are prefixed with `/api/v1/auth`.

#### 1. User Signup

**Endpoint**: `POST /api/v1/auth/signup`

**Description**: Register a new user with email and password.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "Test1234",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "role": "client"
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Response**: `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "client",
    "is_active": true,
    "is_verified": false,
    ...
  }
}
```

#### 2. User Login

**Endpoint**: `POST /api/v1/auth/login`

**Description**: Authenticate user with email and password.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "Test1234"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    ...
  }
}
```

#### 3. Request Magic Link

**Endpoint**: `POST /api/v1/auth/magic-link`

**Description**: Request a passwordless magic link authentication via email (requires Supabase Auth configuration).

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response**: `200 OK`
```json
{
  "message": "Magic link sent to your email. Please check your inbox.",
  "email": "user@example.com"
}
```

**Note**: Requires `SUPABASE_URL` and `SUPABASE_KEY` environment variables to be configured.

#### 4. Get Current User

**Endpoint**: `GET /api/v1/auth/me`

**Description**: Get the current authenticated user's information.

**Headers**: 
```
Authorization: Bearer <access_token>
```

**Response**: `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "role": "client",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "avatar_url": null,
  "bio": null,
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-01T12:00:00"
}
```

#### 5. Update Profile

**Endpoint**: `PUT /api/v1/auth/me`

**Description**: Update the current user's profile information.

**Headers**: 
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "full_name": "Jane Doe",
  "phone_number": "+1234567890",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Experienced freelancer"
}
```

**Response**: `200 OK` (Updated user object)

#### 6. Change Password

**Endpoint**: `POST /api/v1/auth/change-password`

**Description**: Change the current user's password.

**Headers**: 
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword123"
}
```

**Response**: `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

## Using Authentication in Your Routes

### Protecting Routes with Authentication

To protect a route and require authentication, use the `get_current_active_user` dependency:

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_active_user)
):
    return {"message": f"Hello {current_user.email}"}
```

### Role-Based Access Control

#### Using Pre-defined Role Dependencies

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin, require_client, require_freelancer
from app.models.user import User

router = APIRouter()

@router.get("/admin-only")
async def admin_only_route(
    current_user: User = Depends(require_admin)
):
    return {"message": "Admin access granted"}

@router.get("/client-only")
async def client_only_route(
    current_user: User = Depends(require_client)
):
    return {"message": "Client access granted"}

@router.get("/freelancer-only")
async def freelancer_only_route(
    current_user: User = Depends(require_freelancer)
):
    return {"message": "Freelancer access granted"}
```

#### Using Custom Role Requirements

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import require_role
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/client-or-freelancer")
async def mixed_access_route(
    current_user: User = Depends(require_role([UserRole.CLIENT, UserRole.FREELANCER]))
):
    return {"message": "Access granted to clients and freelancers"}
```

## Environment Configuration

Add these environment variables to your `.env` file:

```bash
# JWT Settings
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Supabase Auth (for Magic Links)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
```

**Important Security Notes**:
- Generate a strong, random `SECRET_KEY` for production (use `openssl rand -hex 32`)
- Never commit your `.env` file to version control
- Keep your Supabase keys secure

## Database Migration

The authentication system adds a `role` field to the users table. Run the migration:

```bash
alembic upgrade head
```

This will:
1. Create the `userrole` enum type with values: admin, client, freelancer
2. Add the `role` column to the `users` table with default value 'client'

## Testing

Unit tests for authentication utilities are available in `tests/test_auth_utils.py`.

Run tests:
```bash
# Set required environment variables
export SECRET_KEY="test-secret-key"
export DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test"

# Run tests
pytest tests/test_auth_utils.py -v
```

## Security Features

### Password Security
- **bcrypt hashing**: Industry-standard password hashing with automatic salt
- **Password strength validation**: Enforces strong passwords
- **No plaintext storage**: Passwords are never stored in plaintext

### JWT Security
- **Token expiration**: Tokens expire after 30 minutes (configurable)
- **Signature verification**: All tokens are cryptographically signed
- **Role-based claims**: User role is encoded in the token

### API Security
- **HTTPS enforcement**: Automatic redirect to HTTPS in production
- **Security headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS
- **Bearer token authentication**: Standard HTTP Bearer authentication scheme
- **Role-based authorization**: Fine-grained access control

## Examples

### Complete Authentication Flow

```python
import httpx

# 1. Sign up a new user
signup_response = httpx.post(
    "http://localhost:8000/api/v1/auth/signup",
    json={
        "email": "user@example.com",
        "password": "Test1234",
        "full_name": "John Doe",
        "role": "client"
    }
)
token = signup_response.json()["access_token"]

# 2. Access protected endpoint
headers = {"Authorization": f"Bearer {token}"}
profile_response = httpx.get(
    "http://localhost:8000/api/v1/auth/me",
    headers=headers
)
user = profile_response.json()

# 3. Update profile
update_response = httpx.put(
    "http://localhost:8000/api/v1/auth/me",
    headers=headers,
    json={
        "full_name": "Jane Doe",
        "bio": "Updated bio"
    }
)

# 4. Change password
password_response = httpx.post(
    "http://localhost:8000/api/v1/auth/change-password",
    headers=headers,
    json={
        "current_password": "Test1234",
        "new_password": "NewTest1234"
    }
)
```

### Using Magic Links

```python
import httpx

# Request magic link
response = httpx.post(
    "http://localhost:8000/api/v1/auth/magic-link",
    json={"email": "user@example.com"}
)

# User receives email and clicks link
# Link contains token that can be verified via Supabase Auth
# After verification, create JWT token for API access
```

## Troubleshooting

### Common Issues

#### 1. "Could not validate credentials"
- Token may be expired (tokens expire after 30 minutes)
- Token may be invalid or tampered with
- Check that you're sending the token in the Authorization header

#### 2. "Access denied. Required roles: [...]"
- User doesn't have the required role
- Check the user's role in the database
- Admins can modify user roles if needed

#### 3. "Magic link authentication is not available"
- Supabase credentials not configured
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Magic links are optional; use password authentication instead

#### 4. "Email already registered"
- User with this email already exists
- Use login endpoint instead of signup
- Or use password reset if user forgot password

## Next Steps

- Implement password reset functionality
- Add email verification flow
- Set up refresh tokens for longer sessions
- Add OAuth providers (Google, GitHub, etc.)
- Implement two-factor authentication (2FA)
- Add rate limiting to prevent brute force attacks
