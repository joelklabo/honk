# AI Agent Configuration

> **⚠️ IMPORTANT:** This file (`docs/agents.md`) is the **SINGLE SOURCE OF TRUTH** for all AI agent instructions.
> 
> The following files are **SYMLINKS** to this file:
> - `AGENTS.md` → `docs/agents.md`
> - `CLAUDE.md` → `docs/agents.md`
> - `GEMINI.md` → `docs/agents.md`
> - `.github/instructions.md` → `docs/agents.md`
>
> **ONLY EDIT THIS FILE** (`docs/agents.md`) when updating AI agent context or instructions.
> Changes here automatically apply to all AI assistants (Agents, Claude, Gemini, GitHub Copilot).

## Project Structure

```
.
├── .github/
│   └── instructions.md -> ../docs/agents.md  (symlink)
├── .gitignore
├── AGENTS.md -> docs/agents.md               (symlink)
├── CLAUDE.md -> docs/agents.md               (symlink)
├── GEMINI.md -> docs/agents.md               (symlink)
├── docs/
│   ├── agents.md                 ← YOU ARE HERE (source of truth)
│   ├── plans/
│   │   └── main.md               ← Main work tracking document
│   ├── references/               # Documentation, research, notes
│   └── README.md
└── tmp/                          # Temporary files (gitignored)
```

## General Guidelines

- Follow project conventions and style
- Reference `docs/` for context
- **Use `docs/plans/main.md` for work tracking**
  - This is the primary document for tasks, progress, decisions, and next steps
  - Update this file as you complete tasks or make progress
  - Document important decisions and their rationale here
- **Use the project's `tmp/` directory** for all temporary files, scratch work, and outputs
  - ⚠️ **DO NOT use `/tmp/` or system temp directories**
  - All temporary files should go in `./tmp/` (relative to project root)
  - This directory is gitignored and safe for any temporary content
  - Examples: logs, cache files, build artifacts, test outputs, scratch files
- Check `docs/plans/` for project planning documents
- Check `docs/references/` for reference documentation

## Project Context

- **Goal:** Honk is an agent-first CLI that standardizes automation flows (doctor packs, auth, tooling). The first shipping tool is `honk demo hello`, which exercises the shared scaffolding.
- **Authoritative spec:** `docs/spec.md` captures the architecture, pinned dependencies, command documentation expectations, and CI workflows. Update it before making structural changes.
- **Work tracking:** `docs/plans/main.md` lists the current tasks, decisions, and blockers. Keep it current whenever you ship meaningful changes.

### Tech Stack

- Python 3.12.2 managed via uv 0.4.20 (`uv run …` is preferred for every command).
- Typer 0.12.3 + Rich 13.7.1 for CLI UX and help output; Textual 0.61.0 is an optional TUI dependency.
- Pydantic 2.8.2 + jsonschema 4.23.0 for result enveloping/introspection.
- HTTPX 0.27.2 + RESPX 0.21.1 for HTTP integrations/mocking.
- Tooling: pytest 8.3.3, pytest-xdist 3.6.1, ruff 0.6.9, mypy 1.11.2, nox 2024.4.15, pre-commit hooks.
- System CLIs: `gh` ≥ 2.58.0, `az` ≥ 2.63.0 (with DevOps extension), Node.js 20.13.1 via Volta when the optional Next.js site comes online.

### Architecture Overview

**CLI Structure:**
- **Grammar:** `honk <area> <tool> <action>` - consistent three-level hierarchy
- **Areas:** Top-level namespaces (e.g., `demo`, `auth`, `watchdog`) grouping related tools
- **Plugin System:** Areas register via `entry_points(group="honk.areas")` or namespace scan
- **Module Layout:**
  ```
  src/honk/
  ├── cli.py              # Root Typer app, global options, plugin loader
  ├── result.py           # Result envelope models and exit codes
  ├── registry.py         # Command introspection metadata
  ├── help.py             # JSON help schema generation
  ├── internal/           # Shared systems (doctor, logging)
  │   └── doctor/         # Prerequisite checking framework
  ├── auth/               # Authentication subsystem
  └── tools/<area>/       # Area-specific implementations
      ├── __init__.py     # Area registration (exports register() function)
      └── <tool>.py       # Tool commands (Typer sub-app)
  ```

**Result Envelope Pattern:**
- Every command returns a structured `ResultEnvelope` (JSON schema: `schemas/result.v1.json`)
- Required fields: `version`, `command`, `status`, `changed`, `code`, `summary`, `run_id`, `duration_ms`
- Extended fields: `facts{}` (command output data), `pack_results[]` (doctor checks), `links[]` (docs/resources), `next[]` (suggested follow-up commands)
- Exit codes: `0` (ok), `10` (prereq_failed), `11` (needs_auth), `12` (token_expired), `20` (network), `30` (system), `50` (bug), `60` (rate_limited)
- Humans see Rich-formatted output; agents consume JSON via `--json` flag

**Doctor Packs (Prerequisite System):**
- Framework for checking requirements before command execution
- Built-in packs: `global` (OS, disk, network), `auth-gh[scopes]`, `auth-az[org]`
- Packs declare dependencies (`requires=["global"]`) and emit remediation steps
- Commands call `run_all_packs(plan=plan)` before mutations
- Results included in `pack_results[]` array of result envelope

**Auth Subsystem:**
- Providers: GitHub (`gh` CLI wrapper), Azure DevOps (`az devops` CLI wrapper)
- Token storage: `keyring` library for secure credential management
- Commands: `honk auth <provider> {status,ensure,login,refresh,logout}`
- Auto-upgrade scopes via `gh auth refresh --scopes ...` or `az devops login`
- Expiry warnings when PAT < 7 days remaining

**Introspection System:**
- `honk introspect --json` emits full command catalog (areas, tools, actions, args, prereqs, examples)
- `honk help-json <command>` returns single-command schema
- Registry populated via `register_command(CommandMetadata(...))` calls
- Schema version: `schemas/introspect.v1.json`

### Coding Standards

- Always run commands through `uv run …` (or an activated `.venv` created by uv) to guarantee the locked environment.
- Implement CLI actions with Typer; provide descriptive docstrings, option `help=` text, and examples so `--help`/`--help-json` stay self-documenting.
- Use the shared result envelope helper for every command outcome. Surface prereq/auth problems via `status="prereq_failed"`/`"needs_auth"` and include actionable `next[]` entries.
- All temporary files, logs, or JSON streams belong under `tmp/` (never `/tmp`).
- Update `docs/spec.md` when changing architecture, dependencies, or process expectations, and log the decision in `docs/plans/main.md`.
- Keep lint/type/test suites passing locally (`uv run ruff check`, `uv run mypy`, `uv run pytest`) before sending changes upstream.

### Adding New Tools (Quick Reference)

When implementing a new tool (e.g., `honk watchdog pty`):

1. **Create area structure** under `src/honk/tools/<area>/`:
   - `__init__.py` - Area registration with `register(app: typer.Typer) -> AreaMetadata`
   - `<tool>.py` - Typer sub-app with commands (actions)
   - `<tool>_<module>.py` - Supporting logic (scanners, parsers, helpers)

2. **Implement commands** following patterns:
   - Call `run_all_packs(plan=plan)` for prerequisite checks
   - Use `auth.ensure()` for authentication when needed
   - Build `ResultEnvelope` with `facts`, `links`, `next` populated
   - Support `--json`, `--plan`, `--no-color` flags
   - Use Rich formatting for human output (panels, tables, status)

3. **Register metadata** for introspection:
   - Call `register_command(CommandMetadata(...))` for each action
   - Include `area`, `tool`, `action`, `full_path`, `description`, `options`, `arguments`, `prereqs`, `examples`

4. **Write tests** mirroring runtime layout:
   - Unit: `tests/tools/<area>/test_<tool>_<module>.py`
   - Integration: `tests/tools/<area>/test_<tool>_integration.py`
   - Contract: `tests/contract/test_<area>_<tool>_contract.py` (schema validation)

5. **Document**:
   - Implementation spec in `docs/references/<tool>-spec.md`
   - User guide in `docs/references/<tool>-guide.md` (optional)
   - Update `docs/plans/main.md` with task tracking
   - Update `docs/spec.md` if new patterns emerge

6. **Verify**:
   - `uv run honk <area> <tool> --help` renders correctly
   - `uv run honk introspect --json` includes new commands
   - All tests pass: `uv run pytest`
   - Linting passes: `uv run ruff check && uv run mypy`

## Important Files & Directories

- **docs/plans/main.md** - Main work tracking document (tasks, progress, decisions)
- **docs/plans/** - Additional project plans, architecture decisions, roadmaps
- **docs/references/** - Reference documentation, research notes
- **docs/agents.md** - This file (AI configuration)
- **tmp/** - Temporary files and scratch work (gitignored)

## Custom Agents

Define custom GitHub Copilot agents below:

### Example Agent

```markdown
---
name: Example Agent
description: A sample custom agent
---

# Agent Instructions

Your instructions here...
```

### Azure CLI Auth Agent

```markdown
---
name: Azure CLI Auth Agent
description: Deep specialist for az CLI + Azure DevOps authentication flows
---

# Agent Instructions

- Reference `docs/references/azure-cli-auth.md` before answering.
- Always describe which credential type fits the user’s scenario (interactive dev, CI, GitHub-hosted runners, Azure resources) and call out security trade-offs.
- When discussing Azure DevOps, detail PAT handling, `AZURE_DEVOPS_EXT_PAT`, `az devops login`, and Entra token acquisition via `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798`.
- Include remediation checklists for failures (e.g., `AADSTS50076`, missing scopes, expired PAT) and link to the relevant Microsoft Learn articles you rely on.
- Default to automation-friendly advice (device code, non-interactive flows, secure secret storage in keyring/Key Vault) and remind users to rotate secrets.
```

### GitHub CLI Auth Agent

```markdown
---
name: GitHub CLI Auth Agent
description: Expert navigator for gh CLI authentication, scopes, and multi-host setups
---

# Agent Instructions

- Use `docs/references/github-cli-auth.md` as your quick sheet. Reconcile every answer with the `gh auth login/status/refresh/token/logout` manuals you’ve studied.
- Explain how to choose between OAuth browser flow, `--with-token`, and environment-driven auth (`GH_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GH_HOST`). Offer copy-pasteable sequences.
- Advise on scope hygiene using `gh auth refresh --scopes/--remove-scopes`, and mention the minimum (`repo`, `read:org`, `gist`) whenever relevant.
- Coach users on multi-account setups: when to `gh auth switch`, how to isolate credentials via `GH_CONFIG_DIR`, and how to export tokens safely to other tools.
- When tokens must be revoked, list the exact UI path (`Settings → Applications → GitHub CLI`) and caution against leaving secrets in shell history.
```
