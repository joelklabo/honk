# Honk Auth Subsystem Spec

2025-11-17

## Goals

- Provide a reusable Python module (`honk.core.auth`) that manages authentication for GitHub (`gh`) and Azure DevOps (`az devops`).
- Centralize credential acquisition, storage, expiry tracking, and refresh so individual Honk tools never touch tokens directly.
- Guarantee headless + interactive flows, deterministic exit codes, and JSON-first outputs that match the main Honk result envelope contract.
- Support multiple accounts/hosts/orgs simultaneously while keeping UX simple (`honk auth <provider> <action>`).
- Surface proactive warnings when tokens near expiry (<7 days) and supply actionable `next[]` steps.

## Provider Overview

| Provider | CLI backend | Auth artifacts | Primary scopes |
| --- | --- | --- | --- |
| GitHub | `gh auth login/refresh/status` | OAuth token stored in system keychain (managed by gh) + optional PAT from stdin | `repo`, `read:org`, `gist` base; add `admin:org`, `workflow`, etc. |
| Azure DevOps | `az devops login`, `az login --use-device-code`, REST PAT endpoints | PAT stored in Keychain entry per organization | Org-level PAT scopes (`vso.code`, `vso.work`, `vso.packaging`) |

## Architecture

```
src/honk/core/auth/
    __init__.py
    base.py           # shared Pydantic models, enums
    github.py         # GitHub-specific adapters
    azure.py          # Azure DevOps-specific adapters
    keyring_store.py  # keyring + metadata persistence helpers
    cli.py            # Typer sub-app reused by honk auth commands
    doctor.py         # provider-specific doctor pack integrations
```

- `AuthProvider` (base class): implements `ensure(context)`, `status()`, `refresh()`, `logout()`, `metadata()`.
- Providers depend on two lower layers:
  1. `KeyringStore`: encrypts tokens via `keyring` + stores JSON metadata in `~/.config/honk/auth.json`.
  2. `ProcessRunner`: thin wrapper over `uv run gh …` / `uv run az …` with Rich logging + JSON parsing helpers.

### Credential discovery order

Before prompting a user or touching the keyring, the auth manager must honor any credentials that the CLIs already expose:

- **GitHub**: check `GH_TOKEN`/`GITHUB_TOKEN` (github.com) and `GH_ENTERPRISE_TOKEN`/`GITHUB_ENTERPRISE_TOKEN` (GHE). Respect `GH_HOST` when deciding which host to query. If these env vars exist, treat them as authoritative and skip `gh auth login` entirely.
- **Azure DevOps**: reuse an existing `az login` session whenever possible. If `AZURE_DEVOPS_EXT_PAT` is present (or a PAT is piped to stdin), prefer that over prompting the user. Honk-specific helpers (e.g., `HONK_AZURE_DEVOPS_PAT_FILE`) remain fallbacks for niche automation.

## Token Lifecycle (GitHub)

1. **Acquisition**
   - Preferred: `gh auth login --web --scopes <scopes>` (device flow) triggered via `AuthProvider.ensure` when no valid token is found.
   - Headless: `gh auth login --with-token` reading from stdin if HONK is running in CI.
   - Honk will launch the `gh auth login` wizard automatically (opening the OAuth device page in the user’s browser) whenever it needs new credentials. If the environment forbids browser launch, it prints the device code and copies it to the clipboard so the user can finish auth manually.
   - After login, run `gh auth status --hostname <host> --json hosts` to capture account metadata, followed by `gh auth token --hostname <host> --user <account>` to retrieve the raw credential for hashing. (Never persist the plaintext token outside the immediate context.)
   - If a user elects to paste a token instead, Honk opens the correct GitHub page (`https://github.com/settings/tokens` for classic, `https://github.com/settings/personal-access-tokens/new` for fine-grained) via the default browser, prompts for the string, verifies it with `gh auth status`, and only then stores it.
   - Remind users of the minimum scopes (`repo`, `read:org`, `gist`) and that fine-grained PATs are best exported via `GH_TOKEN`/`GH_ENTERPRISE_TOKEN` for automation.
   - Persist token reference: store opaque credential in keyring key `honk/github/<hostname>/<username>` (value = token). Metadata entry:
     ```json
     {
       "provider": "github",
       "hostname": "github.com",
       "user": "octocat",
       "scopes": ["repo","read:org"],
       "expires_at": "2026-01-15T12:00:00Z",
       "minted_at": "2025-11-17T20:15:00Z",
       "source": "gh auth login"
     }
     ```
2. **Usage**
   - Tools call `auth.ensure("github", scopes=[...])`.
   - Provider checks metadata + runs `gh auth status --hostname … --json hosts --jq '…'` to confirm scopes.
   - Missing scopes → run `gh auth refresh --scopes <scopes>` headlessly; doctor pack receives failure if refresh denied.
   - If the target host/account is not currently active, issue `gh auth switch --hostname … --user …` before refreshing scopes so `gh auth refresh` touches the right identity.
3. **Expiry tracking**
   - Use `expiresAt` from `gh auth status` when available (GitHub CLI exposes for fine-grained tokens). If absent, fall back to storing `minted_at + 365d` and refreshing proactively at the 350-day mark.
   - Background check (doctor pack) includes `facts.auth.github.expires_in_days`.
4. **Refresh**
   - `honk auth refresh gh --scopes repo,workflow` executes `gh auth refresh --scopes … --hostname <host>`.
   - Parse JSON output (when available) or re-run `gh auth status --json` to capture new scopes + expiry, then update keyring metadata atomically.
   - Provide Rich summary + result envelope `facts` describing new expiry, scopes, and warnings.
   - Add `next[]` entries that explain how to revoke or regenerate credentials via `https://github.com/settings/applications` → “GitHub CLI” whenever Honk detects stale scopes or compromised tokens.
   - Reminder: GitHub CLI never drops the baseline `repo`, `read:org`, and `gist` scopes, so Honk should treat those as immutable when editing scope sets.
5. **Warning thresholds**
   - `<7 days`: status still `ok` but `facts.auth.warning` plus Rich yellow panel.
   - Expired: `status="needs_auth"`, exit 11, `next` includes refresh/login commands.

## Token Lifecycle (Azure DevOps)

1. **Acquisition**
   - `auth.ensure("azure", org="https://dev.azure.com/my-org")` first checks whether an Entra access token is already available via `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798`. Honk drives this automatically: it runs `az login` (device flow on headless hosts) if needed, selects the user’s subscription with `az account set -s <subscription-id>`, then executes `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv`. The GUID is the Microsoft DevOps resource ID published in Microsoft Learn; if it ever changes, read the latest value from [Issue Entra tokens with Azure CLI](https://learn.microsoft.com/en-us/azure/devops/cli/entra-tokens?view=azure-devops). Favor this short-lived token over PATs whenever possible.
   - Next, reuse any PAT surfaced through `AZURE_DEVOPS_EXT_PAT` or prior `az devops login` session before falling back to keyring lookups (`honk/azure_devops/<org-url>`).
   - Missing entry → Honk attempts `az devops login --organization <url>` on behalf of the user. When PAT input is required, it automatically opens the Azure DevOps PAT page (`https://dev.azure.com/<org>/_usersSettings/personalAccessTokens`) in the browser, prompts for the token, validates it by running `az devops project list --org <url>`, and only stores it after the command succeeds. Remind users they can create scoped tokens via `User settings → Personal access tokens → + New Token`, choosing minimal scopes (Agent Pools, Code, etc.). Optionally stream PATs via stdin for CI.
   - For headless use, allow `HONK_AZURE_DEVOPS_PAT_FILE` to point to a file; tool reads once, feeds into login, then deletes file securely.
   - Store PAT in keyring; metadata entry includes `org_url`, `scopes`, `expires_at` (user-supplied or read from PAT creation API), `created_with`.
2. **Usage**
   - Tools call `auth.ensure("azure", org=…)`. Provider prefers Entra tokens when available; otherwise it verifies PATs by running `az devops project list --org <url> --query "value[].name"`.
   - Non-zero exit → categorize (401/403) and escalate to doctor pack.
3. **Expiry tracking**
   - PAT creation UI returns expiration length (30/60/90 days custom). Prompt user for TTL when storing; persist exact date.
   - Provide `honk auth status az --json` to show `expires_at`, `scopes`, and `org`.
   - Doctor pack warns at `<14 days` so enterprise admins have margin to recreate PATs.
4. **Refresh**
   - PATs cannot be extended; we generate a replacement by prompting again (optionally launching `az devops login --organization …` which requests PAT via browser/device flow).
   - After new PAT captured, update keyring entry + metadata.
5. **Device fallback**
   - If PAT entry fails and CLI is non-interactive, command returns `status="needs_auth"`, `code="auth.azure.pat_required"`, and `next=["honk","auth","az","login","--org",…]`.

6. **Rotation & policies**
   - Surface reminders to rotate PATs regularly and reference tenant policies (auto-revoke leaked PATs, maximum lifetimes). When Honk detects compromised tokens, include admin-friendly `next[]` steps pointing to the PAT Lifecycle Management APIs.

### MFA enforcement & remediation

- Microsoft will require multifactor auth for user identities in CLI flows (see “The impact of multifactor authentication on Azure CLI in automation scenarios”). Honk should proactively warn when `az login` is using a username/password path and suggest switching to service principals (`az login --service-principal …`), managed identities (`az login --identity`), or workload federation as appropriate.
- When `az` returns `AADSTS50076` (or similar) during ensure/refresh, emit `status="needs_auth"`, include the failing tenant ID, and list concrete remediation steps (`create service principal`, `assign role`, `update script to use --service-principal`).

## Metadata & Storage

- **Keyring**: continue using existing dependency (`keyring==24.3.1`). Keys follow `honk/<provider>/<identifier>` naming to avoid collisions.
- **Metadata cache**: JSON file at `~/.config/honk/auth.json` containing array of provider entries. Access through `AuthMetadataStore` (Pydantic models ensure schema). Fields:
  - `provider`, `id`, `display_name`, `scopes`, `expires_at`, `minted_at`, `status`, `warning`, `last_checked_at`.
- **Integrity**: on every run, metadata is reconciled with `gh auth status --json` or `az devops project list`; mismatches trigger repairs.
- **Redaction**: metadata never stores actual tokens; only hashed fingerprints using `hashlib.sha256(token)`. (Add dependency `cryptography` only if we later encrypt metadata; not required now.)

## CLI UX (`honk auth …`)

```
honk auth gh status   --json|--help-json
honk auth gh ensure   --scopes repo,workflow --hostname github.com --profile work
honk auth gh refresh  --scopes admin:org
honk auth gh logout   --hostname github.com

honk auth az status   --org https://dev.azure.com/my-org
honk auth az login    --org … [--pat-file path]
honk auth az refresh  --org …
honk auth az logout   --org …
```

- All commands honor `--json/--plan/--no-color/--events-jsonl` and return the enhanced result envelope.
- `status` commands return `facts.auth` object summarizing scopes, expiry, warning, hashed fingerprint, and last-checked timestamp.
- `ensure` (used by doctor packs) performs read-only verification when `--plan` is set; otherwise it may call refresh flows automatically if interactive.

## Doctor Pack Integration

- `auth-gh[scopes]`
  - Inputs: list of scopes + hostname.
  - Steps: `AuthProvider.ensure` → if missing scopes or token, status `needs_auth` with `next` pointing to `honk auth gh refresh`.
  - Output facts: `expires_in_days`, `scopes_missing`, `warning`.
- `auth-az[org]`
  - Inputs: org URL.
  - Steps: `AuthProvider.ensure` → run `az devops project list` to confirm PAT works.
  - Output facts: `expires_in_days`, `org_url`, `warning`.

## Python API Surface

```python
from honk.core.auth import AuthManager, ProviderID, EnsureContext

manager = AuthManager(config=Config.load())
credential = manager.ensure(ProviderID.GITHUB, EnsureContext(scopes=["repo"], hostname="github.com"))
if credential.status is Status.OK:
    token = credential.token  # only accessible within context manager
    # use token for HTTP requests if needed
```

- `AuthManager.ensure` returns a context object exposing tokens only inside a `with` block to reduce accidental leaks.
- Outside of Honk core, tools call high-level helpers (`auth.ensure_github(scopes=…)`) that wrap CLI invocations, not tokens.

## Dependencies

| Package | Version | Purpose |
| --- | --- | --- |
| `python-dateutil` | 2.9.0 | Parse ISO timestamps (`expiresAt`). |
| `pendulum` (optional) | 3.x | Humanized durations for warnings. |
| `keyring` | already listed | Token storage. |
| `httpx` | already listed | Potential direct API checks (optional). |
| `pydantic` | already listed | Metadata models. |
| `rich` | already listed | Warning panels. |
| `tenacity` | 9.x (optional) | Retry wrapper for flaky CLI subprocesses. |

Additions to `docs/spec.md` dependency table if adopted: `python-dateutil`, `pendulum`, `tenacity`.

## Edge Cases & Handling

| Scenario | Behavior |
| --- | --- |
| Token missing scopes | Attempt automatic `gh auth refresh --scopes …`; if non-interactive, emit `needs_auth` with next steps. |
| Expired PAT | Immediately return `needs_auth` + guidance; doctor pack fails before tools run. |
| Keyring unavailable | Fall back to encrypted file in `~/.config/honk/secure/` (AES-256 using OS key). Emit warning + instructions to install keyring backend. |
| Multiple GitHub hosts | Metadata keyed by hostname; `honk auth gh status --hostname host` handles each separately. |
| Device flow denied | Bubble up failure with `status="needs_auth"`, `code="auth.github.device_denied"`, `next` instructing to rerun login. |
| Non-interactive refresh request | If CLI is headless and cannot open browser/device prompts, command fails fast with `status="needs_auth"`, `facts.interactive_required=true`. |
| Azure CLI returns `AADSTS50076` (MFA required) | Fail fast with `status="needs_auth"`, include tenant + user info, and emit `next[]` steps describing how to create/use a service principal or managed identity per Microsoft guidance. |

## References

- GitHub CLI manual: [`gh auth login`](https://cli.github.com/manual/gh_auth_login), [`gh auth status`](https://cli.github.com/manual/gh_auth_status), [`gh auth refresh`](https://cli.github.com/manual/gh_auth_refresh)
- Azure DevOps CLI auth documentation (overview): [Azure DevOps CLI – Get started](https://learn.microsoft.com/en-us/azure/devops/cli/?view=azure-devops)
- PAT guidance: [Microsoft Learn – Azure DevOps PATs](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate)
```