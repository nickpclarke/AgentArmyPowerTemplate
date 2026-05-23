# GCP Cloud Run Container Pipeline

Drop-in tooling for building a container and shipping it to **Google Cloud Run**
across **segregated landscapes** (dev / qa / uat / prod), with **keyless** auth
(Workload Identity Federation), **Google Secret Manager** for runtime secrets,
**feature flags** woven through every environment, and **Terraform** as the
recommended IaC path.

Two CI engines are provided — use whichever your spoke prefers:

- **GitHub Actions** — reusable workflow `.github/workflows/gcp-cloud-run-deploy.yml` (in the Hub repo)
- **Cloud Build** — `cloudbuild.yaml` in this folder

## Files

| File | Purpose |
|---|---|
| `terraform/` | **Recommended.** Provisions Artifact Registry, deploy + runtime service accounts, Workload Identity Federation, Secret Manager secrets, feature-flag env, and the Cloud Run service. |
| `terraform/environments/*.tfvars` | One file per landscape (dev/qa/uat/prod): project, flags, secrets, scaling. |
| `terraform/Makefile` | `make ENV=prod apply` — targets a landscape with isolated state. |
| `setup/bootstrap-wif.sh` | No-Terraform quickstart for the same IAM/WIF/registry bootstrap via `gcloud`. |
| `cloudbuild.yaml` | Cloud Build pipeline: build → push → deploy (with optional Secret Manager wiring). |
| `github-actions-caller.yml` | Example caller a spoke drops into `.github/workflows/deploy.yml` (dev→qa→uat→prod promotion). |
| `Dockerfile` / `.dockerignore` | Example container that listens on `$PORT` (Cloud Run requirement). |

## Quick start (Terraform, recommended)

```bash
cd terraform
# Edit the landscape you want, then apply it with isolated state:
make ENV=dev apply
```

`make` initialises a per-environment state prefix (`cloud-run/<service>/<env>`)
and applies `environments/<env>.tfvars`, so dev/qa/uat/prod never collide. Then
set the two GitHub repo (or environment) secrets from the outputs:

```bash
make ENV=dev output
# workload_identity_provider -> WORKLOAD_IDENTITY_PROVIDER (repo/env secret)
# deploy_service_account     -> DEPLOY_SERVICE_ACCOUNT     (repo/env secret)
# runtime_service_account    -> service_account input
# set_secrets_flag           -> set_secrets input
# feature_flags_rendered     -> FLAG_* env the service sees
```

## Quick start (no Terraform)

```bash
PROJECT_ID=my-gcp-project GITHUB_REPO=owner/my-api-spoke \
  ./setup/bootstrap-wif.sh
```

It prints the same secret values to add to the spoke repo.

## Wire up a spoke (GitHub Actions)

1. Copy `github-actions-caller.yml` to the spoke's `.github/workflows/deploy.yml`
   and edit `project_id`, `service`, etc.
2. Add repo secrets `WORKLOAD_IDENTITY_PROVIDER` and `DEPLOY_SERVICE_ACCOUNT`.
3. Push to `main` — the reusable workflow builds, pushes to Artifact Registry,
   and deploys to Cloud Run. The caller MUST grant `id-token: write` (keyless auth)
   and pass `secrets: inherit`.

## Secret Manager

- Terraform creates a secret container per entry in the `secrets` map and grants
  the **runtime** service account `secretmanager.secretAccessor`.
- Add secret *values* out of band so they stay out of state:
  `echo -n "s3cr3t" | gcloud secrets versions add db-password --data-file=-`
- At deploy time, secrets are mounted as env vars via the `set_secrets` input
  (GitHub Actions) or `_SET_SECRETS` substitution (Cloud Build), format:
  `ENV_NAME=secret-id:latest,OTHER=other-id:latest`.

## Landscapes (dev / qa / uat / prod)

Each environment is its own segregated landscape:

- **Infra/state** — `environments/<env>.tfvars` + a per-env state prefix
  (`make ENV=<env> apply`). The default model is **one GCP project per
  environment** (full isolation); for a shared project, give each env a distinct
  `service_name`.
- **CI** — each landscape maps to a **GitHub Environment** (`dev`/`qa`/`uat`/`prod`).
  Put that env's `WORKLOAD_IDENTITY_PROVIDER` + `DEPLOY_SERVICE_ACCOUNT` as
  environment-scoped secrets, and add required reviewers on `prod` to gate it.
- **Promotion** — the caller deploys dev→qa→uat automatically, then `prod` after
  approval (see `github-actions-caller.yml`).

## Feature flags (across layers)

Flags are a first-class, **vendor-neutral** concept here:

- Declare them per landscape in `feature_flags` (a `map(bool)`). Terraform renders
  them into the service as `FLAG_<NAME>` env vars (e.g. `FLAG_NEW_CHECKOUT=true`),
  so an app reads flags the same way in every layer — no SDK required.
- Promote a flag left-to-right (dev→qa→uat→prod) by flipping it in each tfvars,
  giving you a simple, auditable progressive-delivery story in git.
- **Upgrade path:** when you outgrow boolean env flags (targeting rules,
  percentage rollouts, kill switches), keep the same `FLAG_*` contract and back it
  with a managed provider (OpenFeature + LaunchDarkly/Flagsmith/GrowthBook).
  Route that work to the `feature-flag-engineer` agent.

## Why keyless?

No long-lived JSON keys to leak or rotate. The Workload Identity provider is
scoped to a single `owner/repo`, so only that repo can impersonate the deployer
service account. See `gcp-infra-engineer` for the GCP-side conventions.

## Why not Bicep?

Bicep is Azure-only (it compiles to ARM templates) and cannot provision GCP
resources. Terraform is the right IaC here and also covers Azure/AWS if you add
spokes on other clouds later. For an Azure Container Apps spoke, use the
`azure-infra-engineer` agent and Bicep instead.
