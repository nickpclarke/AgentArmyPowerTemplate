# GCP Container Pipeline (Cloud Run)

Reusable tooling to build a container and deploy it to **Google Cloud Run** across
**segregated landscapes** (dev/qa/uat/prod), with **keyless** auth (Workload
Identity Federation), **Google Secret Manager** for runtime secrets, **feature
flags** woven through every environment, and **Terraform** as the recommended IaC
path. The full template lives in
[`templates/gcp-cloud-run/`](https://github.com/nickpclarke/AgentArmy/tree/main/templates/gcp-cloud-run).

Two CI engines ship side by side — pick one per spoke:

- **GitHub Actions** — the reusable workflow `.github/workflows/gcp-cloud-run-deploy.yml`
- **Cloud Build** — `templates/gcp-cloud-run/cloudbuild.yaml`

!!! note "Hub vs Spoke"
    In the **Hub** these are template artifacts; the reusable workflow only runs
    via `workflow_call`/`workflow_dispatch`, so it never deploys the Hub itself.
    A **spoke** wires it up with a small caller workflow and its own GCP project.

## Architecture

```
GitHub push ──▶ GitHub Actions / Cloud Build
                     │  (keyless OIDC via Workload Identity Federation)
                     ▼
              docker build ──▶ Artifact Registry ──▶ gcloud run deploy
                                                          │
                                   runtime SA ◀───────────┘ mounts
                                        │  secretmanager.secretAccessor
                                        ▼
                                 Google Secret Manager
```

## One-time setup

=== "Terraform (recommended)"

    ```bash
    cd templates/gcp-cloud-run/terraform
    # Edit the landscape you want, then apply it with isolated state:
    make ENV=dev apply
    ```

    Provisions Artifact Registry, deploy + runtime service accounts, the
    Workload Identity pool/provider (scoped to one repo), Secret Manager
    secrets, feature-flag env, and the Cloud Run service. Cloud Run image
    changes are `ignore_changes`-d so CI owns image rollout while Terraform
    owns config. `make` uses a per-env state prefix so dev/qa/uat/prod never
    collide.

=== "gcloud (no Terraform)"

    ```bash
    PROJECT_ID=my-gcp-project GITHUB_REPO=owner/my-api-spoke \
      ./templates/gcp-cloud-run/setup/bootstrap-wif.sh
    ```

Both print the values for the two GitHub repo secrets:

| Secret | What |
|---|---|
| `WORKLOAD_IDENTITY_PROVIDER` | Full WIF provider resource name |
| `DEPLOY_SERVICE_ACCOUNT` | Deployer service account email |

## Deploy from a spoke

=== "GitHub Actions"

    Copy `templates/gcp-cloud-run/github-actions-caller.yml` to the spoke's
    `.github/workflows/deploy.yml`:

    ```yaml
    jobs:
      deploy:
        uses: nickpclarke/AgentArmy/.github/workflows/gcp-cloud-run-deploy.yml@main
        with:
          project_id: my-gcp-project
          service: my-service
          allow_unauthenticated: false
          service_account: my-service-runtime@my-gcp-project.iam.gserviceaccount.com
          set_secrets: "DB_PASSWORD=db-password:latest,API_KEY=api-key:latest"
        secrets: inherit
    ```

    The caller **must** grant `permissions: id-token: write` and pass
    `secrets: inherit` for keyless auth.

=== "Cloud Build"

    ```bash
    gcloud builds submit --config templates/gcp-cloud-run/cloudbuild.yaml \
      --substitutions=_SERVICE=my-svc,_REGION=us-central1,_REPOSITORY=containers,\
    _RUNTIME_SA=my-service-runtime@my-gcp-project.iam.gserviceaccount.com,\
    _SET_SECRETS="DB_PASSWORD=db-password:latest"
    ```

## Secret Manager

- Each entry in the Terraform `secrets` map (`ENV_VAR => secret-id`) creates a
  secret container and grants the **runtime** service account
  `roles/secretmanager.secretAccessor`.
- Add values out of band so they never land in Terraform state:

    ```bash
    echo -n "s3cr3t" | gcloud secrets versions add db-password --data-file=-
    ```

- Secrets mount as env vars at deploy time via `set_secrets` (Actions) or
  `_SET_SECRETS` (Cloud Build): `ENV_NAME=secret-id:latest`.

## Landscapes (dev / qa / uat / prod)

Environments are segregated end to end:

| Layer | How it's segregated |
|---|---|
| Infra | `terraform/environments/<env>.tfvars` — one GCP project per landscape (default) |
| State | per-env backend prefix `cloud-run/<service>/<env>` via `make ENV=<env>` |
| Secrets/identity | a GitHub **Environment** per landscape holds env-scoped `WORKLOAD_IDENTITY_PROVIDER` + `DEPLOY_SERVICE_ACCOUNT` |
| Promotion | caller deploys dev→qa→uat automatically, then `prod` behind required reviewers |
| Labels | every resource is labelled `env=<landscape>` for cost attribution |

## Feature flags (across layers)

Flags are a first-class, vendor-neutral concept:

- Declare per landscape in Terraform `feature_flags` (`map(bool)`). They render
  into the service as `FLAG_<NAME>` env vars (e.g. `FLAG_NEW_CHECKOUT=true`), so
  apps read flags identically in every layer with no SDK.
- Promote a flag left-to-right by flipping it in each `*.tfvars` — a simple,
  git-auditable progressive-delivery trail.

    ```hcl
    # environments/prod.tfvars
    feature_flags = {
      new_checkout   = false   # still baking
      rate_limiting  = true
    }
    ```

- **Upgrade path:** keep the `FLAG_*` contract but back it with a managed
  provider (OpenFeature + LaunchDarkly/Flagsmith/GrowthBook) when you need
  targeting, percentage rollouts, or kill switches. Route that to the
  `feature-flag-engineer` agent.

## Why keyless (no JSON keys)?

Long-lived service-account keys are the most common GCP credential leak. The
Workload Identity provider is scoped to a single `owner/repo` via an attribute
condition, so only that repo can impersonate the deployer. This matches the
`gcp-infra-engineer` agent's conventions.

!!! tip "Bicep?"
    Bicep is **Azure-only** and cannot provision GCP resources, so it does not
    apply to a Cloud Run pipeline. Terraform is the right choice here and also
    covers Azure/AWS spokes later. For an Azure Container Apps spoke, use the
    `azure-infra-engineer` agent with Bicep.

## Related

- Cloud provider/stack guide: [Cloud Serving Landscape](cloud-serving.md)
- GCP implementation agent: `gcp-infra-engineer`
- Multi-cloud strategy: `cloud-architect`
