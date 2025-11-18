## Honk Spec

Table of contents
1. Implementation
2. Dependencies
3. Testing & CI
4. Agent contract (docs/agents.md)
5. Initial deliverables (what to implement first)
6. Suggestions — what else to add

1) Implementation

1.1 Python toolchain (uv: locked + auto bootstrapped)
- Target Python 3.12.2 and uv 0.4.20 (adjust only through explicit spec updates).
- Bootstrap:
    ```bash
    uv init --name honk
    uv python install 3.12
    uv venv --python 3.12 --seed .venv
    uv add typer==0.12.3 rich==13.7.1 textual==0.61.0 httpx==0.27.2 pydantic==2.8.2 keyring==24.3.1 jsonschema==4.23.0
    uv add -d pytest==8.3.3 pytest-xdist==3.6.1 respx==0.21.1 ruff==0.6.9 mypy==1.11.2 nox==2024.4.15
    uv sync --all-extras --dev
    ```
- Use repo-local `.venv/` managed by uv; prefer `uv run <cmd>` so activation is automatic in shells and CI.
- Add optional direnv support (`layout python .venv/bin/python`) but keep `uv run` as the canonical path.
- `noxfile.py` hosts reusable sessions (`ruff`, `mypy`, `tests`, `format`, `docs-check`) that shells and CI call with `uv run nox -s <session>`.

1.2 Core CLI skeleton (agent-first Typer app)
- Modules: `src/honk/__init__.py`, `src/honk/cli.py`, `src/honk/result.py`, `src/honk/help.py` (custom JSON help emitter).
- Typer 0.12.x provides `--help` with Rich formatting; it does **not** implement `--help-json`, so we add one ourselves plus `honk introspect --json` to expose machine schemas.
- Required capabilities:
    - `honk introspect --json`: emits command catalog (areas, tools, actions, args, prereqs, examples). Implemented via internal registry scan (see §1.8) and serialized with Pydantic.
    - `--help-json` option on every action: dumps only that command’s schema (arguments, options, examples, doctor packs, auth scopes).
    - Result envelope helper describing `status`, `code`, `changed`, `summary`, `run_id`, `duration_ms`, `facts{}`, `links[]`, `next[]`, `pack_results[]`.
    - Base flags on every command: `--json`, `--plan`, `--no-input`, `--events-jsonl tmp/<file>.jsonl`, `--no-color` (forces monochrome Rich output for accessibility).
    - `--plan` executes doctor/auth checks and returns proposed actions under `facts.plan.steps[]` without side effects.
- Deterministic exit codes: `0 ok`, `10 prereq_failed`, `11 needs_auth`, `12 token_expired`, `20 network`, `30 system`, `50 bug`, `60 rate_limited`.
- Result envelope schema (commit JSON Schema under `schemas/result.v1.json`, validate in CI):
    ```json
    {
      "version": "1.0",
      "command": ["demo","hello","run"],
      "status": "ok",
      "changed": false,
      "code": "demo.hello.run.ok",
      "summary": "Sent greeting",
      "run_id": "uuid4",
      "duration_ms": 12,
      "facts": {"greeting": "hello, world"},
      "pack_results": [{"pack": "global", "status": "ok", "duration_ms": 7}],
      "links": [{"rel": "docs", "href": "https://…"}],
      "next": [{"run": ["honk","demo","hello","run","--json"], "summary": "Repeat with JSON"}],
      "retry_after_secs": 0
    }
    ```
- Emit `retry_after_secs` and set `status="remote.rate_limited"`, `exit=60`, when upstream APIs return 429/abuse responses; include a single `next` entry that sleeps/backoffs.

1.3 Prereq engine (“doctor” packs)
- Lives under `src/honk/internal/doctor/` with pack registry + runner.
- Built-in packs:
    - `global`: OS, arch, disk free, network reachability, tmp dir permissions.
    - `auth-gh[scopes]`: uses `gh auth status --show-token --json` to inspect scopes; if missing, run `gh auth refresh --scopes <scopes>` headlessly or emit `needs_auth` with `next=["gh","auth","refresh",...]`.
    - `auth-az[org]`: runs `az devops project list --org <url>`; on 401/403 attempts PAT from Keychain via `az devops login --organization <url>`; fallback to device code flow with actionable `next`.
- Packs declare `requires=["global"]` style dependencies and expose `summary`, `checks[]`, `next[]` describing remediation commands.
- Packs run before any action with `--plan` obeyed (no mutations), and emit structured responses consumed by the result envelope.

1.4 Shared auth subsystem (GitHub + Azure DevOps)
- Detailed flows, CLI UX, and storage design live in [`docs/spec-auth.md`](./spec-auth.md); this section summarizes the high points for the main spec.
- Command group: `honk auth <provider> <action>` with Typer sub-apps per provider.
- GitHub provider actions: `status`, `ensure`, `login`, `refresh`, `logout`; call `gh auth status --json` to diff desired scopes (repo/read:org/admin:org). Auto-upgrade by running `gh auth refresh --scopes ...` and surfacing remediation steps.
- Azure DevOps actions: `ensure`, `login`, `logout`, `configure`; prefer PAT-based `az devops login` (read from keyring), set defaults via `az devops configure -d organization=…`, and fall back to `az login --use-device-code` when PAT absent.
- PAT management rules (applies to both providers):
    - Tokens are stored/retrieved via `keyring`; commands never read raw secrets from env vars.
    - `honk auth status` prints scope coverage plus expiration time (pull from provider API where available, else store alongside keyring entry). Emit a yellow Rich panel + `facts.auth.warning="PAT expires in <n days>"` when <7 days remain.
    - Acquisition flows:
        - GitHub: run `gh auth login --scopes <scopes>` (device or browser flow); capture resulting token via `gh auth status --show-token --json token,expires_at` and store in keyring entry `honk/github` with metadata `{scopes:[], expires_at}`.
        - Azure DevOps: prompt for PAT (stdin) or initiate device flow; feed PAT to `az devops login --organization <url>` and store encrypted copy under `honk/azure_devops/<org>` with metadata.
    - Persistence: tokens live solely in keyring; metadata cache persisted under `~/.config/honk/auth.json` for quick expiry checks (never storing secrets, only hashes + timestamps).
    - Refresh flows:
        - `honk auth refresh gh --scopes repo,read:org` calls `gh auth refresh --scopes …`, parses new expiry, updates keyring and metadata atomically, and outputs next steps (e.g., “Scopes upgraded”).
        - `honk auth refresh az --org https://dev.azure.com/foo` requests a PAT (stdin prompt or pass via `--pat-file`), pipes to `az devops login`, and rotates stored metadata.
    - Background reminders: doctor packs raise `needs_auth` (exit 11) with `next=["honk","auth","<provider>","refresh",...]` whenever expiration threshold is exceeded so downstream tools never guess.
    - Other tools treat auth as opaque; they call `auth.ensure()` and receive structured failures (`status="needs_auth"`, `next=[...]`) if tokens are missing/expired so they never implement PAT logic themselves.
- Other tools call into providers instead of reimplementing auth flows; doctor packs use `auth-*` providers as prereqs.

1.5 `honk demo hello` (first tool)
- Area: `demo`; command path: `honk demo hello run`.
- Purpose: prove the shared scaffolding works end-to-end (doctor → auth → result envelope) before investing in heavier tooling.
- Behavior:
    - Runs `global` doctor pack; respects `--plan` to skip side effects.
    - Accepts `--name` (default "world") and `--json` (inherit base flag) to emit a greeting message.
    - Prints Rich-formatted output for humans and always returns the structured result envelope for agents.
- Implementation guidance:
    1. Create `demo_app = typer.Typer(help="Demo commands that showcase Honk plumbing.")`.
    2. Register `@demo_app.command("hello")` with `help="Print a greeting using shared result envelope"` and argument annotations describing options (Typer auto-generates `--help`).
    3. Inside the command, call the doctor engine (`doctor.run("global")`); if it fails, bubble up `status="prereq_failed"` with `next` suggestions from the pack output.
    4. Compose success responses via `result.ok(summary="Sent greeting", facts=[{"name": "greeting", "value": message}])`.
    5. Attach the demo app to the main CLI: `app.add_typer(demo_app, name="demo")`.
- Example help invocation (auto-generated by Typer + Rich):
    ```bash
    uv run honk demo hello --help
    ```
  This is the canonical “man page” and must stay descriptive (include option help, examples, and notes on JSON usage).

1.6 Command documentation pattern (Typer-powered “man pages”)
- Every command provides thorough docstrings, option `help=` text, and example usage via Typer’s `epilog`/`rich_help_panel`.
- Agents learn commands by running `honk introspect --json` or `honk <…> --help-json`; humans rely on `--help` and the colorful Rich output.
- When extending Honk, update the command’s Typer configuration instead of adding separate markdown man pages. If additional prose is needed, store it beside the command under `docs/references/`.

1.7 Developer ergonomics
- `pre-commit` hooks (Ruff lint + MyPy quick type check) keep contributors aligned.
- `tmp/` is the only scratch directory; commands writing logs/events must respect it.
- Optional niceties: Textual-based TUI (`honk ui`) and a Next.js site remain stretch goals but should reuse the same introspection data. Textual can render in terminal or browser, so any view must consume the same JSON envelopes/events instead of bespoke transport.
- Textual TUI mirrors JSON responses—no command should depend on scraping TUI output; it merely renders the same result envelopes/events for humans.
- Honk must look/feel consistent: prefer Typer’s built-in help, Rich formatting helpers (see below), and the shared result envelope instead of bespoke prints.
- Follow framework best practices—Typer command docstrings, Pydantic models for structured data, HTTPX clients with context managers—so agents can rely on predictable behavior.
- Centralized redaction: all logs/results/events pass through `core.redact(data)` which masks keys containing `token|secret|pat|password`; commands must never print secrets.
- Accessibility: honor `--no-color`/`HONK_NO_COLOR`; ensure Rich styles degrade to plain text (no reliance on color alone) and prefer semantic headings/emojis sparingly.

1.8 CLI container design patterns
- Treat Honk as a container/namespace host: `honk <area> <tool> <action>` is the canonical grammar, with each area mounted as a Typer sub-app.
- Use the word **area** everywhere (not domain/module) so docs, schemas, and help stay aligned.
- Directory layout:
    - `src/honk/cli.py`: root Typer app, global options, plugin loader that iterates entry points / namespace packages.
    - `src/honk/core/`: shared systems (`doctor`, `auth`, `result`, `introspect`, `logging`).
    - `src/honk/tools/<area>/`: area-specific Typer apps and helpers (e.g., `tools/demo/hello.py`).
- Plugin discovery:
    - Areas register themselves via `entry_points(group="honk.areas")` or a namespace scan (`pkgutil.iter_modules(honk.tools.__path__)`).
    - Each area module exposes `register(app: typer.Typer) -> AreaMetadata` (name, summary, prereqs, options).
    - `cli.py` loads every entry point dynamically; missing metadata raises at import time, so adding a tool never requires editing central registries.
    - The collected metadata feeds `honk introspect --json` and `--help-json`, ensuring definitions live in one place.
- Shared dependencies (doctor packs, auth adapters, tmp/ discipline, Rich output) must be reused across tools to maintain a consistent UX.
- Result envelopes drive both human Rich rendering and agent JSON; no tool writes bespoke stdout without first updating the envelope.
- `src/honk/core/ui.py` hosts reusable Rich helpers so every command renders output the same way. Example helpers (extend as needed):
    ```python
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    def render_success(summary: str) -> None:
        console.print(Panel(summary, title="Success", border_style="green"))

    def render_error(summary: str, details: str | None = None) -> None:
        body = summary if not details else f"{summary}\n[dim]{details}[/dim]"
        console.print(Panel(body, title="Error", border_style="red"))

    def render_facts(facts: list[dict[str, str]]) -> None:
        table = Table(title="Facts", show_header=True, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Value")
        for fact in facts:
            table.add_row(fact["name"], fact["value"])
        console.print(table)
    ```
- Commands call these helpers (or higher-level wrappers) so humans always see the same layout; agents still read the raw result envelope.

1.9 Adding a new tool (extensibility checklist)
1. Create a module under `src/honk/tools/<area>/` with a Typer app and descriptive help text (`area_app = typer.Typer(help="...")`).
2. Implement commands using shared helpers:
    - Call `doctor.run("global")` (and other packs) before mutating anything.
    - Use `auth.ensure("gh", scopes=[...])` or `auth.ensure("az", org=...)` instead of shelling out manually.
    - Return results via `result.ok()`/`result.error()` so humans and agents see consistent output.
3. Publish the area via the plugin loader:
    - Export `def register(app: typer.Typer) -> AreaMetadata` in the module.
    - Expose the module through `pyproject.toml` entry points (`[project.entry-points."honk.areas"] demo = honk.tools.demo:register`).
    - The loader fails fast if metadata is missing or duplicate area names appear.
4. Update `docs/spec.md` (tool section) and `docs/plans/main.md` (task + decision) to capture the new command's intent and requirements.
5. Add tests mirroring runtime layout (`tests/tools/<area>/test_<tool>.py`) covering doctor/auth interactions and the result envelope.
6. Run `uv run honk <area> <tool> --help` to verify the auto-generated “man page” remains descriptive; adjust Typer docstrings/option help as needed.
7. Snapshot Rich output for key commands using `rich.console.Console(record=True)` tests so layout regressions fail fast.

1.10 Configuration & profiles
- Config files live under `~/.config/honk/` (XDG). `config.toml` stores global toggles; `profiles/<name>.toml` override per context (e.g., `ios-prod`, `demo`).
- Supported keys (grow as the CLI expands):
    ```toml
    [runner]
    xcode_path = "/Applications/Xcode_16.app"
    labels = ["self-hosted","macOS","xcode-16"]

    [auth]
    github_scopes = ["repo","read:org"]
    az_org = "https://dev.azure.com/my-org"

    [telemetry]
    enabled = false
    ```
- Commands honor `--profile <name>`; the active profile is emitted via `facts.profile` in the result envelope.
- `honk config show` prints merged config (redacting keys containing `token|secret|pat`); `honk config set key=value` updates `config.toml` while keeping TOML comments intact.
- Config toggles include color mode (`color=auto|always|never`), tmp directory override, telemetry opt-in, and default doctor packs.

---

2) Dependencies (what and why)

| Category | Tool | Version | Notes |
| --- | --- | --- | --- |
| Python runtime | CPython | 3.12.2 | Matches uv-managed `.venv`; upgrade via spec change only. |
| Package manager | uv | 0.4.20 | Single command bootstraps env + lock file. |
| CLI framework | Typer | 0.12.3 | Auto help/`--help-json`; integrates Rich. |
| Output formatting | Rich | 13.7.1 | Colorized help + result rendering. |
| TUI (optional) | Textual | 0.61.0 | Future interactive UI. |
| Schemas | Pydantic | 2.8.2 | Result envelope + introspection models. |
| HTTP | HTTPX | 0.27.2 | Remote integrations; RESPX for tests. |
| Secrets | keyring | 24.3.1 | macOS Keychain storage for tokens. |
| Validation | jsonschema | 4.23.0 | Validate introspection/results if needed. |
| Testing | pytest | 8.3.3 | Core test runner. |
| Parallel tests | pytest-xdist | 3.6.1 | Speed up suites. |
| HTTP mocking | respx | 0.21.1 | Mock HTTPX clients. |
| Linting | ruff | 0.6.9 | Style + import order. |
| Typing | mypy | 1.11.2 | Enforce Pydantic/type hints. |
| Task runner | nox | 2024.4.15 | Shared automation entrypoint.

System CLIs (pin via tooling docs):
- GitHub CLI `gh` ≥ 2.58.0.
- Azure CLI `az` ≥ 2.63.0 with DevOps extension.
- Node.js 20.13.1 via Volta (needed only when building optional Next.js site). Enable Corepack and set the repo root `packageManager` field (`"packageManager": "pnpm@9.12.0"`) so every workspace component reuses the same pnpm without per-project duplication.

---

3) Testing & CI

3.1 Test levels
- Unit: result envelope helpers, doctor pack combinators, argument parsing, auth adapters.
- Contract (lightweight for now): run `honk introspect --json` and representative `honk demo hello --json` in CI to ensure outputs stay parseable.
- Integration: subprocess wrappers around `gh`/`az` (mock with RESPX/fixtures until real credentials available).
- E2E (future): guardrails for heavier workflows once new tools ship.
- Schema discipline: keep `schemas/result.v1.json` and `schemas/introspect.v1.json` under version control; validate emitted JSON against them via `uv run pytest tests/contract` during CI.

3.2 Pytest layout
```
tests/
    core/
    doctor/
    demo/
    contract/
tests_integration/
```
- Use `tmp_path` fixtures for scratch artifacts; forbid touching global `/tmp`.

3.3 GitHub Actions plan
- `.github/workflows/ci-core.yml` (Ubuntu latest): checkout → `uv python install 3.12 && uv sync --locked` → run `uv run ruff check`, `uv run mypy`, `uv run pytest -m "not slow"`, `uv run honk introspect --json > tmp/introspect.json`, `uv run honk demo hello --help` to ensure help renders.
- Capture `uv run honk demo hello --help-json > tmp/demo_hello.help.json` and validate it against `schemas/help.v1.json` to guarantee the machine contract stays stable.
- If/when web tooling lands, add `corepack enable` + `corepack use pnpm@9.12.0` before any `pnpm` command to guarantee reproducible installs.
- `.github/workflows/ci-macos.yml` (macOS): same uv bootstrap + `uv run honk demo hello --plan --json` to exercise doctor packs on Apple hardware.
- `.github/workflows/docs-guard.yml`: fail if markdown docs exist outside `docs/` (respect symlinks noted in `docs/README.md`).
- `.github/workflows/release.yml`: triggered on tags; runs `uv build` and `uv publish` after reusing `ci-core` steps.
- Smoke + snapshot tests:
    - Add `uv run pytest tests/snapshots/test_help.py -m snapshots` in `ci-core` to record/compare Rich output using `Console(record=True)`.
    - Future tools should extend the snapshot suite so regressions in formatting immediately fail CI.

3.4 Performance discipline
- Cache `.venv`/`.uv` directories via GitHub Actions cache to keep installs fast.
- Reuse HTTPX clients and auth tokens across commands where possible; store ephemeral artifacts under `tmp/` to avoid re-computation.
- Ensure doctor packs short-circuit when prior runs succeed (`--plan` can reuse cached checks) so repeated invocations stay quick.
- Consider memoizing expensive discovery (e.g., `honk introspect`) so agents benefit from consistent, low-latency responses.

---

4) Agent contract (docs/agents.md)
- Grammar:
    ```
    honk <area> <tool> <action> [flags]
    ```
- Discovery:
    - `honk introspect --json` → full catalog.
    - `honk <…> --help-json` → action schema.
- Execution defaults:
    - Headless by default; prefer `--json`. Use `--plan` for dry-run; stream via `--events-jsonl`.
- Result envelope v1.0 (schema): version, command, status, changed, code, summary, facts, links, next.
- Auth and prereq semantics: `needs_auth` and `prereq_failed` statuses include `links` and `next` remediation commands.
- tmp/: all ephemeral artifacts under `./tmp/`.
- Chaining: `next[]` entries are argv-ready arrays.
- Versions: `honk --version` prints CLI + schema versions.

---

5) Initial deliverables (tiny slice to land)
1. Locked uv environment + `.venv`, `pyproject.toml`, and `noxfile.py` with baseline sessions.
2. Typer CLI skeleton emitting result envelopes + `honk introspect --json`.
3. Doctor engine with `global` pack wired into CLI + `--plan` semantics.
4. Minimal `honk auth ensure gh|az` that shells out to `gh`/`az` and stores tokens via keyring.
5. `honk demo hello` tool demonstrating prereqs → command → result envelope with descriptive Typer help.
6. GitHub Actions workflows (`ci-core`, `ci-macos`, `docs-guard`, `release`) matching the plan above.

---

6) Suggestions — what else to add
- Security & secrets: document Keychain usage, PAT rotation, ephemeral token policies.
- Observability: structured logging + optional telemetry surface (respect opt-in).
- Error handling: shared retry/backoff helpers for network actions.
- Release & upgrade strategy: versioning policy for CLI/result schema, changelog expectations.
- Distribution: publish to PyPI via uv Trusted Publisher and maintain a Homebrew formula that wraps the PyPI artifact; keep `honk` as the single entry point across channels.
- Contribution & governance: CODEOWNERS, contributing.md, review checklist, release checklist.
- Documentation & onboarding: quickstart showing uv bootstrap + `honk demo hello run --name you` flow.
- Architecture artifacts: diagrams showing CLI, doctor, auth, and future tool areas.
- UX & accessibility: Textual TUI accessibility notes; Rich color usage guidelines.
- Performance & CI scale: caching uv/ruff/mypy artifacts, pytest shard strategy when suites grow.
- Backwards compatibility: how to evolve the result envelope and introspection schema safely.

---

Keep the spec concise and treat `docs/agents.md` as the single source of truth for agent contracts. Track day-to-day work and decisions in `docs/plans/main.md`.
