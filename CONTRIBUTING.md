# Contributing to Amani Escrow Backend

Thank you for considering contributing to Amani Escrow Backend! This guide will help you get started.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Security](#security)
- [Code of Conduct](#code-of-conduct)

## Getting Started

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 14+ or Supabase account
- Git
- Basic understanding of FastAPI and async Python

### First-Time Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/amani-backend.git
   cd amani-backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

4. **Setup pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local credentials
   ```

6. **Run tests to verify setup**
   ```bash
   pytest
   ```

## Development Setup

### Running the Development Server

```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
python app/main.py
```

### Database Setup

```bash
# Run migrations
alembic upgrade head

# Check migration status
alembic current

# Create a new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_auth.py

# Run tests matching pattern
pytest -k "test_user"

# Run with verbose output
pytest -v
```

## Coding Standards

### Code Formatting

We use **Black** for code formatting and **isort** for import sorting:

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Check formatting without changes
black --check app/ tests/
```

**Configuration**:
- Line length: 100 characters
- Target: Python 3.11
- Profile: black (for isort)

### Linting

We use **flake8** for linting:

```bash
# Run flake8
flake8 app/

# Check specific file
flake8 app/routes/auth.py
```

**Key Rules**:
- Max line length: 100
- Max complexity: 10
- Google-style docstrings
- No unused imports

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Run manually on all files
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

**Hooks include**:
- Black formatting
- isort import sorting
- flake8 linting
- Secret detection (detect-secrets)
- Security scanning (bandit)
- Trailing whitespace removal
- YAML/JSON validation

### Code Style Guidelines

1. **Naming Conventions**
   - Classes: `PascalCase`
   - Functions/variables: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`
   - Private members: `_leading_underscore`

2. **Docstrings**
   ```python
   def function_name(param1: str, param2: int) -> bool:
       """Brief description of function.
       
       More detailed description if needed.
       
       Args:
           param1: Description of param1
           param2: Description of param2
           
       Returns:
           Description of return value
           
       Raises:
           ValueError: When and why this is raised
       """
       pass
   ```

3. **Type Hints**
   - Always use type hints for function parameters and return values
   - Use `Optional[Type]` for nullable values
   - Use `Union[Type1, Type2]` for multiple possible types

4. **Async/Await**
   - Use `async def` for database operations
   - Use `await` for async calls
   - Don't mix sync and async without proper handling

## Testing Guidelines

### Test Coverage Target

- **Minimum**: 85% overall coverage
- **Current**: 63-64% (needs improvement)
- Focus on critical paths and business logic

### Test Organization

```
tests/
├── unit/              # Unit tests (no external dependencies)
├── integration/       # Integration tests (database, external services)
└── api/              # API endpoint tests
```

### Writing Tests

1. **Unit Tests**
   ```python
   import pytest
   from unittest.mock import AsyncMock, patch
   
   @pytest.mark.unit
   @pytest.mark.asyncio
   async def test_function_name():
       """Test description."""
       # Arrange
       mock_dependency = AsyncMock()
       
       # Act
       result = await function_under_test(mock_dependency)
       
       # Assert
       assert result == expected_value
   ```

2. **Integration Tests**
   ```python
   @pytest.mark.integration
   @pytest.mark.asyncio
   async def test_endpoint(test_client):
       """Test endpoint integration."""
       response = await test_client.get("/api/v1/endpoint")
       assert response.status_code == 200
   ```

3. **Test Naming**
   - `test_<function>_<scenario>_<expected_result>`
   - Example: `test_create_user_with_valid_data_returns_user`

4. **Test Coverage**
   - Write tests for new features
   - Write tests for bug fixes
   - Maintain or improve coverage percentage

### Running Security Scans

```bash
# Run bandit security scanner
bandit -r app/ -c pyproject.toml

# Run detect-secrets
detect-secrets scan

# Check for known vulnerabilities
pip install safety
safety check
```

## Submitting Changes

### Branch Naming

- Features: `feature/description-of-feature`
- Bug fixes: `fix/description-of-bug`
- Documentation: `docs/description-of-changes`
- Refactoring: `refactor/description-of-refactor`

### Commit Messages

Follow the conventional commits format:

```
type(scope): brief description

Detailed explanation if needed.

- Bullet points for multiple changes
- Reference issues: Fixes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(auth): add magic link authentication

Implement passwordless login using email magic links.
Includes rate limiting and expiration handling.

Closes #45
```

```
fix(wallet): resolve race condition in balance sync

Use idempotency keys and proper transaction isolation
to prevent duplicate balance snapshots.

Fixes #67
```

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow coding standards
   - Write/update tests
   - Update documentation

3. **Run checks locally**
   ```bash
   # Format code
   black app/ tests/
   isort app/ tests/
   
   # Run linters
   flake8 app/
   
   # Run tests
   pytest --cov=app
   
   # Run security scans
   bandit -r app/ -c pyproject.toml
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Use descriptive title
   - Fill in PR template
   - Link related issues
   - Request review

### PR Requirements

- [ ] Tests pass locally
- [ ] Code coverage maintained or improved
- [ ] Code formatted (Black, isort)
- [ ] Linting passes (flake8)
- [ ] Security scans pass (bandit)
- [ ] Documentation updated
- [ ] No secrets committed
- [ ] Descriptive commit messages

## Security

### Reporting Vulnerabilities

**DO NOT** create a public issue for security vulnerabilities.

Instead:
- Email security contact (see SECURITY_NOTICE.md)
- Include description, impact, and reproduction steps
- Wait for acknowledgment before public disclosure

### Security Best Practices

1. **Never commit secrets**
   - Use `.env` for local secrets
   - Use environment variables in production
   - Keep `.env.example` with placeholders only

2. **Input validation**
   - Always validate user input
   - Use Pydantic schemas for validation
   - Sanitize inputs to prevent XSS/SQL injection

3. **Authentication**
   - Use JWT tokens for authentication
   - Implement proper password hashing
   - Add rate limiting for auth endpoints

4. **Dependencies**
   - Keep dependencies updated
   - Review dependency changes
   - Run security scans regularly

See [SECURITY_NOTICE.md](SECURITY_NOTICE.md) for detailed security guidelines.

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discriminatory comments
- Personal attacks
- Publishing private information
- Trolling or inflammatory comments
- Any conduct violating professional standards

## Development Workflow

### Typical Development Cycle

1. **Pick an issue**
   - Check existing issues
   - Comment to claim issue
   - Ask questions if unclear

2. **Develop locally**
   - Create feature branch
   - Write code with tests
   - Run tests frequently

3. **Quality checks**
   - Format code
   - Run linters
   - Run tests with coverage
   - Security scan

4. **Submit PR**
   - Push to your fork
   - Create pull request
   - Respond to review comments

5. **After merge**
   - Delete feature branch
   - Update local main branch
   - Start next issue!

## Getting Help

- **Documentation**: Check README.md, DEPLOYMENT.md, API_REFERENCE.md
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Code review**: Request review from maintainers

## Resources

### FastAPI Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)

### Testing Resources
- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

### Development Tools
- [Black](https://black.readthedocs.io/)
- [isort](https://pycqa.github.io/isort/)
- [flake8](https://flake8.pycqa.org/)
- [pre-commit](https://pre-commit.com/)

## Questions?

Feel free to open an issue or discussion if you have questions!

---

Thank you for contributing to Amani Escrow Backend! 🚀
