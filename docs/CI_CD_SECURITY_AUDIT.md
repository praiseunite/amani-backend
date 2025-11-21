# CI/CD Security Audit

## Overview

This document provides security guidelines and audit procedures for CI/CD secrets, environment variables, and connection strings in the Amani Backend project.

## Current Security Status

### CI/CD Secrets

#### GitHub Actions Secrets

The following secrets should be configured in GitHub repository settings:

**DO NOT USE IN CI** (Listed for awareness):
- ❌ Production database credentials
- ❌ Production API keys
- ❌ Real Supabase service keys
- ❌ Customer data access tokens

**Safe for CI** (Test/Mock values only):
- ✅ `SECRET_KEY` - Test-only secret key (e.g., "test-secret-key-for-ci")
- ✅ `DATABASE_URL` - CI PostgreSQL service (ephemeral, destroyed after test)
- ✅ `SUPABASE_URL` - Mock/test URL (e.g., "https://test.supabase.co")
- ✅ `SUPABASE_KEY` - Test anonymous key (no real access)
- ✅ `SUPABASE_SERVICE_KEY` - Test service key (no real access)

#### Codecov Token

- `CODECOV_TOKEN` - For coverage reporting (read-only for public repo)
- Safe to use in CI
- No access to sensitive data

### Environment Variables in CI Workflows

#### `.github/workflows/ci.yml`

**Current Setup** (Safe):
```yaml
env:
  SECRET_KEY: test-secret-key-for-ci
  DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
  SUPABASE_URL: https://test.supabase.co
  SUPABASE_KEY: test-key
  SUPABASE_SERVICE_KEY: test-service-key
  ENVIRONMENT: testing
```

**Security Assessment**: ✅ SAFE
- All values are test-only
- Database is ephemeral (created and destroyed with workflow)
- No production credentials exposed
- Values are visible in logs (acceptable for test data)

## Security Best Practices

### 1. Separation of Environments

**Principle**: Never use production credentials in CI/CD

| Environment | Database | API Keys | Secrets |
|-------------|----------|----------|---------|
| CI/Testing  | Ephemeral test DB | Mock/test keys | Test-only values |
| Staging     | Staging DB | Staging keys | Staging secrets |
| Production  | Production DB | Production keys | Production secrets |

### 2. Secret Rotation Policy

#### Test Secrets (CI)
- **Rotation**: Not required (no real access)
- **Review**: Annually or when exposed

#### Staging Secrets
- **Rotation**: Every 90 days
- **Process**: Update GitHub Secrets → Redeploy staging

#### Production Secrets
- **Rotation**: Every 60 days or immediately if compromised
- **Process**: 
  1. Generate new secret
  2. Update GitHub Secrets
  3. Deploy with new secrets
  4. Verify application works
  5. Revoke old secrets

### 3. Credential Storage

#### GitHub Secrets (Encrypted at Rest)

**How to add secrets**:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secret name and value
4. Secret is encrypted and not visible after saving

**Access control**:
- Only repository admins can view/edit secrets
- Secrets are masked in logs
- Third-party actions cannot access secrets by default

### 4. Preventing Secret Leaks

#### Code Review Checklist

- [ ] No hardcoded credentials in code
- [ ] No credentials in commit messages
- [ ] `.env` files in `.gitignore`
- [ ] No credentials in log statements
- [ ] No credentials in error messages
- [ ] Test values clearly marked as test-only

#### Pre-commit Hooks

Consider adding git-secrets or similar:

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
apt-get install git-secrets  # Linux

# Initialize in repository
git secrets --install
git secrets --register-aws  # If using AWS
```

#### Scanning Tools

Recommended tools for secret scanning:

1. **GitHub Secret Scanning** (Enabled by default)
   - Automatically scans commits for known secret patterns
   - Sends alerts if secrets detected

2. **TruffleHog**
   ```bash
   pip install truffleHog
   trufflehog --regex --entropy=False .
   ```

3. **Gitleaks**
   ```bash
   docker run -v ${pwd}:/path zricethezav/gitleaks:latest detect --source="/path" -v
   ```

## Audit Procedures

### Weekly Audit

1. **Review CI workflow files**
   ```bash
   # Check for hardcoded secrets
   grep -r "password\|secret\|key" .github/workflows/
   ```

2. **Check environment variables**
   - Verify only test values in CI
   - Ensure production values not exposed

3. **Review recent commits**
   ```bash
   # Check commit history for secrets
   git log --all --oneline --grep="password\|secret\|api.key"
   ```

### Monthly Audit

1. **Review GitHub Secrets**
   - List all configured secrets
   - Verify purpose of each secret
   - Remove unused secrets

2. **Access control review**
   - Review who has repository admin access
   - Verify team members still need access

3. **Check for leaked secrets**
   - Run secret scanning tools
   - Check for exposed credentials on GitHub

### Quarterly Audit

1. **Rotate staging secrets**
2. **Review secret rotation policy**
3. **Update this document with changes**
4. **Train team on security best practices**

## Incident Response

### If Secret is Exposed

**Immediate Actions** (< 1 hour):

1. **Identify scope**
   - Which secret was exposed?
   - Where was it exposed (commit, log, issue)?
   - Who has access?

2. **Rotate secret immediately**
   ```bash
   # Example: Rotate database password
   # 1. Connect to database
   psql $DATABASE_URL
   # 2. Change password
   ALTER USER production_user WITH PASSWORD 'new-secure-password';
   # 3. Update GitHub Secret
   # 4. Redeploy application
   ```

3. **Revoke old secret**
   - Disable API key
   - Change database password
   - Rotate JWT secret (invalidates all tokens)

4. **Remove from history** (if in git)
   ```bash
   # Use BFG Repo-Cleaner
   bfg --replace-text passwords.txt
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

**Follow-up Actions** (< 24 hours):

5. **Investigate impact**
   - Check logs for unauthorized access
   - Review database audit logs
   - Check for data exfiltration

6. **Notify stakeholders**
   - Inform team lead
   - Document incident
   - Report if required by policy

7. **Prevent recurrence**
   - Update security guidelines
   - Add pre-commit hooks
   - Train team members

## Connection String Security

### Database Connection Strings

**Format**: `postgresql+asyncpg://username:password@host:port/database`

**Security guidelines**:

1. **Never hardcode connection strings**
   ```python
   # ❌ BAD
   DATABASE_URL = "postgresql+asyncpg://admin:password123@prod.example.com/db"
   
   # ✅ GOOD
   from app.core.config import settings
   DATABASE_URL = settings.DATABASE_URL
   ```

2. **Use environment variables**
   ```bash
   export DATABASE_URL="postgresql+asyncpg://..."
   ```

3. **Secure password in connection string**
   - Use URL encoding for special characters
   - Use strong passwords (20+ characters)
   - Never log connection strings

4. **Use SSL/TLS for connections**
   ```python
   DATABASE_URL = "postgresql+asyncpg://user:pass@host/db?ssl=require"
   ```

### API Keys and Tokens

**Storage**:
- Store in environment variables
- Use secret management service (AWS Secrets Manager, Azure Key Vault)
- Never commit to version control

**Usage**:
```python
# ✅ GOOD
from app.core.config import settings
api_key = settings.FINCRA_API_KEY

# ❌ BAD
api_key = "sk_live_abc123..."
```

## Compliance

### Data Protection Requirements

- **GDPR**: No personal data in CI logs
- **PCI DSS**: No payment card data in test environment
- **HIPAA**: N/A for this project

### Access Logging

GitHub automatically logs:
- Secret access (when used in workflows)
- Repository access
- Secret updates

Review logs regularly in Settings → Logs.

## Security Training

### For Developers

**Required knowledge**:
- How to use environment variables
- Where to find secrets (GitHub Secrets)
- What NOT to commit (credentials, API keys)
- How to rotate secrets

**Resources**:
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

### For DevOps

**Additional knowledge**:
- Secret rotation procedures
- Incident response plan
- Audit procedures
- Monitoring and alerting

## Monitoring and Alerting

### GitHub Alerts

Enabled alerts:
- Secret scanning alerts
- Dependabot security alerts
- Code scanning alerts (if CodeQL enabled)

### Manual Checks

Weekly:
- Review workflow logs for suspicious activity
- Check for failed secret access attempts

### Automated Monitoring

Consider implementing:
- Failed authentication monitoring
- Database access logging
- API rate limiting and monitoring

## Contact Information

### Security Team

- **Security Lead**: [Name/Email]
- **DevOps Lead**: [Name/Email]
- **On-call Engineer**: [Contact/Pager]

### Reporting Security Issues

- Email: security@amani.example.com
- Private vulnerability disclosure: [GitHub Security Advisory]

## Review and Updates

- **Last reviewed**: November 21, 2025
- **Next review**: December 21, 2025
- **Review frequency**: Monthly
- **Document owner**: DevOps Team

## Changelog

- 2025-11-21: Initial security audit documentation created
- Added CI/CD secret inventory
- Documented rotation policy
- Added incident response procedures

---

**Document Version**: 1.0  
**Classification**: Internal Use Only  
**Approval**: [Name, Title, Date]
