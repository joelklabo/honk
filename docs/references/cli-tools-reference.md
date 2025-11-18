# CLI Tools Reference

> **Quick reference for external CLI tools used in the Honk project**

## ⚠️ CRITICAL: `gh` vs `copilot` Distinction

**These are two completely separate CLI tools - do NOT confuse them!**

### GitHub CLI (`gh`)

**Purpose:** Official GitHub CLI for repository and API management

**Installation:**
```bash
brew install gh              # macOS
# or
winget install GitHub.cli    # Windows
# or
sudo apt install gh          # Debian/Ubuntu
```

**Common Commands:**
```bash
# Authentication
gh auth login
gh auth status
gh auth logout

# Repositories
gh repo clone owner/repo
gh repo create my-new-repo
gh repo view

# Pull Requests
gh pr list
gh pr create
gh pr view 123
gh pr merge 123

# Issues
gh issue list
gh issue create
gh issue view 456

# GitHub Actions
gh workflow list
gh workflow run workflow.yml
gh run list
```

**Authentication:**
- Manages GitHub API tokens via `gh auth login`
- Stores credentials in keyring/keychain
- Used by Honk's auth subsystem: `honk auth gh status`

**Configuration:**
- Config dir: `~/.config/gh/`
- Hosts file: `~/.config/gh/hosts.yml`

---

### GitHub Copilot CLI (`copilot`)

**Purpose:** AI-powered command-line assistant for suggesting and explaining commands

**Installation:**
```bash
# Separate installation - NOT part of `gh`
npm install -g @githubnext/github-copilot-cli

# OR (if available via other package managers)
brew install github-copilot-cli
```

**Common Commands:**
```bash
# Get AI suggestions for commands
copilot suggest "install git"
copilot suggest "find large files"
copilot suggest "compress directory"

# Get explanations for commands
copilot explain "git rebase -i HEAD~5"
copilot explain "tar -xzvf archive.tar.gz"

# Ask general questions
copilot ask "how do I configure SSH keys?"
```

**Key Differences from `gh`:**
- Standalone CLI tool (NOT `gh copilot`)
- Focuses on AI assistance, not GitHub API operations
- Does NOT manage GitHub repositories/issues/PRs
- Separate authentication from `gh`

---

## Common Mistakes & Corrections

### ❌ Wrong Commands

```bash
# WRONG: Trying to use copilot as gh subcommand
gh copilot suggest "install git"
gh copilot --agent planloop
gh copilot explain

# WRONG: Trying to use gh as copilot subcommand
gh suggest "install git"
```

### ✅ Correct Commands

```bash
# CORRECT: Use copilot standalone
copilot suggest "install git"
copilot explain "ls -la"

# CORRECT: Use gh for GitHub operations
gh auth login
gh pr list
gh issue create
```

---

## When to Use Which Tool

### Use `gh` when you need to:
- Authenticate with GitHub API
- Create/manage repositories
- Work with issues and pull requests
- Manage GitHub Actions workflows
- Clone repositories
- Manage GitHub settings

### Use `copilot` when you need to:
- Get AI suggestions for shell commands
- Explain complex commands
- Ask how to accomplish terminal tasks
- Generate command variations

### Use `honk` (this project) when you need to:
- Manage authentication for multiple services (`honk auth`)
- Monitor system health (`honk watchdog`, `honk system`)
- Automate releases (`honk release`)
- Take AI-assisted notes (`honk notes`)

---

## Integration with Honk

### Honk's Auth System Uses `gh`

Honk wraps the `gh` CLI for GitHub authentication:

```bash
# Honk commands that use gh internally
honk auth gh status          # Calls: gh auth status
honk auth gh login           # Calls: gh auth login
honk auth gh refresh         # Calls: gh auth refresh
honk auth gh logout          # Calls: gh auth logout
```

**Why?** Honk provides a unified interface across multiple auth providers (GitHub, Azure, etc.)

### Honk Does NOT Use `copilot`

The `copilot` CLI is independent and not integrated into Honk's codebase.

If you want AI assistance with Honk commands, use:
- GitHub Copilot extension in your editor
- GitHub Copilot Chat
- Standalone `copilot` CLI (separate from Honk)

---

## Quick Reference Table

| Tool | Command | Purpose | Auth Method | Used by Honk? |
|------|---------|---------|-------------|---------------|
| GitHub CLI | `gh` | GitHub API operations | `gh auth login` | ✅ Yes (auth subsystem) |
| Copilot CLI | `copilot` | AI command assistance | Separate auth | ❌ No (independent) |
| Honk CLI | `honk` | Dev workflow automation | Wraps `gh`/`az` | - (this project) |
| Azure CLI | `az` | Azure API operations | `az login` | ✅ Yes (auth subsystem) |

---

## Further Reading

- **GitHub CLI (`gh`)**: https://cli.github.com/
- **GitHub CLI Manual**: https://cli.github.com/manual/
- **GitHub Copilot CLI**: https://githubnext.com/projects/copilot-cli
- **Honk Auth Reference**: `docs/references/github-cli-auth.md`
