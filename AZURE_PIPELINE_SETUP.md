# Azure Infrastructure & CI/CD Pipeline Setup Guide

Complete guide to set up the full Azure pipeline from GitHub to Container Apps with automated infrastructure validation.

## 📋 Overview

This setup includes:
- ✅ **Infrastructure Validator CLI** - Validates and inventories all Azure resources
- ✅ **GitHub Actions Pipeline** - Automated build, push to ACR, deploy to Container Apps
- ✅ **Azure Container Registry** - Stores container images
- ✅ **Container Apps** - Serverless container deployment

## 🚀 Quick Start (5 Steps)

### Step 1: Prepare Azure Credentials for GitHub

```bash
# Login to Azure
az login

# Create service principal with necessary permissions
az ad sp create-for-rbac \
  --name "AgentArmyPipeline" \
  --role contributor \
  --scopes /subscriptions/449cf71f-50c4-43f8-bc88-ddde8f007580

# Copy the output JSON
```

### Step 2: Add GitHub Secrets

In your GitHub repo → Settings → Secrets and variables → Actions:

1. **`AZURE_CREDENTIALS`** (JSON from step 1):
```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "449cf71f-50c4-43f8-bc88-ddde8f007580",
  "tenantId": "21b8c7be-a6c6-4fec-837e-74694e4b454a"
}
```

2. **`AZURE_REGISTRY_LOGIN_SERVER`**:
```
agentarmy<timestamp>.azurecr.io
```

3. **`AZURE_REGISTRY_USERNAME`**:
```
<your-registry-name>
```

4. **`AZURE_REGISTRY_PASSWORD`**:
```
<admin-password from ACR>
```

### Step 3: Run the Infrastructure Validator

Test locally first:

```bash
# Make the script executable
chmod +x azure-infra-validator.py

# Run validation
python azure-infra-validator.py --subscription AASub1

# Generate JSON report
python azure-infra-validator.py \
  --subscription AASub1 \
  --output infrastructure-report.json
```

**Expected Output:**
```
🚀 Starting Azure Infrastructure Validation
Subscription: AASub1

🔐 Validating Key Vault...
  ✓ akv01-agentarmy (eastus) - N secrets accessible

🗄️  Validating Cosmos DB...
  ✓ cosmosdb-sbx-01 (eastus) - Kind: GlobalDocumentDB

🤖 Validating Microsoft Foundry...
  ✓ fndry-01 (eastus) - Kind: OpenAI

📦 Validating Container Registry...
  ⚠ No Container Registry - Required for pipeline

🐳 Validating Container Apps...
  ⚠ No Container Apps deployed yet

⚡ Validating Function Apps...
  ⚠ No Function Apps deployed

🗃️  Validating SQL Database...
  ⚠ No SQL servers deployed
```

### Step 4: Enable Container Apps (Optional)

```bash
# Create Container Apps environment if not exists
az containerapp env create \
  --name agentarmy-env \
  --resource-group rg-01 \
  --location eastus

# Or check existing environments
az containerapp env list --resource-group rg-01
```

### Step 5: Push to GitHub & Watch Pipeline

```bash
# Commit changes
git add .
git commit -m "feat: add Azure infrastructure validator and CI/CD pipeline"
git push origin main
```

Visit GitHub Actions to watch the pipeline run:
- **Phase 1**: Infrastructure validation ✅
- **Phase 2**: Build container image
- **Phase 3**: Push to Azure Container Registry
- **Phase 4**: Deploy to Container Apps (if enabled)
- **Phase 5**: Post-deployment validation

## 📊 Infrastructure Inventory Report

After running the validator, examine `infrastructure-report.json`:

```json
{
  "timestamp": "2026-05-23T21:15:30.123456",
  "subscription": "AASub1",
  "validation_summary": {
    "total_resources": 7,
    "healthy": 3,
    "warnings": 4,
    "failures": 0
  },
  "resources": [
    {
      "name": "akv01-agentarmy",
      "resource_type": "Microsoft.KeyVault/vaults",
      "status": "✓",
      "location": "eastus",
      "message": "N secrets accessible",
      "details": { "secrets": N }
    }
    // ... more resources
  ],
  "inventory": {
    "keyvaults": [...],
    "cosmos_accounts": [...],
    "foundry_accounts": [...],
    "registries": [...]
  }
}
```

## 🔧 Manual Validation Commands

### Key Vault
```bash
az keyvault list
az keyvault secret list --vault-name akv01-agentarmy
```

### Cosmos DB
```bash
az cosmosdb list
az cosmosdb database list --account-name cosmosdb-sbx-01 --resource-group rg-01
```

### Microsoft Foundry / Azure OpenAI
```bash
az cognitiveservices account list
az cognitiveservices account show --name fndry-01 --resource-group rg-01
```

### Container Registry
```bash
az acr list
az acr repository list --name <registry-name>
```

### Container Apps
```bash
az containerapp list --resource-group rg-01
az containerapp env list --resource-group rg-01
```

## 📦 Creating Your First Container App

Once pipeline succeeds and image is in ACR:

```bash
# 1. Get the container registry URL
REGISTRY=$(az acr list --resource-group rg-01 --query "[0].loginServer" -o tsv)

# 2. Create Container Apps environment (if needed)
az containerapp env create \
  --name agentarmy-env \
  --resource-group rg-01 \
  --location eastus

# 3. Deploy to Container Apps
az containerapp create \
  --name agentarmy-app \
  --resource-group rg-01 \
  --environment agentarmy-env \
  --image $REGISTRY/agentarmy:latest \
  --target-port 8080 \
  --ingress external \
  --registry-login-server $REGISTRY \
  --registry-username <username> \
  --registry-password <password>

# 4. Get the URL
az containerapp show \
  --name agentarmy-app \
  --resource-group rg-01 \
  --query properties.configuration.ingress.fqdn
```

## 🔐 Security Best Practices

1. **Use Managed Identity instead of credentials** (recommended for production):
```bash
# For Container Apps with managed identity
az containerapp create \
  --name agentarmy-app \
  --resource-group rg-01 \
  --environment agentarmy-env \
  --image $REGISTRY/agentarmy:latest \
  --system-assigned
```

2. **Rotate credentials regularly**:
```bash
az acr credential rotate --name <registry-name> --password-name password1
```

3. **Use Key Vault for secrets**:
```bash
# Reference secrets in Container Apps environment
az containerapp create \
  --name agentarmy-app \
  --resource-group rg-01 \
  --environment agentarmy-env \
  --secret-names vault-secret \
  --secrets 'vault-secret=keyvaultRef:https://akv01-agentarmy.vault.azure.net/secrets/my-secret'
```

## 📈 Monitoring & Logs

### Pipeline Logs
- GitHub Actions → Workflow runs → View logs

### Container App Logs
```bash
# Stream logs in real-time
az containerapp logs show \
  --name agentarmy-app \
  --resource-group rg-01 \
  --follow

# Get last N lines
az containerapp logs show \
  --name agentarmy-app \
  --resource-group rg-01 \
  --tail 50
```

### Application Insights (if configured)
```bash
# Monitor performance and errors
az monitor app-insights metrics show \
  --resource-group rg-01 \
  --app <app-insights-name>
```

## 🐛 Troubleshooting

### "Resource not found" error
```bash
# Verify subscription and resource group
az account set --subscription AASub1
az group exists --name rg-01
```

### RBAC permission denied
```bash
# Update service principal permissions
az role assignment create \
  --assignee <service-principal-id> \
  --role "Contributor" \
  --scope /subscriptions/449cf71f-50c4-43f8-bc88-ddde8f007580
```

### ACR push fails
```bash
# Verify ACR credentials
az acr credential show --name <registry-name>

# Manually login and test
az acr login --name <registry-name>
docker tag agentarmy:latest <registry>/agentarmy:test
docker push <registry>/agentarmy:test
```

### Container Apps deployment fails
```bash
# Check Container Apps environment
az containerapp env show --name agentarmy-env --resource-group rg-01

# Check app status and errors
az containerapp show --name agentarmy-app --resource-group rg-01
```

## 📚 Next Steps

1. **Customize Container Image** - Modify `Dockerfile` for your application
2. **Add Health Checks** - Implement `/health` endpoint
3. **Configure Environment Variables** - Set via `--env-vars` in Container Apps
4. **Set up Autoscaling** - Configure min/max replicas
5. **Add Custom Domain** - Map your domain to Container Apps FQDN
6. **Implement Monitoring** - Connect Application Insights

## 🔗 Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/)

## ✅ Validation Checklist

- [ ] Azure CLI installed and authenticated
- [ ] GitHub repository set up with secrets
- [ ] Service principal created with appropriate permissions
- [ ] Infrastructure validator runs successfully locally
- [ ] GitHub Actions workflow file committed
- [ ] Dockerfile configured for your application
- [ ] ACR created (manual or via pipeline)
- [ ] Container Apps environment created (optional, for deployment)
- [ ] First pipeline run successful
- [ ] Container image pushed to ACR
- [ ] App deployed to Container Apps (if using phase 4)

---

**Last Updated**: 2026-05-23
**Status**: Ready for Production
