# GitHub CLI Authentication Reference

_Last reviewed: 2025-11-17_

## Core commands

| Command | Purpose | Key flags & behaviors |
| --- | --- | --- |
| `gh auth login` | Enroll an account/host | Defaults to browser OAuth; supports `--web`, `--with-token` (classic PAT from stdin), `--hostname`, `--git-protocol {ssh|https}`, `--scopes`, `--skip-ssh-key`. [Manual](https://cli.github.com/manual/gh_auth_login) |
| `gh auth status` | Inspect stored credentials | `--json hosts`, `--show-token`, `--active`, `--hostname`. Non-zero exit if any account broken (unless `--json`). [Manual](https://cli.github.com/manual/gh_auth_status) |
| `gh auth refresh` | Add/remove scopes or reissue token | `--scopes`, `--remove-scopes`, `--reset-scopes`, `--hostname`, `--clipboard`. Maintains minimum `repo`, `read:org`, `gist`. [Manual](https://cli.github.com/manual/gh_auth_refresh) |
| `gh auth switch` | Change active account per host | `--hostname`, `--user`. Needed before refreshing inactive accounts. [Manual](https://cli.github.com/manual/gh_auth_switch) |
| `gh auth token` | Print active token | Accepts `--hostname` and `--user`; useful for passing tokens to other tools securely via subshells. [Manual](https://cli.github.com/manual/gh_auth_token) |
| `gh auth logout` | Remove local credentials | Does **not** revoke tokens server-side; visit Settings → Applications to revoke “GitHub CLI” OAuth grant. [Manual](https://cli.github.com/manual/gh_auth_logout) |

## Authentication flows

1. **Browser-based OAuth (default)**
   - CLI launches device/browsers; stores fine-grained `gh` token in OS credential store (Keychain, Windows Credential Manager, libsecret).
   - If credential store unavailable, falls back to plaintext file location exposed via `gh auth status`.
   - Optionally copy one-time device code to clipboard using `--clipboard`.

2. **Token input**
   - Pipe a classic PAT (`repo`, `read:org`, `gist` minimum) via `--with-token < mytoken.txt`.
   - For fine-grained PATs, prefer setting `GH_TOKEN` directly to avoid scope mismatch warnings.

3. **Environment-only usage**
   - Set `GH_TOKEN`/`GITHUB_TOKEN` (for github.com) or `GH_ENTERPRISE_TOKEN`/`GITHUB_ENTERPRISE_TOKEN` for GHE hosts. [Environment reference](https://cli.github.com/manual/gh_help_environment)
   - `GH_HOST` defines default hostname if not inferable from git remotes; combine with token env vars for headless CI.

4. **SSH assist**
   - During `gh auth login --git-protocol ssh` the CLI detects existing keys, offers to upload or generate new ones, and updates Git remotes accordingly.

## Multi-account & enterprise considerations

- Each authenticated host can hold multiple accounts. `gh auth status` highlights the active one; `gh auth switch --hostname <host> --user <handle>` rotates focus.
- `gh auth login --hostname <ghe.company.com>` enrolls GitHub Enterprise Server ≥ 2.20. Set `GH_HOST` or use `--hostname` per command.
- For automation hitting multiple hosts, export `GH_HOST` and host-specific tokens via environment variables to avoid interactive prompts.

## Scope management strategy

- Minimum scopes when using OAuth/classic PAT with CLI-managed tokens: `repo`, `read:org`, `gist`.
- Augment scopes for advanced tasks (`workflow`, `write:packages`, `admin:org`) via `gh auth refresh --scopes ...`.
- Remove scopes cleanly via `gh auth refresh --remove-scopes scope1,scope2`; CLI re-opens OAuth consent.
- `--reset-scopes` re-authenticates with minimum set if cleanup is required.

## Token inspection & export

- Run `gh auth status --json hosts --show-token` for structured summary including hostnames, usernames, and masked tokens.
- `gh auth token` prints the raw token; combine with process substitution to feed other tools (e.g., `export GITHUB_TOKEN=$(gh auth token)` inside subshells). Avoid storing plaintext tokens on disk.

## Logout and revocation workflow

1. `gh auth logout --hostname <host> --user <handle>` removes local credentials.
2. To fully revoke OAuth grant, visit `https://github.com/settings/applications` → “GitHub CLI” → “Revoke”.
3. For fine-grained PATs used with env vars, delete them in the GitHub UI or use REST API to revoke.

## Automation tips

- Disable prompts with `GH_PROMPT_DISABLED=1` when feeding tokens non-interactively.
- Use `GH_PROMPT_DISABLED` plus `GH_TOKEN` inside GitHub Actions (set `GH_TOKEN: ${{ github.token }}`) to reuse the workflow’s job token.
- For scripting multiple hosts, rely on `gh auth status --json` + `jq` to detect expired/broken logins and re-run `gh auth refresh` as needed.
- Set `GH_CONFIG_DIR` to isolate credentials per project or environment (e.g., ephemeral CI workspaces).

## Troubleshooting

| Symptom | Likely cause | Mitigation |
| --- | --- | --- |
| `Authentication failed for <host>` from git | Git remote URL uses HTTPS but CLI configured for SSH or vice versa | Rerun `gh auth login` and pick desired git protocol, or set via `gh config set git_protocol ssh` |
| `Scopes are insufficient` when calling APIs | Token lacks required scope | `gh auth refresh --scopes <needed>` or issue new PAT |
| `gh auth status` exits 1 | At least one host/account invalid | Re-run login/refresh for flagged host; use `--json hosts --jq '.hosts | add'` for automation-friendly parsing |
| Device code expires | Browser not completed in time | Re-run `gh auth login --web --clipboard` |

## References

1. [gh auth login](https://cli.github.com/manual/gh_auth_login)
2. [gh auth status](https://cli.github.com/manual/gh_auth_status)
3. [gh auth refresh](https://cli.github.com/manual/gh_auth_refresh)
4. [gh auth switch](https://cli.github.com/manual/gh_auth_switch)
5. [gh auth token](https://cli.github.com/manual/gh_auth_token)
6. [gh auth logout](https://cli.github.com/manual/gh_auth_logout)
7. [Environment variables](https://cli.github.com/manual/gh_help_environment)
