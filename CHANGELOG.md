# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Homebrew formula for installation
- PyPI package publication
- Additional watchdog tools (GitHub Actions analyzer)
- More authentication providers (GitLab, Bitbucket)

## [0.1.0] - 2025-11-18

### Added
- **Core CLI Infrastructure**
  - Typer-based CLI with Rich formatting
  - Result envelope pattern for all commands
  - `--json` flag for machine-readable output
  - `--plan` flag for dry-run operations
  - `--no-color` flag for accessibility
  - Exit codes: 0 (ok), 10 (prereq_failed), 11 (needs_auth), 12 (token_expired), 20 (network), 30 (system), 50 (bug), 60 (rate_limited)

- **Authentication Subsystem**
  - `honk auth gh` - GitHub authentication via gh CLI
    - `status` - Check authentication status
    - `login` - OAuth flow with scope management
    - `refresh` - Add/update scopes
    - `logout` - Remove authentication
  - `honk auth az` - Azure DevOps authentication via az CLI
    - `status` - Check authentication status
    - `login` - Device code flow
    - `refresh` - PAT rotation guidance
    - `logout` - Remove authentication
  - System keychain integration for secure token storage
  - Support for GitHub Enterprise
  - Scope validation and management

- **Doctor Pack System**
  - `global` pack - OS, disk, network, tmp directory checks
  - `auth-gh[scopes]` - GitHub authentication and scope validation
  - `auth-az[org]` - Azure DevOps authentication validation
  - Prerequisite checking before command execution
  - Remediation step generation

- **Watchdog PTY Tool**
  - `honk watchdog pty show` - Display PTY usage and detect leaks
  - `honk watchdog pty clean` - Kill processes with orphaned PTYs
  - `honk watchdog pty watch` - Continuous monitoring with auto-cleanup
  - Leak detection heuristics for Copilot agents and Node.js processes
  - Safe defaults with plan mode preview

- **System Commands**
  - `honk demo hello` - Example command demonstrating the stack
  - `honk doctor` - Run prerequisite checks
  - `honk introspect --json` - Command catalog with metadata
  - `honk version` - Version information
  - `honk info` - System information
  - `honk help-json` - Machine-readable help

- **CLI Design System**
  - 6 semantic tokens (success, error, warning, info, dim, emphasis)
  - Consistent Rich theme across all commands
  - Proper color contrast and accessibility support

- **Testing Infrastructure**
  - 93 passing tests (2 skipped)
  - Unit tests for all components
  - Integration tests for CLI commands
  - Contract tests for JSON schemas
  - Mock-based testing for external dependencies

- **CI/CD Workflows**
  - `ci-core` - Linux testing, linting, type checking
  - `ci-macos` - macOS compatibility testing
  - `docs-guard` - Documentation organization enforcement
  - `release` - Automated releases on version tags
  - `schema-validation` - JSON schema validation

- **Documentation**
  - Comprehensive user guides
    - Authentication User Guide (8.5KB)
    - Watchdog PTY User Guide (11.7KB)
    - Security Guide (12.5KB)
    - Versioning Strategy (13.3KB)
  - Technical specifications
    - Auth Subsystem Spec
    - Watchdog PTY Spec
    - Design System Spec
  - Reference documentation
    - GitHub CLI Auth Reference
    - Azure CLI Auth Reference
  - Project plans and tracking

- **JSON Schemas**
  - Result envelope schema (v1.0)
  - Introspection schema (v1.0)
  - Contract validation in CI

### Security
- Secure token storage via system keychain (Keychain Access, libsecret, Windows Credential Manager)
- No plaintext tokens in code or logs
- Secure credential workflows
- Token rotation support
- Scope management and least privilege
- CI/CD secret management patterns

### Dependencies
- Python 3.12.2+
- uv 0.4.20 for dependency management
- Typer 0.12.3 for CLI framework
- Rich 13.7.1 for terminal formatting
- Pydantic 2.8.2 for data validation
- keyring 24.3.1 for credential storage
- pytest 8.3.3 for testing

### Notes
- This is the initial release (0.1.0)
- API is not yet stable (0.x series)
- Breaking changes may occur in minor versions
- See versioning-strategy.md for details

[Unreleased]: https://github.com/org/honk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/org/honk/releases/tag/v0.1.0
