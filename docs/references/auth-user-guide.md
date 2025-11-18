# Honk Authentication User Guide

## Overview

The `honk auth` subsystem provides unified authentication management for GitHub and Azure DevOps. It handles credential acquisition, storage, validation, and refresh cycles so individual tools never touch tokens directly.

## Quick Start

### GitHub Authentication

```bash
# Check authentication status
honk auth gh status

# Login (opens browser for OAuth)
honk auth gh login

# Login with specific scopes
honk auth gh login --scopes repo,read:org,workflow

# Refresh and add new scopes
honk auth gh refresh --scopes workflow

# Logout
honk auth gh logout
```

### Azure DevOps Authentication

```bash
# Check authentication status
honk auth az status

# Login (device code flow)
honk auth az login

# Logout
honk auth az logout
```

## GitHub Authentication

### Status Command

Check your current GitHub authentication state:

```bash
honk auth gh status
```

Example output:
```
✓ Authenticated to github.com as username
  User: username
  Hostname: github.com
  Scopes: repo, read:org, gist
```

JSON output for automation:
```bash
honk auth gh status --json
```

### Login Command

Login to GitHub using OAuth flow:

```bash
# Basic login (opens browser)
honk auth gh login

# Login with specific scopes
honk auth gh login --scopes repo,read:org,workflow,admin:org

# Login without browser (device code)
honk auth gh login --no-web
```

**Common Scopes:**
- `repo` - Full control of private repositories
- `read:org` - Read org and team membership
- `workflow` - Update GitHub Action workflows
- `admin:org` - Full control of orgs and teams
- `gist` - Create gists

The login command:
1. Opens your browser to GitHub OAuth page
2. Prompts you to authorize the application
3. Saves the token securely in your system keychain
4. Validates the token and displays your authentication status

### Refresh Command

Add new scopes or refresh your existing token:

```bash
# Add workflow scope
honk auth gh refresh --scopes repo,read:org,workflow

# Refresh with all existing scopes
honk auth gh refresh
```

**Note:** GitHub CLI maintains baseline scopes (`repo`, `read:org`, `gist`) automatically. You cannot remove these.

### Logout Command

Remove GitHub authentication:

```bash
honk auth gh logout
```

This removes the token from your system keychain and logs you out of the GitHub CLI.

### GitHub Enterprise

To authenticate with GitHub Enterprise:

```bash
# Login to GHE instance
honk auth gh login --hostname github.enterprise.com

# Check status for specific host
honk auth gh status --hostname github.enterprise.com
```

## Azure DevOps Authentication

### Status Command

Check your Azure DevOps authentication state:

```bash
honk auth az status
```

Example output:
```
✓ Authenticated to Azure as user@example.com
  User: user@example.com
```

### Login Command

Login to Azure using device code flow:

```bash
honk auth az login
```

This command:
1. Displays a device code
2. Opens your browser to Microsoft's device login page
3. Prompts you to enter the device code
4. Saves the authentication token securely
5. Configures Azure CLI for DevOps operations

**For headless environments:**
The device code flow is designed for headless/remote scenarios. Simply copy the code and visit the URL from any device.

### Logout Command

Remove Azure authentication:

```bash
honk auth az logout
```

## JSON Output

All auth commands support `--json` flag for automation:

```bash
# Get status as JSON
honk auth gh status --json

# Example output structure
{
  "version": "1.0",
  "command": ["honk", "auth", "gh", "status"],
  "status": "ok",
  "code": "auth.gh.status.valid",
  "summary": "Authenticated to github.com as username",
  "facts": {
    "auth": {
      "provider": "github",
      "status": "valid",
      "hostname": "github.com",
      "user": "username",
      "scopes": ["repo", "read:org", "gist"],
      "source": "gh auth status"
    }
  },
  "next": []
}
```

## Authentication Flow Integration

Other `honk` commands automatically check authentication using doctor packs:

```bash
# This command requires GitHub auth
honk watchdog actions analyze --repo owner/repo

# If not authenticated, you'll see:
# ✗ GitHub authentication: Not logged in
#   → Run: honk auth gh login
```

The doctor pack system ensures prerequisites are met before commands execute.

## Security Best Practices

### Token Storage

Tokens are stored securely using your system's keychain:
- **macOS:** Keychain Access
- **Linux:** libsecret/gnome-keyring
- **Windows:** Windows Credential Manager

Never store tokens in:
- Environment variables
- Configuration files
- Shell history
- Version control

### Token Rotation

GitHub tokens don't expire by default (OAuth tokens), but you should rotate them periodically:

```bash
# Logout and login again
honk auth gh logout
honk auth gh login
```

Azure DevOps PATs have expiration dates. Check and refresh before expiry:

```bash
# Check status regularly
honk auth az status
```

### Scope Management

Follow the principle of least privilege:

```bash
# Only request scopes you need
honk auth gh login --scopes repo,read:org

# Add scopes as needed
honk auth gh refresh --scopes workflow
```

### Multi-Account Setup

For multiple GitHub accounts:

```bash
# Use different hostnames or gh CLI profiles
export GH_HOST=github.com
honk auth gh login

export GH_HOST=github-work.com
honk auth gh login --hostname github-work.com
```

## Troubleshooting

### "Not logged in" Error

**Problem:** `honk auth gh status` shows not logged in.

**Solution:**
```bash
honk auth gh login
```

### "Missing scopes" Error

**Problem:** Command fails with missing scopes error.

**Solution:**
```bash
# Add the required scopes
honk auth gh refresh --scopes repo,read:org,workflow
```

### "gh CLI not found" Error

**Problem:** GitHub CLI not installed.

**Solution:**
```bash
# macOS
brew install gh

# Linux
# See https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# Windows
# See https://github.com/cli/cli/releases
```

### "az CLI not found" Error

**Problem:** Azure CLI not installed.

**Solution:**
```bash
# macOS
brew install azure-cli

# Linux/Windows
# See https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
```

### Authentication Expired

**Problem:** Token expired or revoked.

**Solution:**
```bash
# Logout and login again
honk auth gh logout
honk auth gh login

# Or refresh
honk auth gh refresh
```

## Environment Variables

### GitHub

The auth system respects these environment variables:

- `GH_TOKEN` / `GITHUB_TOKEN` - Pre-authenticated token
- `GH_HOST` - Target GitHub hostname
- `GH_ENTERPRISE_TOKEN` - GHE-specific token

### Azure DevOps

- `AZURE_DEVOPS_EXT_PAT` - Pre-authenticated PAT
- `AZURE_DEVOPS_ORG` - Default organization

## Examples

### CI/CD Integration

```bash
# GitHub Actions
- name: Setup Honk Auth
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    honk auth gh status --json

# Azure DevOps Pipelines
- script: |
    export AZURE_DEVOPS_EXT_PAT=$(AZURE_DEVOPS_PAT)
    honk auth az status --json
```

### Automated Scripts

```bash
#!/bin/bash
set -e

# Check auth before running commands
if ! honk auth gh status --json | jq -e '.status == "ok"' > /dev/null; then
  echo "Error: Not authenticated to GitHub"
  echo "Run: honk auth gh login"
  exit 1
fi

# Run your commands
honk watchdog actions analyze --repo myorg/myrepo
```

### Multi-Host Setup

```bash
# Configure for multiple GitHub hosts
cat > ~/.honkrc << EOF
[github]
default_host = github.com

[github.enterprise]
host = github.enterprise.com
scopes = repo,read:org,workflow
EOF
```

## Related Documentation

- [Auth Subsystem Spec](./auth-subsystem-spec.md) - Technical implementation details
- [Azure CLI Auth Reference](./azure-cli-auth.md) - Azure CLI authentication deep dive
- [GitHub CLI Auth Reference](./github-cli-auth.md) - GitHub CLI authentication deep dive
- [Doctor Packs](../spec.md#prereq-engine) - Prerequisite checking system

## Support

For issues or questions:
1. Check `honk auth <provider> --help` for command-specific help
2. Run commands with `--json` flag for detailed error information
3. Check system logs for CLI authentication issues
4. Review GitHub/Azure CLI documentation for upstream auth issues

## API Reference

### Exit Codes

- `0` - Success
- `11` - Authentication required (needs_auth)
- `12` - Token expired
- `50` - Internal error

### Status Values

- `valid` - Authentication working
- `expired` - Token expired, refresh needed
- `missing` - Not authenticated
- `invalid` - Authentication failed or revoked
