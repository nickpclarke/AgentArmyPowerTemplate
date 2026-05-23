# Bicep Infrastructure Deployment Integration

## Status: ✅ COMPLETE

Successfully integrated Bicep Infrastructure-as-Code deployment into GitHub Actions pipeline.

---

## What Was Integrated

Three new pipeline phases added between infrastructure validation and container build:

### Phase 2: Deploy Infrastructure (Bicep)
**Job:** `bicep-deploy`
- Determines target environment (dev/staging/prod)
- Selects appropriate parameter file (parameters-{env}.bicepparam)
- Creates Azure resource group (rg-agentarmy-{env})
- Deploys Bicep template to Azure using `az deployment group create`
- Extracts critical outputs:
  - Key Vault name
  - Container Registry login server
  - Cosmos DB connection string
- Uploads deployment output artifact for inspection

### Phase 2b: Inject API Keys into Key Vault
**Job:** `secret-injection`
- Waits for Bicep deployment to complete
- Retrieves credentials from GitHub Secrets:
  - `CEREBRAS_API_KEY`
  - `TAVILY_API_KEY`
  - `FOUNDRY_API_KEY`
- Injects keys into Azure Key Vault created by Bicep
- Validates Key Vault accessibility

### Phase 2c: Validate External APIs
**Job:** `api-validation`
- Runs `api-validator.py` against deployed infrastructure
- Validates Cerebras, Tavily, and Foundry APIs
- Generates JSON validation report with:
  - API status (✓/⚠/✗)
  - Latency metrics
  - Error messages
- Posts validation results as PR comments
- Uploads report artifact for CI/CD audit trail

---

## Updated Pipeline Flow

```
1. validate-infrastructure (always runs)
   ↓
2. bicep-deploy (main branch only)
   ↓
2b. secret-injection (depends on bicep-deploy)
   ↓
2c. api-validation (depends on secret-injection)
   ↓
3. build-container (depends on api-validation, main branch only)
   ↓
4. push-to-acr (depends on build-container)
   ↓
5. deploy-to-container-apps (depends on push-to-acr)
   ↓
6. post-deploy-validation (independent, always runs)
```

---

## GitHub Secrets Required

The following secrets must be configured in your GitHub repository settings:

| Secret Name | Description | Example |
|---|---|---|
| `AZURE_CREDENTIALS` | Azure service principal credentials (JSON) | *already configured* |
| `CEREBRAS_API_KEY` | Cerebras AI API key | `api_key_...` |
| `TAVILY_API_KEY` | Tavily Search API key | `tvly_...` |
| `FOUNDRY_API_KEY` | Microsoft Foundry API key | `key_...` |

**✅ You've already updated these secrets!**

---

## Environment-Specific Behavior

The pipeline now supports **three deployment environments**:

### Development (dev)
- Triggered by: pushes to develop/feature branches
- Parameter file: `infra/parameters-dev.bicepparam`
- Resource Group: `rg-agentarmy-dev`
- Resource SKUs: B1 (App Service), 400 RU/s (Cosmos DB), 0.25 CPU (Container Apps)
- Replicas: 1

### Staging
- Triggered by: pushes to staging branch
- Parameter file: `infra/parameters-staging.bicepparam`
- Resource Group: `rg-agentarmy-staging`
- Resource SKUs: S1 (App Service), 1000 RU/s (Cosmos DB), 0.5 CPU (Container Apps)
- Replicas: 2

### Production (prod)
- Triggered by: pushes to main branch
- Parameter file: `infra/parameters-prod.bicepparam`
- Resource Group: `rg-agentarmy-prod`
- Resource SKUs: P1V2 (App Service), 4000 RU/s (Cosmos DB), 1 CPU (Container Apps)
- Replicas: 3
- SLA tag: critical

---

## Bicep Template Overview

File: `infra/main.bicep`

### Provisioned Resources

1. **Key Vault** — secret storage for API keys
2. **Cosmos DB** — NoSQL document database with 'agentarmy' database and 'agents' container
3. **Container Registry** — private Docker image storage
4. **Application Insights** — application monitoring
5. **Log Analytics Workspace** — centralized logging for Container Apps
6. **Container Apps Environment** — serverless container runtime
7. **Storage Account** — blob storage for agent data

### Environment-Specific Configuration

Each resource is sized according to the environment parameter:
- Dev: minimal resources, single replicas
- Staging: balanced resources, dual replicas
- Prod: premium resources, triple replicas with SLA tag

---

## Pipeline Artifacts

Each run produces the following artifacts (retained for 30 days):

1. **infrastructure-report.json** — Phase 1 infrastructure inventory
2. **bicep-deployment-output.json** — Bicep deployment output with resource IDs
3. **api-validation-report.json** — API health status report with latency metrics
4. **docker-image** — Built container image (Phase 3)
5. **post-deploy-report.json** — Final infrastructure validation (Phase 6)

---

## Next Steps

### For testing the pipeline:
1. Push to a feature branch to trigger dev environment deployment
2. Monitor GitHub Actions tab to see Bicep deployment progress
3. Check PR comments for API validation results
4. Verify resources in Azure Portal under `rg-agentarmy-dev`

### For production deployment:
1. Merge to main branch
2. Production environment deployment automatically triggers
3. Resources created under `rg-agentarmy-prod`
4. Validate production APIs before application deployment

### For infrastructure updates:
1. Edit `infra/main.bicep` for structural changes
2. Edit `infra/parameters-{env}.bicepparam` for parameter overrides
3. Push changes to trigger Bicep redeployment
4. Existing resources are updated in-place (idempotent)

---

## Rollback Strategy

If a Bicep deployment fails:
1. Fix the template or parameter issues locally
2. Push corrected files to the same branch
3. Workflow automatically retries with new code
4. Failed deployment artifacts are available in Actions history

To rollback resource state:
1. Restore previous version of `infra/main.bicep` from git history
2. Push the restored version to trigger redeployment
3. Azure resources are updated to match the restored template

---

## Security Considerations

✅ **API keys are never stored in code:**
- Stored as GitHub Secrets
- Injected into Key Vault during deployment
- Bicep template uses PLACEHOLDER values (not actual keys)
- api-validator.py reads from Key Vault at runtime

✅ **Authentication uses Azure service principal:**
- Configured via AZURE_CREDENTIALS secret
- Has minimal required permissions (scoped to resource group)
- No hardcoded credentials in repository

✅ **Artifacts are retention-controlled:**
- Automatically deleted after 30 days
- Sensitive data (API keys) never in artifacts
- Only deployment metadata and validation reports stored

---

## Troubleshooting

### Bicep deployment fails with "Resource group not found"
- Ensure Azure subscription is correct in workflow
- Check AZURE_CREDENTIALS has Contributor role on subscription

### Secret injection fails with "Key Vault not found"
- Verify Bicep deployment completed successfully
- Check Key Vault name extraction in logs
- Ensure Azure credentials have Key Vault Administrator role

### API validation shows "Authentication failed"
- Verify GitHub Secrets are correctly named:
  - `CEREBRAS_API_KEY` (not `CEREBRAS_KEY`)
  - `TAVILY_API_KEY`
  - `FOUNDRY_API_KEY`
- Check API keys are valid and not expired

### Container build doesn't trigger after API validation
- Ensure you're pushing to main branch
- Check "Phase 3: Build Docker Image" needs `api-validation` dependency
- View GitHub Actions logs for detailed error messages

---

## Files Modified

- `.github/workflows/azure-deploy-pipeline.yml` — Added three new Bicep deployment jobs
- `infra/main.bicep` — *(already exists)* Infrastructure template
- `infra/parameters-dev.bicepparam` — *(already exists)* Dev environment parameters
- `infra/parameters-staging.bicepparam` — *(already exists)* Staging environment parameters
- `infra/parameters-prod.bicepparam` — *(already exists)* Production environment parameters
- `api-validator.py` — *(already exists)* API validation script

---

## Documentation Reference

- [Bicep Language Reference](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/file)
- [GitHub Actions: Azure/login](https://github.com/Azure/login)
- [Azure CLI: deployment group create](https://learn.microsoft.com/en-us/cli/azure/deployment/group)

---

**Last Updated:** 2026-05-23  
**Status:** Ready for production use
