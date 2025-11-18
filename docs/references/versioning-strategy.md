# Honk Versioning Strategy

## Overview

This document defines the versioning strategy for Honk CLI, including CLI versions, schema versions, release processes, and backwards compatibility guarantees.

## Version Components

Honk has multiple versioned components:

1. **CLI Version** - The `honk` command line tool itself
2. **Result Schema Version** - The result envelope format
3. **Introspection Schema Version** - The command catalog format
4. **Python Package Version** - PyPI distribution version

## CLI Versioning

### Semantic Versioning

Honk follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

- **MAJOR** - Breaking changes to CLI interface or behavior
- **MINOR** - New features, backwards compatible
- **PATCH** - Bug fixes, backwards compatible

### Current Version

```bash
honk version
# Output: honk version 0.1.0
```

**Version:** `0.1.0`
- Major: 0 (pre-1.0, API not stable)
- Minor: 1 (initial release)
- Patch: 0 (no patches yet)

### Pre-1.0 Versioning

During the 0.x series:
- **0.y.0** - May include breaking changes
- **0.y.z** - Bug fixes and minor features
- Expect API instability
- Breaking changes documented in CHANGELOG

### Path to 1.0

**Criteria for 1.0.0 release:**
- [ ] API stability proven in production
- [ ] Complete test coverage (>90%)
- [ ] All core tools implemented
- [ ] Documentation complete
- [ ] At least 3 months of 0.x usage
- [ ] No known critical bugs
- [ ] Backwards compatibility plan

**Target:** Q2 2025

### Version Locations

Version is defined in multiple places (kept in sync):

```python
# src/honk/__init__.py
__version__ = "0.1.0"

# pyproject.toml
[project]
version = "0.1.0"

# CLI output
honk version
honk --version
```

## Schema Versioning

### Result Envelope Schema

**Current Version:** `1.0`

Schema file: `schemas/result.v1.json`

**Versioning Policy:**
- Schema version independent of CLI version
- Major version bump for breaking changes
- Schema version in envelope: `"version": "1.0"`

**Breaking Changes:**
- Removing required fields
- Changing field types
- Changing field semantics
- Removing enum values

**Non-Breaking Changes:**
- Adding optional fields
- Adding new enum values
- Relaxing validation rules
- Adding new top-level keys

**Evolution Path:**
```
v1.0 → v1.1 → v2.0 → v2.1 → v3.0
```

**Deprecation Process:**
1. Announce deprecation in v1.0
2. Support v1.0 and v2.0 simultaneously
3. Remove v1.0 support after 6 months
4. Document migration in CHANGELOG

### Introspection Schema

**Current Version:** `1.0`

Schema file: `schemas/introspect.v1.json`

**Same versioning policy as result envelope**

## Release Process

### Version Bump Process

```bash
# 1. Determine version bump type
# Bug fix: 0.1.0 → 0.1.1
# New feature: 0.1.0 → 0.2.0
# Breaking change: 0.1.0 → 0.2.0 (or 1.0.0 if stable)

# 2. Update version in code
vim src/honk/__init__.py
# Update __version__ = "0.2.0"

vim pyproject.toml
# Update version = "0.2.0"

# 3. Update CHANGELOG
vim CHANGELOG.md
# Add entry for 0.2.0

# 4. Commit changes
git add src/honk/__init__.py pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"

# 5. Create and push tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags

# 6. GitHub Actions automatically creates release
```

### Release Tags

Format: `v{MAJOR}.{MINOR}.{PATCH}`

Examples:
- `v0.1.0` - Initial release
- `v0.2.0` - New features
- `v0.2.1` - Bug fix
- `v1.0.0` - Stable API

### Release Workflow

Automated via `.github/workflows/release.yml`:

```yaml
on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-publish:
    # 1. Run tests
    # 2. Build package
    # 3. Publish to PyPI
    # 4. Create GitHub Release
```

### Release Artifacts

Each release includes:
1. **PyPI package** - `honk-{version}.tar.gz`
2. **GitHub Release** - Notes from CHANGELOG
3. **Release notes** - Auto-generated from commits
4. **Assets** - Checksums, signatures

## CHANGELOG Format

Following [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Changes to existing features

### Deprecated
- Features marked for removal

### Removed
- Features removed in this release

### Fixed
- Bug fixes

### Security
- Security improvements

## [0.2.0] - 2025-12-01

### Added
- New `honk watchdog actions` command
- Support for GitHub Enterprise

### Changed
- Improved PTY leak detection heuristics

### Fixed
- Azure DevOps auth token refresh issue

## [0.1.0] - 2025-11-18

### Added
- Initial release
- `honk auth gh/az` commands
- `honk watchdog pty` tool
- `honk demo hello` command
- Doctor pack system
- Result envelope pattern
```

## Backwards Compatibility

### CLI Compatibility Guarantees

**Post-1.0:**
- Command paths won't change (`honk auth gh status` stays)
- Required arguments won't change
- Output format won't break (with `--json`)
- Exit codes won't change meaning
- Schema versions stay supported

**Pre-1.0 (0.x):**
- Minor breaking changes allowed
- Always documented in CHANGELOG
- Migration guide provided
- Deprecation warnings where possible

### Schema Compatibility

**Guarantees:**
- Parsers written for v1.0 work with v1.1, v1.2, etc.
- New fields are always optional
- Enum values never removed without deprecation
- Field types never change

**Non-Guarantees:**
- New commands may appear in introspection
- New exit codes may be added
- Doctor packs may add new checks
- Performance characteristics

### Deprecation Policy

**Process:**
1. **Announce** - Document in CHANGELOG, add warnings
2. **Deprecation Period** - Minimum 6 months (post-1.0)
3. **Removal** - Only in major version bump

**Example:**
```bash
# v1.5.0 - Deprecation announced
honk old-command
# Warning: 'old-command' is deprecated. Use 'new-command' instead.
# Will be removed in v2.0.0

# v1.6.0 - Still works with warning
# v1.7.0 - Still works with warning

# v2.0.0 - Removed
honk old-command
# Error: Unknown command 'old-command'
# Did you mean 'new-command'?
```

## Version Compatibility Matrix

### CLI Versions

| CLI Version | Result Schema | Introspect Schema | Python | Notes |
|-------------|---------------|-------------------|--------|-------|
| 0.1.0       | 1.0           | 1.0               | 3.12+  | Initial release |
| 0.2.0       | 1.0           | 1.0               | 3.12+  | Planned |
| 1.0.0       | 1.0, 2.0      | 1.0, 2.0          | 3.12+  | Stable API |

### Python Version Support

**Current:** Python 3.12.2+

**Policy:**
- Support latest stable Python
- Support Python versions released in last 2 years
- Drop support in major CLI version only
- Announce 6 months before dropping

**Timeline:**
```
2024: Python 3.12+
2025: Python 3.12+, 3.13+
2026: Python 3.13+, 3.14+
```

## Upgrade Paths

### Upgrading CLI

**From 0.1.x to 0.2.x:**
```bash
# Via pip
pip install --upgrade honk

# Via uv
uv pip install --upgrade honk

# Via Homebrew (when available)
brew upgrade honk
```

**Checking compatibility:**
```bash
# Check current version
honk version

# Check schema compatibility
honk introspect --json | jq '.version'

# Validate output works
honk demo hello --json | jq '.'
```

### Schema Migration

**Result Envelope v1 to v2:**
```python
# Parser for v1 and v2
def parse_result(data: dict):
    version = data["version"]
    
    if version.startswith("1."):
        # Handle v1 schema
        return parse_v1(data)
    elif version.startswith("2."):
        # Handle v2 schema
        return parse_v2(data)
    else:
        raise ValueError(f"Unsupported schema version: {version}")
```

**Introspection v1 to v2:**
```python
# Feature detection instead of version checking
def get_command_info(introspect_data: dict):
    # Check for presence of fields, not version
    if "description" in introspect_data["commands"][0]:
        # v1 or v2
        return introspect_data["commands"]
    else:
        # Very old version
        raise ValueError("Unsupported introspection format")
```

## Version Discovery

### Programmatic Access

**Python:**
```python
import honk
print(honk.__version__)  # "0.1.0"
```

**CLI:**
```bash
honk version
honk version --json | jq -r '.facts.honk_version'
honk --version  # Short form
```

**Result Envelope:**
```bash
honk demo hello --json | jq -r '.version'  # "1.0"
```

**Introspection:**
```bash
honk introspect --json | jq -r '.version'  # "1.0"
```

### Runtime Version Checks

**In automation scripts:**
```bash
#!/bin/bash
REQUIRED_VERSION="0.1.0"
CURRENT_VERSION=$(honk version --json | jq -r '.facts.honk_version')

if [ "$CURRENT_VERSION" != "$REQUIRED_VERSION" ]; then
    echo "Error: Requires honk $REQUIRED_VERSION, found $CURRENT_VERSION"
    exit 1
fi
```

**In Python:**
```python
import subprocess
import json

def check_honk_version(required: str) -> bool:
    result = subprocess.run(
        ["honk", "version", "--json"],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    return data["facts"]["honk_version"] == required
```

## Testing Strategy

### Version Compatibility Tests

**Contract tests:**
```python
def test_version_in_result_envelope():
    """All result envelopes must include version."""
    result = run_command(["honk", "demo", "hello", "--json"])
    data = json.loads(result.stdout)
    assert "version" in data
    assert data["version"] == "1.0"

def test_version_command():
    """Version command works."""
    result = run_command(["honk", "version"])
    assert result.returncode == 0
    assert "0.1.0" in result.stdout
```

**Schema validation tests:**
```python
def test_schema_version_matches():
    """Schema version in code matches file."""
    schema = json.load(open("schemas/result.v1.json"))
    # Validate schema is internally consistent
    assert "$schema" in schema
```

### Upgrade Tests

**Test upgrade paths:**
```bash
# Install old version
pip install honk==0.1.0

# Verify it works
honk version

# Upgrade
pip install --upgrade honk

# Verify upgrade
honk version
honk doctor --json  # Should still work
```

## Release Checklist

**Pre-release:**
- [ ] All tests passing
- [ ] Lint and type checks clean
- [ ] Version bumped in all locations
- [ ] CHANGELOG updated
- [ ] Documentation reviewed
- [ ] Breaking changes documented
- [ ] Migration guide written (if needed)
- [ ] Security audit completed
- [ ] Performance regression tested

**Release:**
- [ ] Tag created and pushed
- [ ] CI/CD build passes
- [ ] PyPI package published
- [ ] GitHub release created
- [ ] Release notes published
- [ ] Documentation site updated

**Post-release:**
- [ ] Announcement posted
- [ ] Homebrew formula updated (when available)
- [ ] Docker image updated (if applicable)
- [ ] Examples updated
- [ ] Monitor for issues

## Version Communication

### Release Announcements

**Channels:**
1. GitHub Releases
2. CHANGELOG.md
3. Project README
4. (Future) Project website
5. (Future) Mailing list
6. (Future) Twitter/social media

**Announcement Template:**
```markdown
# Honk v0.2.0 Released

We're excited to announce Honk v0.2.0!

## What's New
- New watchdog actions analyzer
- Improved PTY leak detection
- GitHub Enterprise support

## Breaking Changes
- None

## Bug Fixes
- Fixed Azure DevOps token refresh
- Improved error messages

## Upgrade
pip install --upgrade honk

## Documentation
https://github.com/org/honk/releases/tag/v0.2.0
```

### Version Support Policy

**Active Support:**
- Latest major version (e.g., 1.x)
- Latest minor version of previous major (e.g., 0.9.x when on 1.x)

**Security Updates:**
- Latest major version gets all updates
- Previous major version gets security fixes only
- Support period: 12 months after new major release

**End of Life:**
- Announced 6 months in advance
- Security fixes stop
- No new features
- Encourage upgrade

## Future Considerations

### Schema Evolution

**Planned v2.0 features:**
- Structured error details
- Nested command context
- Performance metrics
- Telemetry hooks

**Backwards compatibility plan:**
```python
# Emit both v1 and v2
honk demo hello --json --schema-version 1  # v1 format
honk demo hello --json --schema-version 2  # v2 format
honk demo hello --json                      # Default (v2)
```

### Distribution Channels

**Current:**
- PyPI (planned)
- Git repository

**Future:**
- Homebrew
- Apt/Yum repositories
- Docker Hub
- Snap/Flatpak
- Windows installer

### Long-Term Support (LTS)

**Post-1.0 plan:**
- LTS versions every 12 months
- Support for 24 months
- Security fixes only after 12 months
- Example: 1.0 LTS, 2.0 LTS, 3.0 LTS

## Related Documentation

- [Release Workflow](.github/workflows/release.yml)
- [CHANGELOG](../../CHANGELOG.md)
- [Contributing Guide](../../CONTRIBUTING.md) (when created)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

## Questions?

For version-related questions:
1. Check CHANGELOG for release notes
2. Review GitHub releases
3. Check documentation for migration guides
4. Open issue for version-specific questions
