# Honk Security Guide

## Overview

This guide covers security best practices for using Honk, particularly around credential management, token storage, and secure automation workflows.

## Credential Management

### Token Storage Architecture

Honk stores all authentication tokens using your operating system's secure credential storage:

**macOS:** Keychain Access
- Tokens stored in login keychain
- Encrypted with your user password
- Protected by system security policies

**Linux:** libsecret/gnome-keyring
- Uses D-Bus Secret Service API
- Encrypted at rest
- Access controlled by session management

**Windows:** Windows Credential Manager
- Integrated with Windows security
- Encrypted using Data Protection API (DPAPI)
- Protected by user account

### What Gets Stored

**GitHub Authentication:**
```
Keychain Entry: honk/github/github.com/username
Contents: OAuth token (managed by gh CLI)
Metadata: ~/.config/honk/auth.json
  - scopes: ["repo", "read:org", "gist"]
  - hostname: "github.com"
  - user: "username"
  - expires_at: null (OAuth tokens don't expire)
  - source: "gh auth login"
```

**Azure DevOps Authentication:**
```
Keychain Entry: honk/azure_devops/dev.azure.com/myorg
Contents: Personal Access Token (PAT)
Metadata: ~/.config/honk/auth.json
  - scopes: ["vso.code", "vso.work"]
  - org_url: "https://dev.azure.com/myorg"
  - user: "user@example.com"
  - expires_at: "2025-12-31T23:59:59Z"
  - created_with: "az devops login"
```

### Metadata File Security

The metadata file (`~/.config/honk/auth.json`) contains:
- ✅ Token expiration dates
- ✅ Scope lists
- ✅ Usernames
- ✅ Hostnames
- ❌ **NEVER** contains actual tokens

**File permissions:**
```bash
chmod 600 ~/.config/honk/auth.json
```

## Token Lifecycle Security

### Acquisition

**GitHub OAuth Flow:**
1. User runs `honk auth gh login`
2. Opens browser to GitHub OAuth page
3. User authorizes application
4. GitHub returns token to gh CLI
5. gh CLI stores in system keychain
6. Honk reads via gh CLI APIs only

**Azure DevOps Flow:**
1. User runs `honk auth az login`
2. Device code displayed
3. User visits activation URL
4. Microsoft validates identity
5. Token returned and stored in keychain
6. Honk wraps az CLI which manages storage

**Security benefits:**
- No token transmission through Honk
- Native CLI tools handle secure storage
- Browser-based auth uses system credentials
- No plaintext tokens in process memory

### Token Rotation

**GitHub:**
```bash
# Rotate OAuth token
honk auth gh logout
honk auth gh login

# Or refresh (reuses same token with new scopes)
honk auth gh refresh --scopes repo,workflow
```

**Azure DevOps:**
```bash
# PATs must be manually rotated
honk auth az logout
honk auth az login

# Set reminders for PAT expiry
honk auth az status --json | jq -r '.facts.auth.expires_at'
```

**Rotation Schedule Recommendations:**
- **OAuth tokens:** Rotate every 90 days
- **PATs with expiry:** Before expiration date
- **PATs without expiry:** Every 30 days
- **Compromised tokens:** Immediately

### Revocation

**GitHub:**
```bash
# Via Honk
honk auth gh logout

# Via GitHub UI
# Settings → Applications → Authorized OAuth Apps → GitHub CLI → Revoke
```

**Azure DevOps:**
```bash
# Via Honk
honk auth az logout

# Via Azure DevOps UI
# User Settings → Personal Access Tokens → Revoke
```

**When to revoke:**
- Lost/stolen device
- Suspected compromise
- Employee offboarding
- Shared development machine turnover
- End of project/contract

## Scope Management

### Principle of Least Privilege

Only request scopes you actually need:

```bash
# ❌ Bad: Request all scopes
honk auth gh login --scopes repo,workflow,admin:org,delete_repo,admin:enterprise

# ✅ Good: Minimal scopes for task
honk auth gh login --scopes repo,read:org
```

### Scope Escalation

Add scopes incrementally as needed:

```bash
# Start minimal
honk auth gh login --scopes repo

# Add workflow scope when needed
honk auth gh refresh --scopes workflow

# Add org admin only when required
honk auth gh refresh --scopes admin:org
```

### Scope Audit

Review active scopes regularly:

```bash
# Check current scopes
honk auth gh status

# Compare with requirements
honk auth gh status --json | jq '.facts.auth.scopes'
```

## Environment Variables

### Secure Usage

**Avoid storing tokens in env vars:**

```bash
# ❌ Insecure
export GH_TOKEN="ghp_xxxxxxxxxxxx"
export AZURE_DEVOPS_EXT_PAT="xxxxxxxxxxxx"

# ✅ Secure: Let Honk/CLI tools manage tokens
honk auth gh status
```

**CI/CD Exception:**

In CI environments, secrets must come from secure secret stores:

```yaml
# GitHub Actions - secure
env:
  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
run: honk auth gh status

# Azure Pipelines - secure
env:
  AZURE_DEVOPS_EXT_PAT: $(DEVOPS_PAT_SECRET)
script: honk auth az status
```

### Shell History Protection

Prevent tokens from entering shell history:

```bash
# Set history ignore patterns
export HISTIGNORE="*GH_TOKEN*:*PAT*:*TOKEN*:*SECRET*"

# Or use space prefix (bash/zsh)
 export GH_TOKEN="xxx"  # Leading space prevents history save

# Better: Don't use env vars for tokens
```

## CI/CD Security

### GitHub Actions

**Secure approach:**

```yaml
name: Secure Workflow

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # ✅ Use built-in GITHUB_TOKEN
      - name: Authenticate
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: honk auth gh status
      
      # ✅ Use repository secrets for other tokens
      - name: Azure Auth
        env:
          AZURE_DEVOPS_EXT_PAT: ${{ secrets.AZURE_PAT }}
        run: honk auth az status
```

**Security features:**
- Secrets never logged
- Automatic masking in output
- Scoped to repository
- Automatic rotation

**Avoid:**
```yaml
# ❌ Don't echo secrets
run: echo ${{ secrets.MY_TOKEN }}

# ❌ Don't write to disk
run: echo ${{ secrets.MY_TOKEN }} > token.txt

# ❌ Don't pass via arguments (shows in ps)
run: honk some-command --token ${{ secrets.MY_TOKEN }}
```

### Azure Pipelines

**Secure approach:**

```yaml
trigger: [main]

variables:
- group: secure-tokens  # Variable group with secrets

steps:
- script: honk auth az status
  env:
    AZURE_DEVOPS_EXT_PAT: $(AZURE_PAT)
  displayName: 'Check Auth'
```

**Security features:**
- Variable groups for secrets
- Secret variables masked in logs
- Access control via permissions

## Common Vulnerabilities

### 1. Token Exposure in Logs

**Problem:**
```bash
# Token visible in command output
honk some-command --token ghp_xxxxxxxxxxxx
```

**Solution:**
```bash
# Use auth subsystem
honk auth gh login
honk some-command  # No token needed
```

### 2. Token Exposure in Code

**Problem:**
```python
# Hardcoded token in source
TOKEN = "ghp_xxxxxxxxxxxx"
```

**Solution:**
```python
# Use auth subsystem via CLI
import subprocess
result = subprocess.run(
    ["honk", "auth", "gh", "status", "--json"],
    capture_output=True
)
# Honk handles token securely
```

### 3. Token Sharing

**Problem:**
- Sharing tokens via email/Slack
- Committing tokens to version control
- Including in screenshots

**Solution:**
- Each user maintains their own tokens
- Use service accounts for shared automation
- Review `.gitignore` for secret files

### 4. Long-Lived Tokens

**Problem:**
- PATs that never expire
- Forgotten tokens in old projects

**Solution:**
```bash
# Set expiration on PATs
# GitHub: 90 days maximum
# Azure: 1 year maximum

# Audit regularly
honk auth gh status --json | jq '.facts.auth.expires_at'
```

### 5. Excessive Scopes

**Problem:**
```bash
# Token with more access than needed
honk auth gh login --scopes repo,delete_repo,admin:org
```

**Solution:**
```bash
# Minimal scopes
honk auth gh login --scopes repo,read:org
```

## Security Checklist

### Initial Setup

- [ ] Install Honk from official sources
- [ ] Verify system keychain is configured
- [ ] Set up proper file permissions (`~/.config/honk/`)
- [ ] Configure shell history filtering
- [ ] Review `.gitignore` for token files

### Regular Operations

- [ ] Rotate tokens every 90 days
- [ ] Audit active tokens monthly
- [ ] Review scope requirements
- [ ] Check for expired/expiring PATs
- [ ] Monitor failed authentication attempts

### CI/CD Setup

- [ ] Use repository secrets
- [ ] Enable secret masking
- [ ] Limit workflow permissions
- [ ] Review secret access logs
- [ ] Rotate service account tokens

### Incident Response

- [ ] Revoke compromised tokens immediately
- [ ] Rotate related credentials
- [ ] Audit access logs
- [ ] Update security policies
- [ ] Document lessons learned

## Multi-User Environments

### Shared Development Machines

**Problem:** Multiple developers using same machine.

**Solution:**
```bash
# Each user has their own credentials
user1$ honk auth gh login
user2$ honk auth gh login

# Keychain separates by user account
# No credential sharing between users
```

### Container Environments

**Problem:** Containers don't persist credentials.

**Solution:**
```bash
# Mount secret at runtime
docker run \
  -e GH_TOKEN="${GH_TOKEN}" \
  my-image honk auth gh status

# Or use Docker secrets
docker secret create gh_token ~/.secrets/gh_token
docker service create \
  --secret gh_token \
  my-image
```

### Service Accounts

**Best practices:**
1. Create dedicated service accounts
2. Use minimal required scopes
3. Set expiration dates
4. Document ownership and purpose
5. Rotate regularly
6. Monitor usage patterns

```bash
# Example: CI service account
# GitHub: Create machine user account
# Azure: Create service principal

# Configure with minimal scopes
honk auth gh login --scopes repo:status,repo:invite
```

## Compliance Considerations

### SOC 2 / ISO 27001

Honk's auth system supports compliance:
- **Access Control:** User-based credential isolation
- **Encryption:** At-rest via OS keychain
- **Audit Trail:** Metadata logs authentication events
- **Least Privilege:** Granular scope management
- **Token Lifecycle:** Rotation and expiration policies

### GDPR

Personal data handling:
- Usernames stored in metadata file
- Tokens in encrypted keychain
- No telemetry or analytics
- Local storage only

### Industry Specific

**Financial Services (PCI DSS):**
- Encrypted credential storage ✅
- Access control by user ✅
- Audit logging available ✅
- Token rotation policies ✅

**Healthcare (HIPAA):**
- Secure authentication ✅
- User-level access control ✅
- Encrypted storage ✅
- Audit trail support ✅

## Incident Response

### Suspected Token Compromise

1. **Immediate Actions:**
```bash
# Revoke tokens
honk auth gh logout
honk auth az logout

# Via UI
# GitHub: Settings → Applications → Revoke
# Azure: User Settings → PATs → Revoke
```

2. **Investigation:**
```bash
# Check last authentication
honk auth gh status --json | jq '.facts.auth'

# Review metadata
cat ~/.config/honk/auth.json

# Check system logs
# macOS: Console.app
# Linux: journalctl
```

3. **Recovery:**
```bash
# Generate new tokens
honk auth gh login
honk auth az login

# Update CI/CD secrets
# Rotate service account tokens
# Notify security team
```

### Data Breach Response

If keychain compromised:
1. Change system password
2. Revoke all OAuth applications
3. Rotate all PATs
4. Enable 2FA if not already
5. Review account activity logs
6. Document timeline

## Best Practices Summary

### DO

✅ Use Honk's auth subsystem
✅ Store tokens in system keychain
✅ Rotate tokens regularly
✅ Use minimal scopes
✅ Enable 2FA on accounts
✅ Audit token usage
✅ Use CI secrets for automation
✅ Set PAT expiration dates

### DON'T

❌ Store tokens in code
❌ Commit tokens to git
❌ Share tokens between users
❌ Log tokens to files
❌ Use tokens in URLs
❌ Email/Slack tokens
❌ Store in environment variables (except CI)
❌ Use excessive scopes

## Additional Resources

- [GitHub Token Security](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure)
- [Azure DevOps Security Best Practices](https://learn.microsoft.com/en-us/azure/devops/organizations/security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Auth User Guide](./auth-user-guide.md)
- [Auth Spec](./spec-auth.md)

## Reporting Security Issues

Found a security vulnerability?

**Do NOT create a public issue.**

Contact: security@example.com (update with actual contact)

Include:
- Description of vulnerability
- Steps to reproduce
- Impact assessment
- Suggested remediation

We take security seriously and will respond within 24 hours.
