# Honk Release Tool - User Guide

## Overview

The `honk release` tool automates the release process for Honk, including version bumping, changelog generation, building, and publishing to PyPI and GitHub.

## Features

- **Semantic Versioning**: Automatic version bumping based on conventional commits
- **Changelog Generation**: AI-powered (with fallback) changelog in Keep a Changelog format
- **Multi-Platform Publishing**: PyPI, GitHub Releases, Homebrew
- **Dry-Run Mode**: Preview changes before committing
- **Flexible Control**: Manual or automatic release type selection

## Quick Start

### Check Current Release Status

```bash
honk release status
```

Shows:
- Current version
- Commits since last release
- Recommended release type
- Breaking changes detected

### Preview Next Release

```bash
honk release preview
```

Shows what the next release would look like without making changes:
- New version number
- Generated changelog
- Files that would be changed

### Create a Release

**Patch Release** (bug fixes):
```bash
honk release patch
```

**Minor Release** (new features):
```bash
honk release minor
```

**Major Release** (breaking changes):
```bash
honk release major
```

**Automatic** (let tool decide based on commits):
```bash
honk release auto
```

## Configuration

Add to `pyproject.toml`:

```toml
[tool.honk.release]
# Enable AI changelog generation (requires GitHub Copilot CLI)
ai_enabled = true

# Changelog file path
changelog_file = "CHANGELOG.md"

# Auto-push after release
auto_push = false

# PyPI repository (pypi or testpypi)
pypi_repository = "pypi"

# Create GitHub release
github_release = true

# GitHub release as draft
github_draft = false
```

## Workflow

### Standard Release Process

1. **Ensure clean working tree**:
   ```bash
   git status
   ```

2. **Check what would be released**:
   ```bash
   honk release preview
   ```

3. **Create release**:
   ```bash
   honk release patch  # or minor/major
   ```

4. **Review changes**:
   ```bash
   git log -1
   git show HEAD
   ```

5. **Push**:
   ```bash
   git push origin main --tags
   ```

### What Happens During Release

1. **Pre-flight checks**:
   - Verifies working tree is clean
   - Checks for commits since last tag
   - Analyzes conventional commits

2. **Version bump**:
   - Updates `pyproject.toml`
   - Updates any `__version__` variables
   - Follows semantic versioning

3. **Changelog generation**:
   - AI-powered (if enabled and available)
   - Fallback to conventional commit parser
   - Groups by type (Added, Fixed, etc.)
   - Highlights breaking changes

4. **Commit and tag**:
   - Commits version changes
   - Creates annotated git tag (v{version})
   - Includes changelog in tag message

5. **Build** (if enabled):
   - Builds Python wheel and sdist
   - Generates Homebrew formula
   - Calculates checksums

6. **Publish** (if enabled):
   - Publishes to PyPI
   - Creates GitHub release
   - Attaches build artifacts

## Conventional Commits

The tool analyzes commit messages to determine release type:

### Commit Types

- `feat:` → Minor version bump (new feature)
- `fix:` → Patch version bump (bug fix)
- `feat!:` or `BREAKING CHANGE:` → Major version bump
- `perf:`, `refactor:`, `docs:` → Patch bump

### Examples

**Feature** (0.1.0 → 0.2.0):
```
feat(auth): add JWT token refresh

Implements automatic token refresh when expired.
```

**Bug fix** (0.1.0 → 0.1.1):
```
fix(api): handle network timeout gracefully

Added retry logic for transient failures.
```

**Breaking change** (0.1.0 → 1.0.0):
```
feat(api)!: redesign authentication API

BREAKING CHANGE: Auth tokens now use OAuth2 format.
Users must re-authenticate.
```

## Advanced Usage

### Dry Run

Test the release process without making changes:

```bash
honk release patch --dry-run
```

### Manual Release Type

Override automatic detection:

```bash
honk release major  # Force major release
```

### Skip Steps

```bash
honk release patch --no-build      # Don't build artifacts
honk release patch --no-publish    # Don't publish to PyPI
honk release patch --no-github     # Don't create GitHub release
```

### AI Changelog

Enable/disable AI changelog generation:

```bash
honk release patch --ai            # Use AI
honk release patch --no-ai         # Use conventional parser only
```

## Troubleshooting

### "Working tree is not clean"

Commit or stash your changes:
```bash
git status
git add . && git commit -m "chore: prepare for release"
```

### "No commits since last release"

Nothing to release. Make some commits first.

### "PYPI_TOKEN not set"

Set PyPI token:
```bash
export PYPI_TOKEN="pypi-..."
```

Or add to `.env` file (not committed):
```bash
PYPI_TOKEN=pypi-...
```

### "GitHub CLI not authenticated"

Authenticate with GitHub:
```bash
gh auth login
```

### AI Changelog Not Working

1. Check Copilot CLI is installed:
   ```bash
   copilot --version
   ```

2. Install if needed:
   ```bash
   gh extension install github/gh-copilot
   ```

3. Or disable AI:
   ```bash
   honk release patch --no-ai
   ```

## Examples

### First Release

```bash
# Check status
honk release status
# Output: "No previous releases found"

# Create initial release
honk release minor
# Output: "Created release v0.1.0"
```

### Bug Fix Release

```bash
# After committing fixes
git log --oneline -3
# fix: resolve memory leak
# fix: correct validation logic
# fix: update dependencies

# Preview
honk release preview
# Output: "Recommended: PATCH (0.1.0 → 0.1.1)"

# Release
honk release patch
```

### Feature Release

```bash
# After adding features
git log --oneline -5
# feat: add export functionality
# feat: implement search
# fix: minor UI tweaks

# Release
honk release minor  # 0.1.1 → 0.2.0
```

### Breaking Change Release

```bash
# After breaking API changes
git log --oneline -2
# feat!: redesign CLI interface
# BREAKING CHANGE: ...

# Preview shows MAJOR recommended
honk release preview

# Release
honk release major  # 0.2.0 → 1.0.0
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      release_type:
        description: 'Release type'
        required: true
        type: choice
        options:
          - patch
          - minor
          - major

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full history for release
      
      - uses: astral-sh/setup-uv@v1
      
      - name: Create Release
        env:
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          uv run honk release ${{ inputs.release_type }}
          git push origin main --tags
```

## Best Practices

1. **Use conventional commits** - Makes versioning automatic
2. **Review preview first** - Always check `honk release preview`
3. **Test after release** - Verify the released package works
4. **Update docs** - Keep release guide current
5. **Announce releases** - Communicate changes to users

## See Also

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Release Tool Specification](./release-tool-spec.md)
