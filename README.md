# Amani Escrow Backend

A secure, high-performance FastAPI backend for the Amani escrow platform with FinCra payment integration.

## Features

- 🚀 **FastAPI Framework**: High-performance async API with automatic OpenAPI documentation
- 🔒 **Security First**: HTTPS enforcement, security headers, comprehensive audit trails
- 🛡️ **Rate Limiting**: Redis-based distributed rate limiting with automatic fallback
- ✅ **Input Validation**: Advanced validation with XSS, SQL injection, and path traversal protection
- 🔐 **Authentication System**: JWT tokens, password hashing, Supabase Auth integration, role-based access control
- 📊 **PostgreSQL/Supabase**: Async SQLAlchemy integration with connection pooling
- 📝 **Structured Logging**: JSON-formatted logs for easy parsing and audit trails
- 🌐 **CORS Configured**: Cross-origin resource sharing support
- 🚨 **Error Handling**: Custom exception handlers with standardized error responses
- ⚡ **Async Support**: Built for high concurrency and scalability
- 💳 **FinCra Integration**: Ready for payment processing integration
- 🔄 **API Versioning**: Versioned API endpoints for backward compatibility

## Project Structure

```
amani-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── audit.py       # Audit trail system
│   │   ├── auth.py        # Authentication utilities
│   │   ├── config.py      # Environment configuration
│   │   ├── database.py    # Database connection and session management
│   │   ├── exceptions.py  # Custom exception handlers
│   │   ├── logging.py     # Structured logging setup
│   │   ├── rate_limit.py  # Rate limiting middleware
│   │   ├── security.py    # Security middleware and utilities
│   │   └── validation.py  # Input validation utilities
│   ├── models/              # SQLAlchemy models
│   │   └── __init__.py
│   ├── routes/              # API route handlers
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoints
│   └── schemas/             # Pydantic schemas
│       └── __init__.py
├── logs/                    # Application logs (auto-created)
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Example environment configuration
├── .gitignore              # Git ignore file
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database (or Supabase account)
- pip package manager

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/praiseunite/amani-backend.git
   cd amani-backend
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and update with your actual credentials
   ```

5. **Run the application**

   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or use the built-in run command:

   ```bash
   python app/main.py
   ```

6. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Hello World: http://localhost:8000/api/v1/
   - Health Check: http://localhost:8000/api/v1/health

## Environment Configuration

Copy `.env.example` to `.env` and configure the following:

### Required Variables

- `SECRET_KEY`: Secret key for JWT tokens (generate a secure random string)
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql+asyncpg://user:pass@host:port/db`)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anonymous key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key

### Optional Variables

- `FINCRA_API_KEY`: FinCra API key for payment integration
- `FINCRA_API_SECRET`: FinCra API secret
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `FORCE_HTTPS`: Enable HTTPS enforcement in production

### Rate Limiting Configuration

- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting (default: True)
- `RATE_LIMIT_PER_MINUTE`: Maximum requests per minute (default: 60)
- `RATE_LIMIT_BURST_SIZE`: Maximum burst size (default: 100)

### Redis Configuration (Optional)

- `REDIS_ENABLED`: Enable Redis for distributed rate limiting (default: False)
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)

## API Endpoints

### Health & Status

- `GET /api/v1/` - Hello World endpoint
- `GET /api/v1/health` - Health check with timestamp
- `GET /api/v1/ping` - Simple ping/pong

### Authentication

- `POST /api/v1/auth/signup` - Register a new user
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/magic-link` - Request magic link (passwordless auth)
- `GET /api/v1/auth/me` - Get current user info
- `PUT /api/v1/auth/me` - Update user profile
- `POST /api/v1/auth/change-password` - Change password

### Project Management

- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects` - List user's projects (paginated)
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete draft project

### Milestone Management

- `POST /api/v1/milestones` - Create a new milestone
- `GET /api/v1/milestones` - List milestones (paginated, filterable)
- `GET /api/v1/milestones/{id}` - Get milestone details
- `PUT /api/v1/milestones/{id}` - Update milestone
- `POST /api/v1/milestones/{id}/submit` - Submit milestone for approval
- `POST /api/v1/milestones/{id}/approve` - Approve or reject milestone

### Escrow & Transactions

- `POST /api/v1/escrow/hold` - Hold funds in escrow
- `POST /api/v1/escrow/release` - Release escrow funds
- `GET /api/v1/escrow/transactions` - List transactions (paginated)
- `GET /api/v1/escrow/transactions/{id}` - Get transaction details

### KYC Verification

- `POST /api/v1/kyc/submit` - Submit KYC information
- `GET /api/v1/kyc/status` - Get KYC submission status
- `POST /api/v1/kyc/resubmit/{kyc_id}` - Resubmit rejected KYC

**See [AUTHENTICATION.md](AUTHENTICATION.md) for complete authentication documentation.**

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With specific log level
uvicorn app.main:app --reload --log-level debug
```

### Running in Production

```bash
# Using Uvicorn with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Security Features

The application implements comprehensive security hardening:

- **HTTPS Enforcement**: Automatic redirect to HTTPS in production
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS
- **Rate Limiting**: Token bucket algorithm with Redis support for distributed limiting
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Advanced validation with XSS, SQL injection, and path traversal protection
- **Audit Trails**: Comprehensive logging of sensitive operations
- **Error Handling**: Secure error responses that don't leak sensitive information
- **Trusted Host Middleware**: Prevents host header attacks
- **Password Hashing**: bcrypt for secure password storage
- **JWT Authentication**: Secure token-based authentication with role-based access control

**See [SECURITY.md](SECURITY.md) for detailed security documentation.**

- **JWT Authentication**: Token-based authentication ready

## Database

The application uses async SQLAlchemy with PostgreSQL:

- **Connection Pooling**: Configured with pool_size=10, max_overflow=20
- **Async Sessions**: Full async/await support
- **Supabase Integration**: Ready for Supabase PostgreSQL
- **Migrations**: Alembic ready for database migrations

## Logging

Structured JSON logging for production with human-readable format for development:

- **Console Logging**: Formatted output to stdout
- **File Logging**: JSON logs stored in `logs/app.log`
- **Request Tracking**: All HTTP requests logged with metadata
- **Error Tracking**: Detailed error logging for debugging

## Database

The application uses async SQLAlchemy with PostgreSQL (Supabase):

- **4 Core Models**: User, Project, Milestone, Transaction
- **Async Support**: Full async/await with asyncpg
- **Connection Pooling**: Configured with pool_size=10, max_overflow=20
- **Row-Level Security**: Supabase RLS policies for data protection
- **Migrations**: Alembic for schema management
- **Relationships**: Fully mapped with foreign keys and cascade operations

**See [DATABASE_SETUP.md](DATABASE_SETUP.md) for complete setup guide.**

## CI/CD Pipeline

The project includes a complete CI/CD pipeline with GitHub Actions:

- **Automated Testing**: pytest with coverage reporting
- **Code Quality**: Black formatting and Flake8 linting
- **Docker Build**: Automated image builds and deployment
- **Continuous Deployment**: Automatic deployment to Docker registry

**See [CI_CD.md](CI_CD.md) for complete CI/CD documentation.**

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
```

## Next Steps

1. ✅ ~~Define database models in `app/models/`~~
2. ✅ ~~Set up database migrations with Alembic~~
3. ✅ ~~Implement authentication and authorization~~
4. ✅ ~~Create Pydantic schemas in `app/schemas/`~~
5. ✅ ~~Implement CRUD operations in `app/crud/`~~
6. ✅ ~~Implement business logic routes in `app/routes/`~~
7. ✅ ~~Configure CI/CD pipeline~~
8. Integrate FinCra payment APIs
9. Add comprehensive end-to-end tests

## License

Copyright © 2024 Amani Platform. All rights reserved.
