// AgentArmy Infrastructure-as-Code (Bicep)
// Provides repeatable, template-based Azure infrastructure deployment
// Supports multiple environments (dev, staging, prod)

metadata description = 'AgentArmy Infrastructure - Complete Azure setup for AI agents'

param environment string = 'dev' @description('Environment name (dev, staging, prod)')
param location string = resourceGroup().location @description('Azure region for resources')
param projectName string = 'agentarmy' @description('Project name for naming convention')
param tags object = {} @description('Tags to apply to all resources')

// Configuration by environment
var environmentConfig = {
  dev: {
    appServicePlanSku: 'B1'
    cosmosDbThroughput: 400
    containerAppsCpu: '0.25'
    containerAppsMemory: '0.5Gi'
    containerAppsReplicas: 1
  }
  staging: {
    appServicePlanSku: 'S1'
    cosmosDbThroughput: 1000
    containerAppsCpu: '0.5'
    containerAppsMemory: '1Gi'
    containerAppsReplicas: 2
  }
  prod: {
    appServicePlanSku: 'P1V2'
    cosmosDbThroughput: 4000
    containerAppsCpu: '1'
    containerAppsMemory: '2Gi'
    containerAppsReplicas: 3
  }
}

var config = environmentConfig[environment]
var resourceNamePrefix = '${projectName}-${environment}'
var resourceTags = union(tags, {
  environment: environment
  project: projectName
  createdBy: 'bicep'
  createdDate: utcNow('u')
})

// ==================== KEY VAULT ====================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv${uniqueString(resourceGroup().id)}'
  location: location
  tags: resourceTags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false
  }
}

// Key Vault Secrets (placeholders - fill from variables)
resource kvSecretCerebasKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'cerebras-api-key'
  properties: {
    value: 'PLACEHOLDER_CEREBRAS_KEY'
  }
}

resource kvSecretTavilyKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'tavily-api-key'
  properties: {
    value: 'PLACEHOLDER_TAVILY_KEY'
  }
}

resource kvSecretFoundryKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'foundry-api-key'
  properties: {
    value: 'PLACEHOLDER_FOUNDRY_KEY'
  }
}

// ==================== COSMOS DB ====================
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: '${resourceNamePrefix}-cosmos'
  location: location
  tags: resourceTags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxIntervalInSeconds: 5
      maxStalenessPrefix: 100
    }
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        failoverPriority: 0
        locationName: location
      }
    ]
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    publicNetworkAccess: 'Enabled'
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosAccount
  name: 'agentarmy'
  properties: {
    resource: {
      id: 'agentarmy'
    }
  }
}

resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: cosmosDatabase
  name: 'agents'
  properties: {
    resource: {
      id: 'agents'
      partitionKey: {
        paths: [
          '/agentId'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/_etag/?'
          }
        ]
      }
    }
    options: {
      throughput: config.cosmosDbThroughput
    }
  }
}

// ==================== CONTAINER REGISTRY ====================
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: '${replace(resourceNamePrefix, '-', '')}acr'
  location: location
  tags: resourceTags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 30
        status: 'enabled'
      }
    }
  }
}

// ==================== APPLICATION INSIGHTS ====================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${resourceNamePrefix}-ai'
  location: location
  kind: 'web'
  tags: resourceTags
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ==================== CONTAINER APPS ENVIRONMENT ====================
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${resourceNamePrefix}-law'
  location: location
  tags: resourceTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: '${resourceNamePrefix}-env'
  location: location
  tags: resourceTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// ==================== STORAGE ACCOUNT ====================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${replace(resourceNamePrefix, '-', '')}sa'
  location: location
  tags: resourceTags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'agent-data'
  properties: {
    publicAccess: 'None'
  }
}

// ==================== OUTPUTS ====================
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri

output cosmosAccountName string = cosmosAccount.name
output cosmosDatabaseName string = cosmosDatabase.name
output cosmosConnectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString

output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer

output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString

output containerAppsEnvironmentName string = containerAppsEnvironment.name
output containerAppsEnvironmentId string = containerAppsEnvironment.id

output storageAccountName string = storageAccount.name
output storageAccountKey string = storageAccount.listKeys().keys[0].value

output deploymentId string = deployment().name
output deploymentTime string = utcNow('u')
