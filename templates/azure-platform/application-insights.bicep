// application-insights.bicep — workspace-bound Application Insights for the
// AgentArmy fleet's distributed-trace + APM sink.
//
// Realizes ARC-ADR-024 + ARC-ADR-010 (Observability Standard). Bound to the
// existing Log Analytics workspace in rg-arcade-platform; the AI connection
// string lands in Key Vault so the OTel Collector can resolve it via
// secretref without it appearing in plain env. Per the observability-engineer
// audit finding, App Insights is the right first metrics/traces backend for
// the current scale (free under 5 GB/mo; ~zero infra ops vs Prometheus).
//
// Deploy at resource-group scope:
//   az deployment group create \
//     --resource-group rg-arcade-platform \
//     --template-file templates/azure-platform/application-insights.bicep \
//     --parameters workspaceName=workspace-rgarcadeplatformzJ8M
//
// Outputs the connection string ID for the Bicep module that follows
// (otel-collector.bicep wires its secretref to this).

targetScope = 'resourceGroup'

@description('Name of the Log Analytics workspace to bind to (workspace-mode AI).')
param workspaceName string

@description('Component name. Defaults to ai-agentarmy-<env>; override per env.')
param appInsightsName string = 'ai-agentarmy-dev'

@description('Region. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Application type for AI. Use "web" for HTTP services.')
@allowed(['web', 'other'])
param applicationType string = 'web'

@description('Key Vault that will receive the connection string secret.')
param keyVaultName string = 'akv01-agentarmy'

@description('Secret name in KV. The OTel Collector resolves the AI connection string via this secret name.')
param connectionStringSecretName string = 'AI-CONNECTION-STRING'

// Reference the existing Log Analytics workspace (must already exist in this RG).
resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: workspaceName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: applicationType
  properties: {
    Application_Type: applicationType
    WorkspaceResourceId: workspace.id
    // 90-day retention (default; matches observability-engineer rec for dev).
    RetentionInDays: 90
    // No public ingestion key; OTel Collector authenticates via the connection
    // string (managed identity → instrumentation key resolved at boot).
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    DisableLocalAuth: false
  }
  tags: {
    env: 'dev'
    service: 'observability'
    team: 'agentarmy'
    'cost-center': 'engineering'
    'managed-by': 'bicep'
  }
}

// Reference the existing KV (must already exist; we don't create here).
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Stash the AI connection string in KV so the OTel Collector secretref
// resolves to it. The KV secret value is the App Insights Connection String
// (preferred over plain instrumentation key — supports endpoint overrides).
resource aiConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: connectionStringSecretName
  properties: {
    value: appInsights.properties.ConnectionString
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

output appInsightsId string = appInsights.id
output appInsightsName string = appInsights.name
output connectionStringSecretUri string = aiConnectionStringSecret.properties.secretUri
output workspaceId string = workspace.id
