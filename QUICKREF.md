# Developer Quick Reference

Quick commands for common development tasks.

## Setup

```bash
# Clone and setup
git clone https://github.com/praiseunite/amani-backend.git
cd amani-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

## Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Docker
docker-compose up -d

# View logs
docker-compose logs -f app
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validation.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run and open coverage report
pytest --cov=app --cov-report=html && open htmlcov/index.html
```

## Code Quality

```bash
# Format code with Black
black app/ tests/

# Check formatting without changes
black --check app/ tests/

# Run linting
flake8 app/ tests/

# Run all quality checks
black --check app/ tests/ && flake8 app/ tests/ && pytest
```

## Database

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Downgrade migration
alembic downgrade -1

# Check current version
alembic current
```

## Docker

```bash
# Build image
docker build -t amani-backend:local .

# Run container
docker run -p 8000:8000 --env-file .env amani-backend:local

# Docker Compose - start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Add and commit changes
git add .
git commit -m "Description of changes"

# Push to remote
git push origin feature/your-feature-name

# Update from main
git checkout main
git pull
git checkout feature/your-feature-name
git merge main
```

## API Documentation

- Local development: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/v1/health

## Useful Commands

```bash
# Check Python version
python --version

# List installed packages
pip list

# Check for outdated packages
pip list --outdated

# Generate requirements.txt
pip freeze > requirements.txt

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Clean test artifacts
rm -rf .pytest_cache htmlcov .coverage coverage.xml
```

## Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
ENVIRONMENT=development  # or production, testing
DEBUG=true  # or false for production
```

## Troubleshooting

### Tests failing with import errors
```bash
# Ensure you're in the project root and have dependencies installed
pip install -r requirements.txt -r requirements-dev.txt
```

### Database connection errors
```bash
# Check DATABASE_URL in .env
# Ensure database is running
# Test connection manually
```

### Docker build fails
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t amani-backend:local .
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

## CI/CD

The CI/CD pipeline runs automatically on push:
- Linting (Black, Flake8)
- Testing (pytest with coverage)
- Docker build verification
- Deployment to Docker registry (main branch only)

See [CI_CD.md](CI_CD.md) for detailed documentation.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
