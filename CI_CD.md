# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Amani Backend application.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and includes:
- **Automated Testing**: Run pytest test suite on every push and pull request
- **Code Quality Checks**: Black formatting and Flake8 linting
- **Docker Build Verification**: Ensure Docker images build successfully
- **Automated Deployment**: Build and push Docker images to registry on main branch

## GitHub Actions Workflows

### CI Pipeline (`ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

#### Jobs:

1. **Linting**
   - Runs Black code formatter check
   - Runs Flake8 linting
   - Both are configured as informational (won't fail CI)
   - Helps maintain code quality standards

2. **Testing**
   - Runs pytest test suite with coverage
   - Uploads coverage reports to Codecov
   - Requires all tests to pass before deployment

3. **Build Docker Image**
   - Verifies Docker image builds successfully
   - Only runs if linting and testing pass
   - Uses BuildKit cache for faster builds

### Deploy Pipeline (`deploy.yml`)

Runs on pushes to `main` branch and can be triggered manually.

#### Features:
- Builds production Docker image
- Pushes to Docker Hub (requires secrets)
- Tags images with:
  - Branch name
  - Git SHA
  - `latest` tag for main branch
  - Semantic version tags if available

## Local Development

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_validation.py -v
```

### Code Quality Checks

```bash
# Check formatting with Black
black --check app/ tests/

# Auto-format code with Black
black app/ tests/

# Run Flake8 linting
flake8 app/ tests/
```

### Docker

#### Building the Image

```bash
# Build Docker image
docker build -t amani-backend:local .

# Run container
docker run -p 8000:8000 --env-file .env amani-backend:local
```

#### Using Docker Compose

```bash
# Start all services (app + Redis)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

## Configuration Files

### pytest.ini
Configures pytest behavior:
- Test discovery patterns
- Coverage reporting
- Async test support
- Test markers

### .flake8
Configures Flake8 linting:
- Line length: 100 characters
- Ignores certain style rules (E203, E266, etc.)
- Excludes virtual environments and build directories
- Allows complexity up to 10

### pyproject.toml
Configures Black code formatter:
- Line length: 100 characters
- Target Python 3.11+
- Excludes virtual environments and migrations

### .dockerignore
Excludes files from Docker build context:
- Python cache files
- Virtual environments
- Environment files
- IDE configurations
- Test artifacts

## GitHub Secrets Required

To enable full CI/CD functionality, configure these secrets in your GitHub repository:

### For Deployment (deploy.yml):
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password or access token

### For Coverage Reporting:
- `CODECOV_TOKEN`: Codecov upload token (optional but recommended)

## Environment Variables for Testing

The test suite requires certain environment variables. These are automatically set by `tests/conftest.py` with sensible defaults:

- `SECRET_KEY`: JWT secret key
- `DATABASE_URL`: Database connection string
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `ENVIRONMENT`: Set to "testing"

For CI environments, these are set in the workflow file.

## Docker Image Structure

The Dockerfile uses a multi-stage build for optimized image size:

1. **Builder Stage**: 
   - Installs build dependencies
   - Installs Python packages
   
2. **Final Stage**:
   - Minimal runtime image
   - Copies only necessary files
   - Runs as non-root (security best practice)

### Image Tags

Images are tagged with multiple identifiers:
- `latest`: Most recent build from main branch
- `main-<sha>`: Specific commit from main branch
- Semantic versions when using release tags

## Continuous Deployment

### Automatic Deployment

When code is merged to `main`:
1. CI pipeline runs tests and checks
2. If all pass, deployment workflow triggers
3. Docker image is built and pushed to registry
4. Image is tagged and available for deployment

### Manual Deployment

You can manually trigger deployment:
1. Go to GitHub Actions tab
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Select branch (usually main)

## Monitoring and Debugging

### View Workflow Runs
- Go to the "Actions" tab in GitHub repository
- Click on a specific workflow run to see details
- View logs for each job and step

### Common Issues

1. **Tests Failing**
   - Check test logs in GitHub Actions
   - Run tests locally to reproduce
   - Ensure environment variables are set correctly

2. **Docker Build Failing**
   - Check Dockerfile syntax
   - Verify requirements.txt is valid
   - Ensure all dependencies are available

3. **Deployment Failing**
   - Verify Docker Hub credentials are correct
   - Check if secrets are properly configured
   - Review deployment logs for specific errors

## Best Practices

1. **Before Pushing**:
   - Run tests locally
   - Check code formatting with Black
   - Run Flake8 to catch potential issues

2. **Pull Requests**:
   - Ensure CI passes before requesting review
   - Address any warnings from linting
   - Maintain or improve test coverage

3. **Merging to Main**:
   - Ensure all tests pass
   - Verify deployment workflow succeeds
   - Monitor application after deployment

## Future Enhancements

Potential improvements to the CI/CD pipeline:

- [ ] Add integration tests with database
- [ ] Add end-to-end API tests
- [ ] Implement staging environment deployment
- [ ] Add security scanning (Snyk, Trivy)
- [ ] Add performance testing
- [ ] Implement blue-green deployments
- [ ] Add automatic rollback on failure
- [ ] Integrate with monitoring/alerting systems

## Support

For issues or questions about the CI/CD pipeline:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Contact the DevOps team
4. Create an issue in the repository
