# Main Work Tracking

> **📋 This is the main work tracking document for this project.**
> 
> Use this file to track tasks, progress, decisions, and next steps.

## Current Status

- Spec reorganized to focus on the uv-managed toolchain, Typer-based CLI, and the `honk demo hello` exemplar.
- Exact dependency versions, documentation expectations, and CI workflow plans are now captured in `docs/spec.md`.
- Next milestone: turn the spec into a working CLI skeleton with doctor/auth plumbing.

## Active Tasks

- [ ] Stand up uv-managed Python environment + `noxfile.py` sessions.
- [ ] Implement Typer CLI skeleton with result envelope + `honk introspect --json`.
- [ ] Build doctor engine with the `global` pack and hook it into commands.
- [ ] Ship `honk demo hello` (doctor + greeting + Rich help text).
- [ ] Configure GitHub Actions workflows (`ci-core`, `ci-macos`, `docs-guard`, `release`).

## Completed Tasks

- [x] Bootstrap AI-oriented project structure
- [x] Refresh spec for demo-first roadmap (uv pins, Typer help pattern, CI plan)

## Next Steps

1. Implement uv environment + baseline nox sessions.
2. Land CLI skeleton + demo command per spec guidance.
3. Wire up CI workflows and verify `honk demo hello --help` runs in automation.

## Decisions & Notes

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
