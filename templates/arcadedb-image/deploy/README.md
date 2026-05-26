# ArcadeDB ACA Deploy — Bootstrap & Operations Guide

> **Hub-owned, fleet-shared platform deploy ([ARC-ADR-023](../../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md)).** The AgentArmy hub owns the deployment of the **shared** ArcadeDB platform instance for the whole fleet. Spokes do NOT run their own ArcadeDB — they consume the URL emitted by this deploy via env (`ARCADEDB_URL`). One database, one source of truth.

This directory contains everything needed to deploy `agentarmy-arcadedb` to
Azure Container Apps with persistent storage, Key Vault-backed secrets, and a
fully automated OIDC GitHub Actions pipeline. The **runnable workflow lives at
[`.github/workflows/arcadedb-aca-deploy.yml`](../../../.github/workflows/arcadedb-aca-deploy.yml)** (hub-owned, hub-triggered). The files in this directory are the deploy lane's bicep, parameters, and bootstrap scripts — referenced by the workflow.

---

## Files

| File | Purpose |
|---|---|
| `arcadedb-aca.bicep` | Full infrastructure: Storage Account, Azure Files shares, ACA environment (optional), Container App with system identity, KV + ACR RBAC. |
| `arcadedb-aca-parameters-dev.bicepparam` | Dev-environment defaults. Override `acrLoginServer` and `projectName` if forking the deploy lane. |
| `bootstrap.sh` | One-time setup (Bash / WSL / Git Bash). Run once per resource group to seed RBAC + secrets. |
| `bootstrap.ps1` | One-time setup (PowerShell 7 / pwsh). |
| (in hub `.github/workflows/`) `arcadedb-aca-deploy.yml` | The actual GitHub Actions workflow — runs from the hub. Builds image, pushes to ACR, applies bicep. |

---

## What gets deployed

```
Resource Group: rg-arcadedb-dev
  Storage Account: st<projectname>devsa
    File Share: arcadedb-databases   (32 GiB)   -> /home/arcadedb/databases
    File Share: arcadedb-config      ( 4 GiB)   -> /home/arcadedb/config
  Container Apps Environment: cae-<projectname>-dev  (created if not supplied)
    ACA Storage: arcadedb-databases  (bound to above share)
    ACA Storage: arcadedb-config     (bound to above share)
  Container App: ca-arcadedb-dev
    Image: <acr>/agentarmy-arcadedb:<tag>
    Ingress: external, port 2480, HTTPS
    Replicas: min=1 / max=1  (single writer, never scales to zero)
    Identity: SystemAssigned
    Probes: liveness + readiness + startup on GET /api/v1/ready (204)
Key Vault: akv01-agentarmy  (existing)
  RBAC: Container App identity -> Key Vault Secrets User
ACR: <acrName>  (existing)
  RBAC: Container App identity -> AcrPull
```

---

## One-time bootstrap

The bootstrap script (Bash or PowerShell) handles all of the steps below.
Run it once from a workstation where `az` is authenticated with Contributor
and Key Vault Secrets Officer rights on the subscription.

### Bash (Linux / macOS / WSL / Git Bash)

```bash
chmod +x templates/arcadedb-image/deploy/bootstrap.sh

templates/arcadedb-image/deploy/bootstrap.sh \
  --subscription  00000000-0000-0000-0000-000000000000 \
  --resource-group rg-arcadedb-dev \
  --location       eastus \
  --acr-name       myacr \
  --aca-env-name   cae-backend-dev \
  --keyvault-name  akv01-agentarmy \
  --github-org     nickpclarke \
  --github-repo    backend-core
```

### PowerShell (Windows / pwsh)

```powershell
templates\arcadedb-image\deploy\bootstrap.ps1 `
  -Subscription  '00000000-0000-0000-0000-000000000000' `
  -ResourceGroup 'rg-arcadedb-dev' `
  -AcrName       'myacr' `
  -AcaEnvName    'cae-backend-dev' `
  -KeyVaultName  'akv01-agentarmy' `
  -GitHubOrg     'nickpclarke' `
  -GitHubRepo    'backend-core'
```

Both scripts are **idempotent** — safe to re-run; existing resources are detected
and skipped.

---

## What the bootstrap creates

### 1. Resource group + ACR

The resource group `rg-arcadedb-dev` (or whatever you supply) and a Basic-tier ACR.
Admin credentials on the ACR are disabled; the Container App pulls via its system
identity (AcrPull RBAC, assigned by the Bicep).

### 2. ACA environment

A new Consumption-tier ACA environment backed by Log Analytics. If you already have
an environment, pass its name as `containerAppsEnvironmentName` in the parameters
file and skip this step — the Bicep will join the existing environment.

### 3. Key Vault secrets

Two randomly-generated passwords are written to `akv01-agentarmy`:

| Secret name | Used as |
|---|---|
| `arcadedb-root-password` | ArcadeDB `root` admin (bootstrap only; not exposed externally). |
| `arcadedb-service-password` | `platform_reader` read-only user (UDA connection). |

**Password constraint:** the service password must not contain the characters
`: [ ] { }` — they are ArcadeDB `defaultDatabases` delimiters and will corrupt the
user-provisioning command at first boot. The bootstrap scripts exclude these
characters from the generated password. If you supply your own password, enforce the
same constraint.

If the secrets already exist, the bootstrap leaves them unchanged.

### 4. OIDC federated credential

An Entra ID app registration `sp-arcadedb-aca-deploy-<repo>` with:
- Contributor on the resource group
- Key Vault Secrets User on `akv01-agentarmy`
- Two OIDC federated credentials scoped to `refs/heads/main` of the spoke repo

---

## Add secrets + variables to the spoke repo

After bootstrap, the script prints the exact values. Add them in
**Settings > Secrets > Actions**:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | App registration client ID |
| `AZURE_TENANT_ID` | Entra ID tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |

Add these in **Settings > Variables > Actions** (not secrets — they are non-sensitive):

| Variable | Value |
|---|---|
| `AZURE_ACR_LOGIN_SERVER` | e.g. `myacr.azurecr.io` |
| `AZURE_RESOURCE_GROUP` | e.g. `rg-arcadedb-dev` |

---

## Install the workflow

Copy the workflow template into the spoke:

```bash
cp templates/arcadedb-image/deploy/arcadedb-aca-deploy.yml \
   .github/workflows/arcadedb-aca-deploy.yml
```

Then push to `main`. The workflow triggers on:
- `push` to `main` when any file under `templates/arcadedb-image/` changes
- `workflow_dispatch` (manual run with optional image tag + environment)

---

## Connecting backend-core's Universal Data Adapter

After the first successful deploy, the workflow summary prints the FQDN.
Register a UDA connection in backend-core using:

```yaml
# Example UDA connection config (adjust to your UDA config format)
arcadedb_dev:
  type: arcadedb
  url: "https://<fqdn>/api/v1"
  database: knowledge
  user: platform_reader
  # secret_ref tells the UDA to resolve the password from Key Vault at runtime
  secret_ref: "akv:arcadedb-service-password"
```

The `akv:` prefix is a convention — the UDA resolves the value from the same Key
Vault (`akv01-agentarmy`) the Container App uses. The UDA's managed identity must
have `Key Vault Secrets User` on the vault (the bootstrap grants this for the deploy
identity; grant it separately for the UDA's identity if it is different).

The MCP endpoint is available at `https://<fqdn>/api/v1/mcp` authenticated with the
`platform_reader` Basic credentials.

---

## Verifying the deployment

```bash
# Health (no auth — should return HTTP 204)
curl -i https://<fqdn>/api/v1/ready

# Studio (opens in browser — requires root or admin credentials)
open https://<fqdn>
```

The smoke-test step in the workflow polls `/api/v1/ready` for up to 3 minutes after
Bicep deployment succeeds. ArcadeDB's JVM cold-start on first boot can take 45-60 s.

---

## Operational notes

- **Single writer.** `minReplicas=1` / `maxReplicas=1` is intentional. ArcadeDB is an
  embedded engine — multiple replicas sharing the same Azure Files mount would
  corrupt data.

- **Volume pairing.** The Bicep mounts both `databases/` and `config/` from the
  same storage account. This is required: `config/server-users.jsonl` (where
  `platform_reader` lives) and the actual database files in `databases/` must be
  co-located or they desync on container recycle.

- **MCP posture.** The `config/mcp-config.json` baked into the image is re-applied
  on every boot even on a persisted `config/` volume, so the read-only posture is
  never accidentally overwritten.

- **Updating the image.** Push a new tag to ACR (the workflow does this automatically)
  then re-run the workflow (or push to `main`). The Bicep `--parameters imageTag=<tag>`
  updates the Container App to a new revision; ACA performs a zero-downtime swap.
  Because `minReplicas=1` the old revision stays active until the new one is healthy.

- **Teardown.** Delete the resource group to remove all resources:
  ```bash
  az group delete --name rg-arcadedb-dev --yes --no-wait
  ```
  The Key Vault secrets are in `akv01-agentarmy` (shared vault) — delete them
  separately if you no longer need them.

- **Shared vs spoke-specific vault.** This template defaults to the hub's shared
  `akv01-agentarmy`. If your spoke has its own vault, pass `--keyvault-name` to
  bootstrap and update `keyVaultName` in the parameters file.
