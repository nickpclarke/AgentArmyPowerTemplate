# Azure Container Apps Dev Template

Copy these files into a platform or spoke workload repository when the service should use the AgentArmy lifecycle promotion lane for Azure Dev containers.

Do not run this lane from the AgentArmy template repository itself. AgentArmy owns the template; workload repos own containers.

| File | Destination | Purpose |
|---|---|---|
| `github-actions-local-docker-gate-to-acr-dev.yml` | `.github/workflows/local-docker-gate-to-acr-dev.yml` | First-class local Docker quality gate that promotes the ACR-watched Dev branch after tests pass. |
| `acr-task.yaml` | `acr-task.yaml` | Azure Container Registry Task definition that builds the Dev image from the promoted branch. |
| `Configure-AcrBranchBuildTask.ps1` | `scripts/azure/Configure-AcrBranchBuildTask.ps1` | One-time ACR Task setup helper for the Dev branch build. |
| `Deploy-AzureContainerAppDev.ps1` | `scripts/azure/Deploy-AzureContainerAppDev.ps1` | Escape hatch for direct local image push/deploy while a spoke is still being shaped. |
| `github-actions-local-to-azure-dev.yml` | `.github/workflows/azure-container-apps-dev.yml` | Legacy/manual direct local push workflow. Prefer the branch promotion gate above. |
| `azure-dev.env.example` | `.azure/dev.env.example` | Non-secret local configuration names for the Dev environment. |

Before using the lifecycle lane:

1. Provision or identify the Dev resource group, ACR, Container App Environment, and Container App.
2. Configure an ACR Task that watches the Dev source branch, usually `azure-dev`.
3. Confirm the local self-hosted runner has `self-hosted` and `docker-local` labels.
4. Add `AZURE_DEV_SOURCE_BRANCH=azure-dev` as a repo or environment variable when you do not want the default.
5. Keep runtime secrets in Key Vault or Container Apps secrets, not in committed workflow YAML.

The local Docker gate may be manual while the spoke matures. Once stable, it can run after merges to `main`. It should only promote the Dev source branch after diagnostics, Docker build, and CLI tests pass.
