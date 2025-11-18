# Main Work Tracking

> **📋 This is the main work tracking document for this project.**
> 
> Use this file to track tasks, progress, decisions, and next steps.

## Current Status

- ✅ Core CLI infrastructure is complete and working:
  - uv-managed environment with all dependencies
  - Typer CLI skeleton with result envelope
  - Doctor engine with `global` pack
  - `honk demo hello` command fully implemented
  - All 34 tests passing
  - Lint and type checking passing
- Next milestone: Configure GitHub Actions workflows

## Active Tasks

- [x] Stand up uv-managed Python environment + `noxfile.py` sessions.
- [x] Implement Typer CLI skeleton with result envelope + `honk introspect --json`.
- [x] Build doctor engine with the `global` pack and hook it into commands.
- [x] Ship `honk demo hello` (doctor + greeting + Rich help text).
- [ ] Configure GitHub Actions workflows (`ci-core`, `ci-macos`, `docs-guard`, `release`).
- [ ] Implement CLI design system (semantic tokens + Rich theme).

## Completed Tasks

- [x] Bootstrap AI-oriented project structure
- [x] Refresh spec for demo-first roadmap (uv pins, Typer help pattern, CI plan)
- [x] Fix Typer/Click dependency incompatibility (pinned Click <8.2.0 for Typer 0.11.x)

## Next Steps

1. Implement uv environment + baseline nox sessions.
2. Land CLI skeleton + demo command per spec guidance.
3. Wire up CI workflows and verify `honk demo hello --help` runs in automation.

## Planned Tasks

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

### 2025-11-18 - CLI Design System Research

- Conducted comprehensive research on CLI design systems (Deep Dive mode, 2 hours, 12 web searches).
- **Recommendation:** Implement Rich Theme-based design system with 6 semantic tokens (Option A - Simple).
- **Industry Validation:**
  - GitHub CLI: Uses semantic tokens + Primer design system
  - Heroku CLI: Minimal palette with strict style guide
  - AWS CLI: Structured, consistent output patterns
  - All leading CLIs follow semantic token pattern
- **Key Principles:**
  - Semantic tokens (error, warning, success, info) not raw colors
  - Icons + colors for accessibility (not color-only)
  - Single source of truth (`src/honk/ui/theme.py`)
  - Helper functions for consistent usage
- **Implementation:** 2-3 hours (already have Rich 13.7.1, ~80 lines of code)
- **Deliverables:** 5 comprehensive documents saved in `tmp/` for reference:
  - Executive summary, implementation guide, working code, visual diagrams, research index
- **Benefits:** Consistency, maintainability, accessibility, professional appearance
- **Future-proof:** Can enhance to Option B (dataclasses) if needed, but Option A sufficient for <50 commands

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
