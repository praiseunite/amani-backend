# 🔐 CRITICAL SECURITY NOTICE

## Exposed Credentials - Immediate Action Required

**URGENT**: Real production credentials were previously committed to this repository in the `.env.example` file. These credentials have been removed, but they remain in the git history.

### Affected Credentials

The following credentials were exposed and **MUST BE ROTATED IMMEDIATELY**:

1. **Supabase Database Credentials**
   - Database URL: `db.oromgkpbbrlfxkzzcarg.supabase.co`
   - Database password was exposed
   - Supabase Anonymous Key was exposed
   - Supabase Service Role Key was exposed

2. **Secret Key**
   - Application SECRET_KEY used for JWT signing was exposed

### Required Actions

#### For Repository Owners (IMMEDIATE)

1. **Rotate Supabase Credentials**
   - Go to Supabase Dashboard → Settings → Database
   - Reset the database password
   - Go to Settings → API
   - Rotate the service role key
   - Update all production environments with new credentials

2. **Rotate Application Secret Key**
   - Generate a new SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Update all production environments
   - This will invalidate all existing JWT tokens (users will need to re-login)

3. **Audit Access Logs**
   - Check Supabase logs for unauthorized access
   - Review database activity for suspicious operations
   - Check application logs for unusual authentication attempts

4. **Consider BFG Repo-Cleaner**
   - To remove secrets from git history: https://rtyley.github.io/bfg-repo-cleaner/
   - Note: This requires force-pushing and coordinating with all contributors

#### For All Developers

1. **Never commit `.env` files** - They are properly ignored in `.gitignore` now
2. **Use `.env.example` as a template only** - Fill in your own values in a local `.env` file
3. **Review the Secrets Management Guide** below before contributing

### Secrets Management Best Practices

#### ✅ DO

- Use `.env.example` with placeholder values only
- Store real credentials in `.env` (which is gitignored)
- Use environment variables for all secrets
- Use secret management tools (AWS Secrets Manager, HashiCorp Vault, etc.) in production
- Generate strong, unique secrets for each environment
- Rotate credentials regularly
- Use different credentials for development, staging, and production

#### ❌ DON'T

- Commit any files containing real credentials
- Share credentials via email, Slack, or other unsecured channels
- Reuse credentials across environments
- Commit `.env`, `.env.local`, or any `.env.*` files (except `.env.example`)
- Put credentials in code comments or documentation
- Use weak or default credentials

### Generating Secure Secrets

```bash
# Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate a random password
python -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(32)))"
```

### Pre-commit Hook Setup

To prevent accidental secret commits, install the pre-commit hook:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Run manually to check all files
pre-commit run --all-files
```

### Setting Up Local Development

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Fill in your values in `.env`:
   - Generate a new SECRET_KEY
   - Add your local database credentials
   - Add your API keys (get these from the respective service dashboards)

3. Never commit the `.env` file

### Reporting Security Issues

If you discover any security vulnerabilities, please email security@amani.com (or the appropriate security contact) instead of opening a public issue.

### Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Git-secrets](https://github.com/awslabs/git-secrets) - Prevents committing secrets

---

**Last Updated**: 2025-11-22  
**Status**: 🔴 CRITICAL - Action Required
