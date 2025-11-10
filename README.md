# Amani Escrow Backend

A secure, high-performance FastAPI backend for the Amani escrow platform with FinCra payment integration.

## Features

- 🚀 **FastAPI Framework**: High-performance async API with automatic OpenAPI documentation
- 🔒 **Security First**: HTTPS enforcement, security headers, structured logging for audits
- 🔐 **Authentication System**: JWT tokens, password hashing, Supabase Auth integration, role-based access control
- 📊 **PostgreSQL/Supabase**: Async SQLAlchemy integration with connection pooling
- 📝 **Structured Logging**: JSON-formatted logs for easy parsing and audit trails
- 🌐 **CORS Configured**: Cross-origin resource sharing support
- ⚡ **Async Support**: Built for high concurrency and scalability
- 💳 **FinCra Integration**: Ready for payment processing integration

## Project Structure

```
amani-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # Database connection and session management
│   │   ├── logging.py       # Structured logging setup
│   │   └── security.py      # Security middleware and utilities
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

- **HTTPS Enforcement**: Automatic redirect to HTTPS in production
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS
- **CORS Protection**: Configurable allowed origins
- **Trusted Host Middleware**: Prevents host header attacks
- **Structured Logging**: All requests and responses logged for audit
- **Password Hashing**: bcrypt for secure password storage
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

## Next Steps

1. ✅ ~~Define database models in `app/models/`~~
2. ✅ ~~Set up database migrations with Alembic~~
3. ✅ ~~Implement authentication and authorization~~
4. Create Pydantic schemas in `app/schemas/`
5. Implement CRUD operations in `app/crud/`
6. Implement business logic routes in `app/routes/`
7. Integrate FinCra payment APIs
8. Add comprehensive tests
9. Configure CI/CD pipeline

## License

Copyright © 2024 Amani Platform. All rights reserved.
