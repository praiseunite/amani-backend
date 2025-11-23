# Branch Protection and CI/CD Governance

This document outlines the branch protection rules, status checks, and CI/CD governance policies for the Amani Backend repository.

## Table of Contents

1. [Branch Strategy](#branch-strategy)
2. [Branch Protection Rules](#branch-protection-rules)
3. [Required Status Checks](#required-status-checks)
4. [Merge Requirements](#merge-requirements)
5. [Deployment Policies](#deployment-policies)
6. [Security Policies](#security-policies)

---

## Branch Strategy

### Branch Types

| Branch | Purpose | Protection Level | Auto-Deploy |
|--------|---------|-----------------|-------------|
| `main` | Production code | Highest | Yes (Production) |
| `develop` | Integration branch | High | Yes (Staging) |
| `feature/*` | Feature development | Medium | No |
| `bugfix/*` | Bug fixes | Medium | No |
| `hotfix/*` | Emergency fixes | High | Manual |
| `release/*` | Release preparation | High | Manual |

### Branch Naming Conventions

```
feature/[issue-number]-[short-description]
bugfix/[issue-number]-[short-description]
hotfix/[issue-number]-[short-description]
release/v[major].[minor].[patch]
```

Examples:
- `feature/123-add-wallet-api`
- `bugfix/456-fix-auth-token`
- `hotfix/789-security-patch`
- `release/v1.2.0`

---

## Branch Protection Rules

### Main Branch Protection

The `main` branch should have the following protection rules enabled:

#### Required

- ✅ **Require pull request reviews before merging**
  - Minimum reviewers: 1 (recommended: 2 for production)
  - Dismiss stale pull request approvals when new commits are pushed
  - Require review from Code Owners (if CODEOWNERS file exists)
  
- ✅ **Require status checks to pass before merging**
  - Require branches to be up to date before merging
  - Required status checks (see [Required Status Checks](#required-status-checks))
  
- ✅ **Require conversation resolution before merging**
  - All review comments must be resolved
  
- ✅ **Require signed commits** (recommended)
  - All commits must be signed with GPG/SSH
  
- ✅ **Require linear history** (optional)
  - Prevent merge commits, require rebase or squash
  
- ✅ **Include administrators**
  - Enforce rules for repository administrators

#### Restrictions

- ❌ **Do not allow force pushes**
  - Prevent `git push --force` on main
  
- ❌ **Do not allow deletions**
  - Prevent accidental branch deletion
  
- ✅ **Restrict who can push to matching branches**
  - Only CI/CD service accounts and administrators

### Develop Branch Protection

Similar to `main` but with relaxed requirements:

- ✅ Require pull request reviews (minimum: 1)
- ✅ Require status checks to pass
- ✅ Require conversation resolution
- ✅ Do not allow force pushes
- ⚠️ Allow administrators to bypass (for emergency fixes)

### Feature Branch Guidelines

- No strict protection rules
- Must be created from `develop`
- Must be merged back to `develop` via PR
- Should be deleted after merge

---

## Required Status Checks

All of the following checks must pass before a PR can be merged to `main` or `develop`:

### CI Pipeline Checks

#### Linting
- **Job**: `lint`
- **Checks**: Black, Flake8
- **Failure Policy**: Blocking
- **Timeout**: 5 minutes

```yaml
Status: ✅ Linting / black-format
Status: ✅ Linting / flake8-lint
```

#### Unit Tests
- **Job**: `unit-tests`
- **Coverage Requirement**: ≥85%
- **Failure Policy**: Blocking
- **Timeout**: 10 minutes

```yaml
Status: ✅ Unit Tests / pytest-unit
Status: ✅ Unit Tests / coverage-report
```

#### Integration Tests
- **Job**: `integration-tests`
- **Database Required**: Yes (PostgreSQL)
- **Failure Policy**: Blocking
- **Timeout**: 15 minutes

```yaml
Status: ✅ Integration Tests / pytest-integration
Status: ✅ Integration Tests / db-migrations
```

#### API Tests
- **Job**: `api-tests`
- **Failure Policy**: Blocking
- **Timeout**: 10 minutes

```yaml
Status: ✅ API Tests / pytest-api
```

#### Migration Tests
- **Job**: `migration-tests`
- **Checks**: Up/Down migration validation
- **Failure Policy**: Blocking
- **Timeout**: 10 minutes

```yaml
Status: ✅ Migration Tests / migration-up-down
```

### Security Checks

#### CodeQL Analysis
- **Job**: `codeql / analyze`
- **Language**: Python
- **Failure Policy**: Blocking on HIGH/CRITICAL
- **Timeout**: 30 minutes

```yaml
Status: ✅ CodeQL / Analyze (python)
```

#### Security Scanning
- **Jobs**: `trivy-scan`, `bandit-scan`, `safety-scan`
- **Failure Policy**: Warning (not blocking)
- **Critical/High Vulnerabilities**: Require acknowledgment

```yaml
Status: ⚠️ Security Scanning / Trivy (warnings allowed)
Status: ⚠️ Security Scanning / Bandit (warnings allowed)
Status: ⚠️ Security Scanning / Safety (warnings allowed)
```

#### Docker Image Scan
- **Job**: `docker-scan`
- **Trigger**: On push to main/develop
- **Failure Policy**: Warning
- **Action Required**: Review and remediate HIGH/CRITICAL

```yaml
Status: ⚠️ Security Scanning / Docker Image (warnings allowed)
```

### Build Checks

#### Docker Build
- **Job**: `build-docker`
- **Failure Policy**: Blocking
- **Timeout**: 15 minutes

```yaml
Status: ✅ Build / docker-image
```

---

## Merge Requirements

### Pull Request Requirements

#### Required Information

All PRs must include:

1. **Title**: Clear, descriptive title
   - Format: `[type]: [brief description]`
   - Examples: `feat: add wallet balance API`, `fix: resolve auth timeout`

2. **Description**: Comprehensive PR description
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Related issues/tickets

3. **Labels**: Appropriate labels
   - `feature`, `bugfix`, `hotfix`, `documentation`, etc.
   - `security` for security-related changes
   - `breaking-change` for breaking changes

4. **Linked Issues**: Reference related issues
   - Use keywords: `Closes #123`, `Fixes #456`, `Resolves #789`

#### Code Review Checklist

Reviewers should verify:

- [ ] Code follows style guidelines (Black, Flake8)
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Security best practices are followed
- [ ] No secrets or credentials in code
- [ ] Database migrations are backward compatible (if applicable)
- [ ] API changes are backward compatible (or versioned)
- [ ] Performance impact is acceptable
- [ ] Error handling is appropriate
- [ ] Logging is adequate

### Merge Strategies

#### Main Branch
- **Strategy**: Squash and merge (recommended)
- **Alternative**: Rebase and merge (for preserving commits)
- **Not Allowed**: Regular merge commits (to keep history clean)

#### Develop Branch
- **Strategy**: Squash and merge or Rebase and merge
- **Allowed**: Regular merge for complex features

### Merge Commit Message Format

```
[type]: [brief description] (#PR-number)

Detailed description of changes

Closes #issue-number
```

Example:
```
feat: add wallet balance caching (#123)

Implemented Redis-based caching for wallet balance queries
to improve performance. Cache expires after 5 minutes.

- Added Redis connection management
- Implemented cache invalidation on balance updates
- Added unit tests for caching logic

Closes #120
```

---

## Deployment Policies

### Automatic Deployments

#### Staging Environment
- **Trigger**: Push to `develop` branch
- **Workflow**: `.github/workflows/deploy-staging.yml`
- **Requirements**: All status checks pass
- **Rollback**: Automatic on health check failure

#### Production Environment
- **Trigger**: Push to `main` branch or version tag
- **Workflow**: `.github/workflows/deploy.yml`
- **Requirements**: 
  - All status checks pass
  - Successful staging deployment
  - Manual approval (for tagged releases)
- **Rollback**: Manual or automatic on critical failure

### Manual Deployments

Manual deployments can be triggered via:

```bash
# GitHub CLI
gh workflow run deploy.yml

# Or via GitHub UI
# Actions → Deploy to Production → Run workflow
```

### Deployment Approval

Production deployments from version tags require approval from:
- Engineering Lead
- DevOps Team
- (Optional) Product Owner for major releases

### Deployment Windows

#### Preferred Times
- **Staging**: Anytime
- **Production**: 
  - Monday-Thursday: 10:00-14:00 UTC
  - Friday: 10:00-12:00 UTC only
  - Weekend: Emergency hotfixes only

#### Blackout Windows
- During major holidays
- During high-traffic events
- End of month/quarter (avoid if possible)

---

## Security Policies

### Secret Management

#### Prohibited
- ❌ No secrets in code
- ❌ No secrets in commit history
- ❌ No secrets in configuration files
- ❌ No secrets in environment files (`.env` files must be in `.gitignore`)

#### Required
- ✅ Use GitHub Secrets for CI/CD
- ✅ Use environment variables for runtime secrets
- ✅ Use secret management service (AWS Secrets Manager, HashiCorp Vault, etc.)
- ✅ Rotate secrets regularly (at least quarterly)
- ✅ Use different secrets for each environment

### Dependency Management

#### Automated Updates
- **Tool**: Dependabot
- **Schedule**: Weekly on Mondays
- **Auto-merge**: Patch updates only (after CI passes)
- **Manual Review**: Minor and major updates

#### Security Alerts
- **Critical/High**: Must be addressed within 48 hours
- **Medium**: Must be addressed within 7 days
- **Low**: Address in next sprint

### Code Scanning

#### Required Scans
- CodeQL (on every PR and weekly schedule)
- Trivy (on every PR and daily schedule)
- Bandit (on every PR)
- Safety (on every PR)

#### Response Requirements
- **Critical**: Block merge, immediate fix required
- **High**: Require acknowledgment, fix in same PR or follow-up
- **Medium/Low**: Track and fix in backlog

### Vulnerability Disclosure

If a security vulnerability is discovered:

1. **Do not** create a public issue
2. Email security@amani.com
3. Follow coordinated disclosure process
4. Patch and release within SLA (based on severity)

---

## Enforcement

### Automated Enforcement
- Branch protection rules (GitHub)
- Required status checks (GitHub Actions)
- CODEOWNERS file
- Pre-commit hooks (optional, developer machines)

### Manual Enforcement
- Code review process
- Security review for sensitive changes
- Architecture review for major changes

### Violations
- First violation: Warning and education
- Repeated violations: Escalation to engineering lead
- Severe violations: Access revocation

---

## Review and Updates

This governance document should be reviewed:
- Quarterly by the engineering team
- After any major incident
- When introducing new tools or processes

### Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-01-22 | Initial version | DevOps Team |

---

## References

- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [GitHub Actions Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
