# Main Work Tracking

> **📋 This is the main work tracking document for this project.**
> 
> Use this file to track tasks, progress, decisions, and next steps.

## Current Status (Updated: 2025-11-18)

- ✅ **Core CLI infrastructure** is complete and working:
  - uv-managed environment with all dependencies
  - Typer CLI skeleton with result envelope
  - Doctor engine with `global` pack
  - `honk demo hello` command fully implemented
  - CLI design system with Rich theme (6 semantic tokens)
  - **93 tests passing** (2 skipped)
  - Lint and type checking passing

- ✅ **Auth subsystem** fully implemented:
  - GitHub auth: `honk auth gh {status,login,refresh,logout}`
  - Azure DevOps auth: `honk auth az {status,login,refresh,logout}`
  - Doctor packs for auth prerequisite checking
  - 28 auth-related tests passing

- ✅ **Watchdog PTY tool** fully implemented:
  - `honk watchdog pty {show,clean,watch}` commands
  - PTY leak detection and cleanup
  - 20 watchdog tests passing
  - Spec available in `docs/references/watchdog-pty-spec.md`

- ✅ **Release tool** fully implemented (NEW - 2025-11-18):
  - Semantic versioning with automatic bump detection
  - Conventional commit parser and analyzer
  - Changelog generation (traditional + AI-ready)
  - Build system (PyPI packages, Homebrew formulae)
  - Publishing (PyPI, GitHub Releases)
  - CLI commands: `honk release {status,preview,patch,minor,major}`
  - **34 tests passing** for release module
  - Comprehensive documentation (user guide + technical spec)
  - See: `docs/references/release-tool-guide.md`

- **Next milestone**: GitHub Actions workflows, polish release tool AI integration

## Active Tasks

- [x] Stand up uv-managed Python environment + `noxfile.py` sessions.
- [x] Implement Typer CLI skeleton with result envelope + `honk introspect --json`.
- [x] Build doctor engine with the `global` pack and hook it into commands.
- [x] Ship `honk demo hello` (doctor + greeting + Rich help text).
- [x] Implement CLI design system (semantic tokens + Rich theme).
- [x] Complete auth subsystem (GitHub + Azure DevOps).
- [x] Implement watchdog PTY tool with tests.
- [x] Implement release automation tool (2025-11-18).
- [ ] Polish release tool AI integration (Copilot CLI).
- [ ] Configure GitHub Actions workflows (`ci-core`, `ci-macos`, `docs-guard`, `release`).

## Completed Tasks

- [x] Bootstrap AI-oriented project structure
- [x] Refresh spec for demo-first roadmap (uv pins, Typer help pattern, CI plan)
- [x] Fix Typer/Click dependency incompatibility (pinned Click <8.2.0 for Typer 0.11.x)
- [x] Implement CLI design system (2025-11-18)
- [x] Complete auth subsystem - GitHub commands (2025-11-18)
- [x] Complete auth subsystem - Azure DevOps commands (2025-11-18)
- [x] Implement auth doctor packs (2025-11-18)
- [x] Add comprehensive auth tests (2025-11-18)
- [x] Implement watchdog PTY tool (2025-11-18)
- [x] Add comprehensive watchdog tests (2025-11-18)
- [x] **Implement release automation tool** (2025-11-18):
  - [x] Module structure and Git operations
  - [x] Conventional commit parser and analyzer
  - [x] Version bumper with semantic versioning
  - [x] CLI commands (status, preview, patch, minor, major)
  - [x] Changelog generators (traditional + AI-ready)
  - [x] Workflow orchestrator
  - [x] PyPI builder and publisher
  - [x] GitHub Releases publisher
  - [x] Homebrew formula generator
  - [x] Configuration system
  - [x] 34 comprehensive tests
  - [x] User guide and technical spec documentation

## Next Steps

1. **Test and polish release tool**:
   - Manual testing of `honk release` commands
   - Complete AI integration (Copilot CLI)
   - Add doctor pack for release prerequisites
   - Test PyPI and GitHub publishing workflows

2. **Configure GitHub Actions workflows**:
   - `ci-core` - Main test suite
   - `ci-macos` - Platform-specific tests
   - `docs-guard` - Documentation validation
   - `release` - Automated releases using `honk release`

3. **Additional enhancements**:
   - Consider additional watchdog tools (GitHub Actions analyzer, resource monitors)
   - Document usage patterns and examples for auth and watchdog tools
   - Add release tool to CI/CD pipeline

## Planned Tasks

### Auth Subsystem Implementation (Tasks 3-6)

**Started**: 2025-11-18 11:49 AM
**Completed**: 2025-11-18 (implementation complete, pending test verification)
**Assignee**: current agent
**Status**: ✅ Implementation Complete (Tests Pending Verification)

**Task 3**: ✅ Complete auth subsystem - implement status, login, refresh, logout commands for GitHub
- Status: Complete
- Implementation:
  - Created `GitHubAuthProvider` class in `src/honk/auth/providers/github.py`
  - Implemented status, login, refresh, logout methods
  - CLI commands in `src/honk/auth/cli.py` (gh_status, gh_login, gh_refresh, gh_logout)
  - Integrated with main CLI via `honk auth gh <command>`
  - Full result envelope support with facts and next steps
  - Tests in `tests/test_auth_github.py` (10 tests covering all scenarios)

**Task 4**: ✅ Complete auth subsystem - implement status, login, refresh, logout commands for Azure DevOps
- Status: Complete
- Implementation:
  - Created `AzureAuthProvider` class in `src/honk/auth/providers/azure.py`
  - Implemented status, login, refresh (guidance), logout methods
  - CLI commands in `src/honk/auth/cli.py` (az_status, az_login, az_refresh, az_logout)
  - Integrated with main CLI via `honk auth az <command>`
  - Full result envelope support with facts and next steps
  - Tests in `tests/test_auth_azure.py` (4 tests covering key scenarios)

**Task 5**: ✅ Implement auth doctor packs (auth-gh, auth-az) for prerequisite checking
- Status: Complete
- Implementation:
  - Created `src/honk/auth/doctor.py` with pack factories
  - `create_github_auth_pack(scopes, hostname)` - validates auth + scopes
  - `create_azure_auth_pack(org)` - validates Azure + DevOps PAT
  - Packs follow standard DoctorPack pattern with CheckResult
  - Tests in `tests/test_auth_doctor.py` (8 tests covering pack behavior)

**Task 6**: ✅ Add comprehensive auth subsystem tests (unit + integration)
- Status: Complete
- Implementation:
  - Unit tests: `test_auth_github.py`, `test_auth_azure.py`, `test_auth_doctor.py`
  - Integration tests: `test_auth_integration.py` (full workflows + envelope contract)
  - Total: 26 new auth tests created
  - All tests use proper mocking (subprocess.run) at correct patch locations
  - Tests cover: authentication flows, error cases, result envelopes, doctor packs

**Files Created:**
- `src/honk/auth/providers/github.py` (316 lines)
- `src/honk/auth/providers/azure.py` (303 lines)
- `src/honk/auth/cli.py` (376 lines - GitHub + Azure commands)
- `src/honk/auth/doctor.py` (159 lines)
- `tests/test_auth_github.py` (184 lines, 10 tests)
- `tests/test_auth_azure.py` (143 lines, 4 tests)
- `tests/test_auth_doctor.py` (187 lines, 8 tests)
- `tests/test_auth_integration.py` (250 lines, 4 test classes)

**Files Modified:**
- `src/honk/cli.py` - Integrated auth sub-apps
- `src/honk/auth/__init__.py` - Exported new components
- `src/honk/auth/providers/__init__.py` - Exported provider classes

**Next Steps:**
- Run full test suite to verify all tests pass
- Update `docs/spec.md` with auth subsystem implementation status
- Consider adding example usage to README

### CLI Design System Implementation

**Goal:** Standardize colors, styles, and status messages across all CLI commands for consistency, accessibility, and maintainability.

**Research Completed:** 2025-11-18 (Deep Dive mode, 12 web searches, 2 hours)
- **Quality Score:** Research 9/10, Solution 10/10
- **Deliverables:** 5 comprehensive documents in `tmp/`
  - `DESIGN_SYSTEM_SUMMARY.md` - Executive summary
  - `cli_design_system_guide.md` - Complete implementation guide (736 lines)
  - `example_theme_implementation.py` - Copy-paste ready code
  - `design_system_architecture.txt` - Visual diagrams
  - `README_RESEARCH.md` - Research index

**Recommendation:** Use Rich's Theme class with 6 semantic tokens (Option A - Simple)
- Already have dependency: Rich 13.7.1
- Industry standard: GitHub CLI, Heroku CLI, AWS CLI all use semantic tokens
- Implementation time: 2-3 hours total
- Single file: `src/honk/ui/theme.py` (~80 lines)

**Semantic Tokens (6 core):**
```python
{
    "success": "bold green",   # ✓ Completions, positive outcomes
    "error": "bold red",       # ✗ Failures, blocking issues
    "warning": "bold yellow",  # ⚠ Cautions, alerts
    "info": "dim cyan",        # ℹ Neutral information
    "dim": "dim white",        # Secondary, metadata
    "emphasis": "bold",        # Important text
}
```

**Implementation Plan:**

**Phase 1: Setup (30 min)**
- [ ] Create `src/honk/ui/` directory
- [ ] Copy `tmp/example_theme_implementation.py` → `src/honk/ui/theme.py`
- [ ] Remove demo code from bottom of theme.py
- [ ] Create `src/honk/ui/__init__.py` with exports:
  ```python
  from .theme import (
      console,
      print_success,
      print_error,
      print_warning,
      print_info,
      print_dim,
      print_kv,
      print_code,
  )
  ```
- [ ] Test: `uv run python -c "from honk.ui import print_success; print_success('Test')"`

**Phase 2: Migration (1-2 hrs)**
- [ ] Update `src/honk/cli.py`:
  - Replace hardcoded status prints with design system helpers
  - Update `doctor` command output formatting
  - Update `version`, `info` commands
- [ ] Update `src/honk/demo/hello.py`:
  - Use `print_info()`, `print_dim()` for output
  - Use `console` for Rich formatting
- [ ] Update `src/honk/internal/doctor/`:
  - Use semantic tokens for pack result output
  - Replace hardcoded ✓/✗ with helper functions
- [ ] Update `src/honk/auth/`:
  - When implemented, use design system from start
- [ ] Visual test all commands:
  ```bash
  uv run honk version
  uv run honk info
  uv run honk doctor
  uv run honk demo hello
  uv run honk introspect
  ```

**Phase 3: Documentation (30 min)**
- [ ] Add design system section to `docs/spec.md`:
  - Reference token definitions
  - Document usage guidelines
  - Link to theme.py as source of truth
- [ ] Update `docs/agents.md`:
  - Add usage guidelines: "Always use `from honk.ui import print_success` not hardcoded colors"
  - Document semantic token names and purposes
  - Add "do's and don'ts" from research guide
- [ ] Update README.md (if applicable):
  - Brief mention of design system approach

**Success Criteria:**
- ✅ All commands use semantic tokens (no hardcoded colors)
- ✅ Consistent icon usage (✓ success, ✗ error, ⚠ warning, ℹ info)
- ✅ Single source of truth (`src/honk/ui/theme.py`)
- ✅ All tests still passing
- ✅ Visual output looks professional and consistent
- ✅ Accessible (color + icons, not color-only)

**Benefits:**
- Consistency across all commands
- Easy to change colors/styles globally
- Accessible by default (icons + colors)
- Self-documenting code (semantic names)
- Professional appearance
- Faster to add new commands

**Future Enhancements (Optional):**
- Support for `--no-color` flag (detect NO_COLOR env var)
- Theme switching (dark/light) if needed
- Additional tokens as needed (currently 6 covers 90% of use cases)
- Upgrade to Option B (Enhanced Theme with dataclasses) if complexity grows

**Research Files Location:**
- All research artifacts saved in `tmp/` directory
- Review `tmp/DESIGN_SYSTEM_SUMMARY.md` for quick reference
- See `tmp/cli_design_system_guide.md` for comprehensive details

**Time Estimate:** 2-3 hours (30m setup + 1-2hr migration + 30m docs)

---

## Decisions & Notes

### 2025-11-18 - CLI Design System Implementation

- ✅ **Implemented** Rich Theme-based design system with 6 semantic tokens (Option A - Simple).
- Created `src/honk/ui/theme.py` with semantic tokens: success, error, warning, info, dim, emphasis
- Helper functions with accessibility-first design (icons + colors): ✓, ✗, ⚠, ℹ
- Integrated NO_COLOR support for test compatibility and accessibility
- Migrated cli.py commands (version, info, introspect, doctor) to use design system
- Updated tests to handle color output properly
- **Result:** All 46 tests passing, lint clean, type checking clean
- **Benefits:** Consistent output across commands, single source of truth, accessible by default
- **Research artifacts:** Saved in `tmp/` for reference (implementation guide, examples, visual diagrams)

### 2025-11-18 - Typer/Click compatibility fix

- Resolved `TypeError: Parameter.make_metavar() missing 1 required positional argument: 'ctx'` by pinning Click to `>=8.0.0,<8.2.0`.
- Typer 0.11.x is incompatible with Click 8.2+ due to breaking changes in Click's parameter handling.
- Added explicit Click dependency constraint to `pyproject.toml` to prevent future issues.
- Fixed `typer.Argument(...)` usage in `help-json` command to remove ellipsis (`...`) for Typer 0.11 compatibility.
- Fixed introspect command's `--json/--no-json` default value (changed True → False to avoid "Secondary flag" error).

### 2025-11-17 - Auth subsystem spec

- Captured standalone design in `docs/spec-auth.md` covering GitHub (`gh`) and Azure DevOps (`az devops`) flows, storage, expiry warnings, and CLI UX.
- Documented metadata schema, doctor pack hooks, and new dependencies (`python-dateutil`, `pendulum`, `tenacity`).

### 2025-11-17 - CLI auth research artifacts

- Added dedicated references (`docs/references/azure-cli-auth.md`, `docs/references/github-cli-auth.md`) summarizing token flows, PAT usage, and troubleshooting for `az` + `gh`.
- Registered specialist agents (“Azure CLI Auth Agent”, “GitHub CLI Auth Agent”) inside `docs/agents.md` so future assistants can answer deeply on those CLIs.

### 2025-11-17 - Demo-first spec refresh

- Locked toolchain on Python 3.12.2 + uv 0.4.20; `uv run` is the canonical execution path.
- Typer's auto-generated `--help` / `--help-json` output is the only required “man page” for each command; Rich formatting stays enabled.
- First deliverable is `honk demo hello`; historical ios-runner work is postponed.
- CI focuses on lint/type/test plus sanity runs of `honk introspect --json` and `honk demo hello` (no dedicated nox contract step yet).

## Blockers & Issues

- None currently.

## Resources & References

- See `docs/references/` for detailed documentation
- See `docs/agents.md` for AI agent configuration
