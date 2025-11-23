# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Amani Backend application.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and includes:
- **Automated Testing**: Run pytest test suite on every push and pull request
- **Code Quality Checks**: Black formatting and Flake8 linting
- **Security Scanning**: CodeQL, Trivy, Bandit, and Safety checks
- **Docker Build Verification**: Ensure Docker images build successfully
- **Automated Deployment**: Build and push Docker images to registry on main branch
- **Environment Management**: Separate staging and production deployments
- **Version Tracking**: Build metadata and version information in deployments

## GitHub Actions Workflows

### CI Pipeline (`ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

#### Jobs:

1. **Linting**
   - Runs Black code formatter check
   - Runs Flake8 linting
   - Both are configured as informational (won't fail CI)
   - Helps maintain code quality standards

2. **Unit Tests**
   - Runs pytest unit test suite with coverage
   - Coverage requirement: ≥85%
   - Uploads coverage reports to Codecov
   - Tests domain, ports, and application layers

3. **Integration Tests**
   - Runs with PostgreSQL service container
   - Tests database interactions
   - Runs Alembic migrations
   - Uploads coverage reports to Codecov

4. **API Tests**
   - Tests API endpoints
   - Validates request/response schemas
   - Uploads coverage reports to Codecov

5. **Migration Tests**
   - Tests migration up (upgrade head)
   - Tests migration down (rollback)
   - Verifies migration reversibility
   - Ensures database state consistency

6. **Build Docker Image**
   - Verifies Docker image builds successfully
   - Only runs if linting and testing pass
   - Uses BuildKit cache for faster builds

### Security Scanning (`security-scan.yml`)

Runs on push, pull request, and daily schedule.

#### Jobs:

1. **Trivy Vulnerability Scanner**
   - Scans filesystem for vulnerabilities
   - Scans requirements.txt for package vulnerabilities
   - Uploads results to GitHub Security tab (SARIF format)
   - Generates artifact reports for review

2. **Bandit Security Linter**
   - Scans Python code for security issues
   - Checks for common security anti-patterns
   - Generates JSON report artifact
   - Configuration in pyproject.toml

3. **Safety Dependency Check**
   - Checks Python dependencies against vulnerability database
   - Identifies known security issues
   - Generates JSON report artifact

4. **Docker Image Security Scan**
   - Scans built Docker image with Trivy
   - Checks for OS package vulnerabilities
   - Uploads results to GitHub Security tab
   - Generates detailed report artifact

### CodeQL Analysis (`codeql.yml`)

Runs on push, pull request, and weekly schedule (Mondays at 6:00 UTC).

#### Features:
- Static analysis for Python code
- Security-extended query suite
- Security and quality queries
- Uploads findings to GitHub Security tab
- Ignores test files and migration scripts

### Staging Deployment (`deploy-staging.yml`)

Runs on push to `develop` branch or manual trigger.

#### Pipeline:

1. **Build and Test**
   - Runs linting and tests
   - Ensures code quality before deployment

2. **Build and Push Image**
   - Generates version metadata (commit SHA, timestamp)
   - Builds Docker image with build arguments
   - Pushes to GitHub Container Registry (GHCR)
   - Tags: `staging-latest`, `staging-<sha>`, versioned tags

3. **Deploy to Staging**
   - Uses GitHub Environment: `staging`
   - Waits for deployment readiness
   - Runs smoke tests
   - Notifies on success/failure

### Production Deployment (`deploy.yml`)

Runs on push to `main` branch, version tags, or manual trigger.

#### Pipeline:

1. **Build and Push Image**
   - Generates production version metadata
   - Builds Docker image with build information
   - Pushes to Docker Hub and GHCR
   - Tags: `latest`, `prod-<sha>`, semantic versions
   - Creates deployment metadata artifact

2. **Deploy to Production**
   - Uses GitHub Environment: `production`
   - Requires manual approval for tagged releases
   - Creates rollback backup
   - Deploys new version
   - Runs smoke tests
   - Auto-rollback on failure

### Fly.io Deployment (`fly-deploy.yml`)

Simple deployment to Fly.io platform.

#### Features:
- Automatic deployment on main branch push
- Uses Fly.io CLI (flyctl)
- Remote build for efficiency

## Version and Build Tracking

### Build Metadata

Every deployment includes:
- **Version**: Semantic version or auto-generated
- **Commit SHA**: Git commit identifier
- **Build Time**: UTC timestamp
- **Build Number**: GitHub Actions run number
- **Build Branch**: Source branch name

### Docker Image Labels

Images are labeled with OCI-standard metadata:
```
org.opencontainers.image.version
org.opencontainers.image.revision
org.opencontainers.image.created
org.opencontainers.image.title
org.opencontainers.image.description
org.opencontainers.image.source
```

### Runtime Access

Build information is available via:
- Environment variables in container
- `/app/build-info.json` file
- API endpoint: `/api/v1/version`
- Health check: `/api/v1/health` (includes version)

## Environment Management

### Environments

| Environment | Branch | URL | Auto-Deploy |
|------------|--------|-----|-------------|
| Development | feature/* | localhost | No |
| Staging | develop | staging-api.amani.com | Yes |
| Production | main | api.amani.com | Yes |

### Environment Variables

Each environment has separate secret management:

#### CI/CD Secrets (GitHub Secrets)
- `DOCKER_USERNAME` / `DOCKER_PASSWORD`
- `FLY_API_TOKEN`
- `CODECOV_TOKEN`

#### Application Secrets (per environment)
- `DATABASE_URL`
- `SECRET_KEY`
- `SUPABASE_URL` / `SUPABASE_KEY`
- `FINCRA_API_KEY` / `FINCRA_API_SECRET`
- `REDIS_URL`
- Environment-specific configuration

### Infrastructure as Code

- Docker Compose for local development
- Dockerfile for consistent builds
- Fly.io configuration: `fly.toml`
- Prometheus/Grafana configs in `config/`

## Artifact Management

### Build Artifacts

Stored with 90-day retention:
- Deployment metadata JSON
- Security scan reports (Trivy, Bandit, Safety)
- Test coverage reports

### Docker Images

Tagged and stored in:
- Docker Hub: `username/amani-backend`
- GitHub Container Registry: `ghcr.io/praiseunite/amani-backend`

Retention policy:
- `latest`: Always current from main
- Semantic versions: Permanent
- SHA tags: 90 days
- Staging tags: 30 days

## Rollback Procedures

### Automated Rollback Script

```bash
# List available versions
./scripts/rollback.sh

# Rollback to specific version
./scripts/rollback.sh v1.2.3

# Automated rollback (no confirmation)
./scripts/rollback.sh v1.2.3 --auto-confirm
```

### Manual Rollback

See [Incident Playbook](docs/runbooks/incident_playbook.md#rollback-procedures) for detailed procedures.

### Database Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

## Branch Protection and Governance

See [Branch Protection Documentation](docs/BRANCH_PROTECTION.md) for:
- Branch protection rules
- Required status checks
- Merge requirements
- Deployment policies
- Security policies

### Required Status Checks

All PRs must pass:
- ✅ Linting (Black, Flake8)
- ✅ Unit Tests (≥85% coverage)
- ✅ Integration Tests
- ✅ API Tests
- ✅ Migration Tests
- ✅ CodeQL Analysis
- ✅ Docker Build
- ⚠️ Security Scans (warnings allowed, must review)

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

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v
```

### Code Quality Checks

```bash
# Check formatting with Black
black --check app/ tests/

# Auto-format code with Black
black app/ tests/

# Run Flake8 linting
flake8 app/ tests/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Security Scanning

```bash
# Run Bandit security scan
bandit -r app/ -c pyproject.toml

# Run Safety dependency check
safety check

# Run Trivy filesystem scan
trivy fs .

# Scan Docker image
docker build -t amani-backend:test .
trivy image amani-backend:test
```

### Docker

#### Building the Image

```bash
# Build Docker image
docker build -t amani-backend:local .

# Build with version metadata
docker build \
  --build-arg BUILD_VERSION=dev \
  --build-arg BUILD_SHA=$(git rev-parse --short HEAD) \
  --build-arg BUILD_TIME=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  -t amani-backend:local .

# Run container
docker run -p 8000:8000 --env-file .env amani-backend:local
```

#### Using Docker Compose

```bash
# Start all services (app + Redis + Monitoring stack)
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
Configures Black code formatter and Bandit:
- Line length: 100 characters
- Target Python 3.11+
- Excludes virtual environments and migrations
- Bandit security exclusions

### .dockerignore
Excludes files from Docker build context:
- Python cache files
- Virtual environments
- Environment files
- IDE configurations
- Test artifacts

### dependabot.yml
Configures automated dependency updates:
- Weekly updates on Mondays
- Separate groups for production and development dependencies
- Auto-labels by ecosystem
- Ignores major version updates (manual review required)

## GitHub Secrets Required

To enable full CI/CD functionality, configure these secrets in your GitHub repository:

### For Deployment
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password or access token
- `FLY_API_TOKEN`: Fly.io API token (if using Fly.io)

### For Coverage Reporting
- `CODECOV_TOKEN`: Codecov upload token (optional but recommended)

### For Application (per environment)
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Application secret key
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- `FINCRA_API_KEY`, `FINCRA_API_SECRET`
- `REDIS_URL` (if using Redis)

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
   - Includes build metadata
   - Has health check configured
   - Creates build-info.json for runtime access

### Image Tags

Images are tagged with multiple identifiers:
- `latest`: Most recent build from main branch
- `main-<sha>`: Specific commit from main branch
- `staging-latest`: Most recent staging build
- `staging-<sha>`: Specific staging commit
- Semantic versions when using release tags (e.g., `v1.2.3`)

## Continuous Deployment

### Automatic Deployment

**Staging (develop branch):**
1. Push to develop triggers CI pipeline
2. If all tests pass, staging deployment workflow triggers
3. Docker image is built and pushed with staging tags
4. Image is deployed to staging environment
5. Health checks verify deployment
6. Smoke tests run automatically

**Production (main branch):**
1. Merge to main triggers CI pipeline
2. If all tests pass, production deployment workflow triggers
3. Docker image is built and pushed with production tags
4. Deployment metadata is generated and stored
5. Image is deployed to production environment
6. Health checks verify deployment
7. Smoke tests run automatically
8. Rollback on failure

### Manual Deployment

You can manually trigger deployment:
1. Go to the "Actions" tab in GitHub repository
2. Select deployment workflow
3. Click "Run workflow"
4. Select branch (usually main for prod, develop for staging)
5. Confirm deployment

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
   - Verify credentials are correct
   - Check if secrets are properly configured
   - Review deployment logs for specific errors

4. **Security Scan Failures**
   - Review vulnerability details in GitHub Security tab
   - Update vulnerable dependencies
   - Add exceptions for false positives (document why)

## Best Practices

1. **Before Pushing**:
   - Run tests locally
   - Check code formatting with Black
   - Run Flake8 to catch potential issues
   - Run security scans locally

2. **Pull Requests**:
   - Ensure CI passes before requesting review
   - Address any warnings from linting and security scans
   - Maintain or improve test coverage
   - Include migration rollback tests if modifying DB schema

3. **Merging to Main**:
   - Ensure all tests pass
   - Verify deployment workflow succeeds
   - Monitor application after deployment
   - Keep an eye on error rates and response times

4. **Security**:
   - Never commit secrets or credentials
   - Review security scan results
   - Address HIGH and CRITICAL vulnerabilities immediately
   - Keep dependencies up to date

## Incident Response

For production incidents, follow the [Incident Playbook](docs/runbooks/incident_playbook.md):
- Assess severity and impact
- Follow rollback procedures if needed
- Communicate with stakeholders
- Document timeline and actions
- Conduct post-mortem review

## Future Enhancements

Potential improvements to the CI/CD pipeline:

- [x] Add CodeQL security scanning
- [x] Add Trivy vulnerability scanning
- [x] Add Dependabot for automated updates
- [x] Add staging environment deployment
- [x] Add build metadata tracking
- [x] Add automated rollback scripts
- [x] Implement environment separation
- [ ] Add performance testing in CI
- [ ] Implement blue-green deployments
- [ ] Add automatic rollback on metrics degradation
- [ ] Integrate with APM for deployment tracking
- [ ] Add automated smoke tests suite
- [ ] Implement canary deployments
- [ ] Add deployment approval gates for production

## Support

For issues or questions about the CI/CD pipeline:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Check [Branch Protection](docs/BRANCH_PROTECTION.md) docs
4. Check [Incident Playbook](docs/runbooks/incident_playbook.md)
5. Contact the DevOps team
6. Create an issue in the repository
