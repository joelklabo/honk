# Azure CLI & Azure DevOps Authentication Reference

_Last reviewed: 2025-11-17_

## Authentication modes in `az`

| Scenario | Recommended command | Notes |
| --- | --- | --- |
| Interactive development | `az login` | Opens browser; supports subscription picker. [Docs](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest) |
| Device/browser-less login | `az login --use-device-code` | CLI prints a device code for headless hosts; still Entra-backed. |
| Managed identity (Azure resources) | `az login --identity` with optional `--client-id/--object-id/--resource-id` | No secrets managed; only available from resources with managed identity enabled. [Docs](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-managed-identity?view=azure-cli-latest) |
| Service principal (automation) | `az login --service-principal --username <app-id> --password <secret|@/path/to/file> --tenant <tenant>` | Preferred for CI automation once MFA enforcement rolls out. Certificates supported via `--certificate`. [Docs](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-service-principal?view=azure-cli-latest) |
| Cloud Shell | Implicit login | No auth prompts; good for quick tests. |

### MFA enforcement impact

- Beginning September 2025, Microsoft mandates MFA for Entra user identities in CLI flows. Any automation that still relies on `az login --username --password` or ROPC must migrate to managed identities, service principals, or federated identities. [Guidance](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-mfa?view=azure-cli-latest)
- MFA errors typically show up as `AADSTS50076`; resolve by switching auth mechanism or specifying `--tenant` when cross-tenant prompts block login.

## Token lifecycle and refresh

- User logins store both access tokens and refresh tokens on disk. Use `az account get-access-token [--resource ...] [--subscription ...]` to emit the current bearer. Output includes both `expiresOn` (local time) and `expires_on` (POSIX) since Azure CLI 2.54.0.
- Refresh tokens rotate automatically whenever `az` successfully redeems them; expect 1 hour access token TTL by default.
- The CLI honors Conditional Access policies; token acquisition may fail if policy blocks interactive device.

### Microsoft Entra tokens for Azure DevOps

- To call Azure DevOps REST APIs without PATs, reuse your CLI session: `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv`. [Docs](https://learn.microsoft.com/en-us/azure/devops/cli/entra-tokens?view=azure-devops)
- Tokens last 1 hour; ideal for one-off automation or rotating credentials in CI.

## Azure DevOps CLI extension (`az devops`)

1. Install/update: `az extension add --name azure-devops` (or `update`). [Quickstart](https://learn.microsoft.com/en-us/azure/devops/cli/?view=azure-devops)
2. Configure defaults: `az devops configure --defaults organization=https://dev.azure.com/<org> project=<Project>`.
3. Authentication paths:
   - **Entra-backed**: run `az login` (interactive/device/service principal) first; `az devops` reuses that context when permitted.
   - **PAT-based**: `az devops login --organization <url>` and paste PAT at prompt.
   - **Non-interactive PAT**:
     - Pipe token: `echo $PAT | az devops login --organization ...`
     - File input: `cat token.txt | az devops login --organization ...`
     - Environment variable: set `AZURE_DEVOPS_EXT_PAT` before running commands; the extension consumes it automatically. [PAT login](https://learn.microsoft.com/en-us/azure/devops/cli/log-in-via-pat?view=azure-devops)
4. Guest users must use `az devops login` (PAT) even if `az login` succeeds elsewhere.
5. DevOps extension cannot use Managed Identities as of 2025; rely on PAT or Entra tokens.

## Personal Access Tokens (PATs) for Azure DevOps

- Creation: User settings → Personal access tokens → `+ New Token`; pick org, scope(s), expiration (max 1 year unless admin policy shortens). [Guide](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops)
- Best practices:
  - Prefer Microsoft Entra tokens when possible; PATs are a fallback for tools lacking Entra support.
  - Use least-privilege scopes (e.g., Agent Pools, Packaging, Code) per workflow.
  - Keep lifetimes short (weekly/30-day) and rotate regularly.
  - Store tokens in secure vaults; never commit them. Azure DevOps auto-revokes leaked PATs if tenant policy enables it.
- Lifecycle operations:
  - Extend/regenerate via UI (creates new string, invalidates previous).
  - Revoke via UI or admin APIs; recommended when user leaves or integration retires.
  - Admins can enforce policies restricting PAT scope/duration and auto-revoke leaked secrets.
- Automation options:
  - Use `AZURE_DEVOPS_EXT_PAT` or pipeline secret variables to supply tokens.
  - PAT Lifecycle Management REST APIs accept Entra access tokens plus `vso.pats` scope to enumerate/create/revoke tokens programmatically (user-context only).
  - For PAT rotation: GET metadata, POST new PAT (reusing ID), DELETE old PAT.
- Format update: as of July 2024 PATs are 84 chars long with `AZDO` signature at positions 76-80; older 52-char tokens remain valid but should be regenerated.

## Managed identities vs service principals

| Identity | Strengths | Limitations |
| --- | --- | --- |
| System-assigned managed identity | Zero-secret, lifecycle bound to resource, ideal for single-resource automation | Cannot authenticate off-resource; limited to Azure-hosted workloads |
| User-assigned managed identity | Reusable across resources; still secretless | Must deploy identity resource & assign roles |
| Service principal + secret | Works anywhere, supports granular RBAC, good for cross-cloud automation | Secrets/certs must be rotated; ensure safe storage |
| Service principal + certificate | Stronger security, integrates with Key Vault | Slightly more setup (PEM bundling) |

Use `az ad sp create-for-rbac` (not covered above) to mint principals, then pass details to `az login --service-principal`.

## Troubleshooting checklist

- `Interactive authentication is needed`: indicates MFA requirement; migrate to workload identities.
- `Authentication failed against tenant ...` during `az login`: specify tenant explicitly via `--tenant <GUID>`.
- PAT rejected by CLI: ensure PAT not expired, organization matches `--organization`, and account has Basic access.
- `az devops` commands failing in CI: confirm `AZURE_DEVOPS_EXT_PAT` is set for process, or run `az login` beforehand and ensure CLI profile stored via `az account show`.

## References

1. [Authenticate to Azure using Azure CLI](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest)
2. [Azure CLI MFA impact](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-mfa?view=azure-cli-latest)
3. [Service principal login](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-service-principal?view=azure-cli-latest)
4. [Managed identity login](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-managed-identity?view=azure-cli-latest)
5. [Azure DevOps CLI quickstart](https://learn.microsoft.com/en-us/azure/devops/cli/?view=azure-devops)
6. [Sign in via Azure DevOps PAT](https://learn.microsoft.com/en-us/azure/devops/cli/log-in-via-pat?view=azure-devops)
7. [Issue Entra tokens with Azure CLI](https://learn.microsoft.com/en-us/azure/devops/cli/entra-tokens?view=azure-devops)
8. [Use personal access tokens](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops)
