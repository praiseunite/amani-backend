# Installation & Running Guide

## Prerequisites
- Python 3.11 or higher
- pip package manager
- PostgreSQL database (or Supabase account)

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- FastAPI, Uvicorn (web framework and server)
- SQLAlchemy, asyncpg (database ORM and driver)
- Supabase client
- bcrypt, python-jose (security)
- pydantic, python-dotenv (configuration)
- python-json-logger (structured logging)
- And more...

### 2. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and update these required variables:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - DATABASE_URL (your PostgreSQL connection string)
```

#### Database URL Format
```
postgresql+asyncpg://username:password@host:port/database_name

# Example:
postgresql+asyncpg://postgres:mypassword@localhost:5432/amani_escrow
```

#### For Supabase
```
postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

### 3. Run the Application

Option A - Using the run script:
```bash
python run.py
```

Option B - Using uvicorn directly:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Option C - For production (with multiple workers):
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Verify Installation

Once the server is running, visit:
- **API Root**: http://localhost:8000/api/v1/
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

You should see a "Hello World" message from the API!

## Testing the API

### Using curl
```bash
# Hello World endpoint
curl http://localhost:8000/api/v1/

# Health check
curl http://localhost:8000/api/v1/health

# Ping
curl http://localhost:8000/api/v1/ping
```

### Using Python
```python
import requests

response = requests.get("http://localhost:8000/api/v1/")
print(response.json())
# Output: {"message": "Hello World! Welcome to Amani Escrow Backend", ...}
```

### Using Browser
Simply open http://localhost:8000/docs in your browser to access the interactive API documentation (Swagger UI).

## Troubleshooting

### Import Errors
If you get import errors, make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database Connection Error
1. Check your DATABASE_URL in .env
2. Ensure PostgreSQL is running
3. Verify database credentials
4. Test connection manually:
```bash
psql postgresql://username:password@host:port/database
```

### Port Already in Use
If port 8000 is in use, change it in .env:
```
PORT=8001
```

### Environment Variables Not Loading
Make sure:
1. .env file exists in the project root
2. .env file has correct format (KEY=VALUE)
3. No spaces around the = sign
4. Restart the application after changes

## Development Workflow

1. **Make code changes**
2. **Application auto-reloads** (when using --reload flag)
3. **Check logs** in console and `logs/app.log`
4. **Test endpoints** via /docs or curl
5. **Commit changes**

## Production Deployment

1. Set environment variables:
   - `ENVIRONMENT=production`
   - `DEBUG=False`
   - `FORCE_HTTPS=True`

2. Use production-grade server:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. Set up reverse proxy (nginx, traefik, etc.)

4. Enable HTTPS with SSL certificate

5. Configure monitoring and logging

## Next Steps After Installation

1. ✅ Verify the API is running
2. ✅ Check health endpoint responds
3. ✅ Review API documentation at /docs
4. 📝 Define database models in `app/models/`
5. 📝 Create API routes in `app/routes/`
6. 📝 Implement business logic
7. 📝 Add authentication endpoints
8. 📝 Set up database migrations with Alembic
9. 📝 Write tests
10. 📝 Deploy to production

---

**Ready to start development!** 🚀
