# ACA GitHub Runner — Ephemeral Self-Hosted CI

Scale-to-zero GitHub Actions self-hosted runners on Azure Container Apps Jobs.
One runner container per queued workflow job; zero cost when idle.

---

## How it works

```
GitHub Actions queue
       │
       │  KEDA polls queue length every 30 s
       ▼
  ┌─────────────────────────────────────────────────┐
  │  Container Apps Environment (Consumption tier)  │
  │                                                 │
  │  Job: job-runner-agentarmy-AgentArmy-ci         │
  │  Job: job-runner-agentarmy-frontend-core-ci     │  ← one Job per repo
  │  Job: job-runner-agentarmy-backend-core-ci      │
  │  Job: job-runner-agentarmy-middle-core-ci       │
  │                                                 │
  │  KEDA github-runner scaler                      │
  │    queueLength >= 1  →  start execution         │
  │    queueLength == 0  →  scale to zero           │
  └─────────────────────────────────────────────────┘
       │
       │  Each execution (= one container):
       ▼
  entrypoint.sh
    1. POST /repos/:owner/:repo/actions/runners/registration-token
    2. ./config.sh --ephemeral --url ... --token <reg-token>
    3. exec ./run.sh   ← runs exactly ONE workflow job, then exits
       │
       └──▶  runner deregisters, container exits 0, ACA marks execution complete
             KEDA sees queue depth decrease, next poll may scale to zero
```

Runners are **ephemeral**: they register, run one job, and exit. No persistent runner
state accumulates. Each new job gets a clean container from the pinned image.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Azure CLI + containerapp extension | `az extension add --name containerapp` |
| _(no local Docker)_ | The image is built server-side by ACR Tasks (`az acr build`) — runs from Azure Cloud Shell or any az-authenticated shell, no daemon needed |
| Subscription **AASub1** | `az account set --subscription AASub1` |
| ACR **agentarmy.azurecr.io** | Shared registry, already exists |
| Key Vault **akv01-agentarmy** | Shared vault, already exists |
| GitHub classic PAT | `repo` scope — see PAT scope section below |
| Resource group for runners | e.g. `rg-github-runner-ci` |

---

## GitHub PAT scope

Use a **classic Personal Access Token** (fine-grained tokens do not yet support
the Actions runner registration API for user accounts).

Required scope: **`repo`** (full repository access).

This grants the PAT permission to:
- List and create self-hosted runner registration tokens (`POST .../registration-token`).
- Read workflow queue status (used by KEDA to determine queue length).

The same PAT you may already have in the Key Vault under `GHRUNNERPAT` can be
reused if it has `repo` scope. The deploy script will skip Key Vault secret creation
if the secret already exists.

**Important:** because `nickpclarke` is a GitHub **user account** (not an
organisation), runners are registered per-repo (`runnerScope: repo`). Organisation
runners would use a single org-level PAT; per-repo registration is the only option
for user accounts.

---

## Security model

| Control | Detail |
|---|---|
| Ephemeral runners | Each container runs one job, then exits. No state persists between jobs. |
| Scale-to-zero | `minExecutions: 0` — no containers run when the queue is empty. Zero idle cost. |
| Managed identity | A user-assigned identity pulls the image from ACR and resolves the KV secret. No stored credentials anywhere. |
| Key Vault-backed PAT | The GitHub PAT lives in Key Vault. ACA resolves it at runtime via `keyVaultUrl` + identity reference. The value never appears in the Bicep template, deployment output, or container logs. |
| Non-root container | Runner process runs as uid 1001 (`runner` user). The runner binary enforces this by default. |
| No docker-in-docker | Azure Container Apps does not support privileged containers. Workflows that need container builds must use ACR Tasks or a separate build step. |
| Private repos only | These runners are scoped to the four private repos under `nickpclarke`. Never attach self-hosted runners to public repositories (untrusted code runs on your infrastructure). |
| Least-privilege RBAC | The managed identity has `AcrPull` on the ACR and `Key Vault Secrets User` on the Key Vault — nothing else. |

---

## Cost

| State | Cost |
|---|---|
| Idle (no queued jobs) | **~$0** — scale-to-zero; no executions running |
| Active (1 runner, 1 vCPU / 2 Gi) | ~$0.000024/vCPU-s + ~$0.000003/GiB-s (Consumption tier, eastus, May 2026) |
| Example: 10 min job | ≈ $0.02 per execution |

The Log Analytics workspace (30-day retention) is the only standing cost:
approximately $2–5/month depending on log volume.

---

## Deploy

```bash
# 1. Clone the hub or copy this template directory to your workstation.
cd templates/aca-github-runner

# 2. Authenticate to Azure.
az login
az account set --subscription AASub1

# 3. Run the deploy script (it will prompt before applying changes).
./deploy.sh \
  --subscription    <your-subscription-id>  \
  --resource-group  rg-github-runner-ci     \
  --location        eastus                  \
  --acr-name        agentarmy               \
  --keyvault-name   akv01-agentarmy         \
  --runner-version  2.317.0                 \
  --create-rg
```

The script:
1. Sets the subscription context.
2. Creates the resource group if `--create-rg` is passed.
3. Checks whether `GHRUNNERPAT` exists in Key Vault; prompts for the value if not.
4. Builds and pushes the runner image to ACR.
5. Runs `az deployment group what-if` so you can review changes before they apply.
6. Asks for confirmation, then runs `az deployment group create`.

### Registries without AAD data-plane auth

Some registries don't honor Azure-AD data-plane auth for image **pull or push** —
the managed-identity pull and `az acr build` both fail with `UNAUTHORIZED:
authentication required`, even when the caller has `AcrPush`/`Owner`. (This is the
case for the shared `agentarmy` registry, which is why the fleet pulls via the
`acr-pwd` admin secret — cf. ARC #179.) For these, build the image once where a
Docker push works, then deploy the already-pushed image with admin Basic-auth:

```bash
./deploy.sh \
  --subscription   AASub1                 \
  --resource-group rg-arcade-platform     \
  --acr-name       agentarmy              \
  --keyvault-name  akv01-agentarmy         \
  --skip-build                             \   # the build's push hits the same AAD wall
  --image-tag      2.334.0-tools           \   # an already-pushed tag
  --acr-admin                                  # pull via ACR admin user/password
```

`--acr-admin` reads the registry's admin user/password (`az acr credential show`)
and passes them as the `acrUsername` / `acrPassword` bicep params; the password is
stored only as an ACA secret, never echoed or written to the template. The admin
user must be enabled (`az acr update -n <acr> --admin-enabled true`).

---

## Updating workflows to use these runners

After deployment, each workflow that should run on the self-hosted fleet must
change its `runs-on` label. This is a **separate, manual step** in each spoke repo
and is not done automatically by this template.

Change:

```yaml
runs-on: ubuntu-latest
```

to:

```yaml
runs-on: [self-hosted, aca-linux]
```

Both labels must be present. `self-hosted` tells GitHub to route the job to a
registered self-hosted runner. `aca-linux` is the discriminator that matches the
runners created by this template; it prevents jobs from landing on any other
self-hosted runner that may be registered.

Until a workflow is updated, it continues to consume GitHub-hosted minutes.
Update workflows in whichever repos are exhausting minutes first.

---

## Reusing an existing ACA environment

By default the Bicep template creates a dedicated Consumption-tier environment
(`cae-agentarmy-ci-runner`) and a Log Analytics workspace.

To co-locate runners with an existing environment (e.g. the ArcadeDB dev
environment `cae-agentarmy-dev`), set `containerAppsEnvironmentName` in
`main.bicepparam`:

```bicep
param containerAppsEnvironmentName = 'cae-agentarmy-dev'
```

When a name is provided, no Log Analytics workspace or ACA environment is created
by this template. The existing environment's log sink is used.

---

## Updating the runner version

The runner binary version is pinned via `ARG RUNNER_VERSION` in the Dockerfile.
To upgrade:

```bash
./deploy.sh \
  --subscription   <id>   \
  --resource-group rg-github-runner-ci \
  --acr-name       agentarmy \
  --runner-version 2.319.0 \
  --image-tag      2.319.0
```

Then update `imageTag` in `main.bicepparam` (or pass `--parameters imageTag=2.319.0`
at deploy time). Old executions that are already running are not affected; new
executions pick up the new image immediately.

---

## Monitoring

```bash
# List recent Job executions for a specific repo runner
az containerapp job execution list \
  --resource-group rg-github-runner-ci \
  --name job-runner-agentarmy-AgentArmy-ci \
  --output table

# Stream logs from the most recent execution
az containerapp job logs show \
  --resource-group rg-github-runner-ci \
  --name job-runner-agentarmy-AgentArmy-ci \
  --follow

# Check KEDA scale rule status (requires containerapp extension >= 0.3.47)
az containerapp job show \
  --resource-group rg-github-runner-ci \
  --name job-runner-agentarmy-AgentArmy-ci \
  --query "properties.configuration.eventTriggerConfig.scale" \
  --output json
```

Log Analytics queries (via Azure Portal or `az monitor log-analytics query`):

```kusto
// All runner execution starts in the last 24 hours
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where ContainerName_s == "runner"
| where Log_s has "configuring runner"
| project TimeGenerated, ContainerJobName_s, Log_s
| order by TimeGenerated desc
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Execution never starts | KEDA cannot reach GitHub API | Check PAT scope; verify KV secret resolves via `az keyvault secret show --vault-name akv01-agentarmy --name GHRUNNERPAT` |
| `exit 127` in container | CRLF in `entrypoint.sh` | The Dockerfile strips CRLF with `sed -i 's/\r$//'`; ensure `.gitattributes` is committed and `git checkout` is clean |
| `FATAL: failed to obtain registration token` | PAT missing `repo` scope or expired | Rotate PAT in GitHub → update Key Vault secret (`az keyvault secret set ...`) |
| Image pull fails | AcrPull not assigned | Re-run Bicep deploy; the role assignment is idempotent |
| Job execution stuck in `Running` for > 30 min | Job timed out | `replicaTimeout: 1800` (30 min); increase if workload is known to be slower |
| Runners accumulate in repo Settings | `--ephemeral` flag missing | Entrypoint.sh passes `--ephemeral` to `config.sh`; rebuild the image |

---

## Files in this template

| File | Purpose |
|---|---|
| `main.bicep` | Bicep template: identity, RBAC, ACA environment (optional), one Job per repo |
| `main.bicepparam` | Default parameter values for the nickpclarke fleet |
| `Dockerfile` | Runner image: Ubuntu 22.04, pinned runner binary, non-root user |
| `entrypoint.sh` | Container entrypoint: mint registration token, configure ephemeral runner, exec run.sh |
| `deploy.sh` | Operator script: build image, ensure KV secret, what-if preview, deploy |
| `.gitattributes` | Forces LF line endings on all shell scripts (prevents exit 127 from CRLF shebangs) |

---

## Relationship to other templates

| Template | Concern |
|---|---|
| `templates/azure-container-apps-dev/` | Application workload deployment (dev lane). Different purpose: deploys your service containers. |
| `templates/arcadedb-image/deploy/` | ArcadeDB database on ACA. Uses the same managed identity + KV reference pattern. |
| `templates/gcp-cloud-run/` | GCP equivalent CI/CD pipeline. Different cloud, different runner approach. |

This template is MECE with `azure-container-apps-dev/`: that template deploys
application workloads; this template hosts the CI runner infrastructure that runs
those deployment workflows.
