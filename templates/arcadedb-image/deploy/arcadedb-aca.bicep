// arcadedb-aca.bicep
// Deploys a single-replica ArcadeDB Container App backed by persistent Azure Files.
//
// Design decisions:
//   - System-assigned managed identity + Key Vault secret references: no plaintext
//     passwords in the template or environment variables at deploy time.
//   - ACA secrets are populated from Key Vault references (identity-based, no SAS).
//     Because ACA cannot mount a secret as a file at the volume level today, the
//     secrets are surfaced as plain env vars (ARCADEDB_ROOT_PASSWORD /
//     ARCADEDB_SERVICE_PASSWORD). The entrypoint prefers *_FILE but falls back to
//     the plain var — both paths are safe inside the container.
//   - minReplicas=1 / maxReplicas=1: ArcadeDB is a single-writer embedded engine;
//     scale-to-zero would drop the persistent connection and corrupt in-flight txns.
//   - Two Azure Files shares (databases + config) mounted at the paths declared as
//     VOLUMEs in the base image. They must be mounted together or the read-only
//     platform_reader user (config/server-users.jsonl) desyncs from the data on
//     pod recycle.
//   - External HTTP ingress on targetPort 2480 (HTTP / Studio / MCP).
//   - Liveness probe via GET /api/v1/ready (returns 204, no auth required).

metadata description = 'ArcadeDB dev database on Azure Container Apps with persistent Azure Files storage'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Azure region. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Short environment tag used in resource names (e.g. "dev", "staging").')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Spoke/project identifier used in resource names (e.g. "backend-core").')
param projectName string = 'backend-core'

@description('ACR login server (e.g. myregistry.azurecr.io).')
param acrLoginServer string

@description('Image name without the registry prefix (e.g. "agentarmy-arcadedb").')
param imageName string = 'agentarmy-arcadedb'

@description('Image tag to deploy.')
param imageTag string = 'latest'

@description('Name of the existing Container Apps Environment to join. Leave empty to create a new one.')
param containerAppsEnvironmentName string = ''

@description('Name of the Key Vault that holds the ArcadeDB passwords. Defaults to the shared repo vault.')
param keyVaultName string = 'akv01-agentarmy'

@description('Key Vault secret name for the ArcadeDB root password.')
param kvSecretNameRootPassword string = 'arcadedb-root-password'

@description('Key Vault secret name for the platform_reader service password.')
param kvSecretNameServicePassword string = 'arcadedb-service-password'

@description('Tags applied to every resource.')
param tags object = {}

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

var prefix = '${projectName}-${environment}'
var safePrefix = replace(replace(prefix, '-', ''), '_', '')  // storage names: alphanumeric only

// ACA Container App name: max 32 chars, lowercase, alphanumeric + hyphens
var containerAppName = 'ca-arcadedb-${environment}'

// Storage account name: max 24 chars, lowercase alphanumeric
var storageAccountName = 'st${take(safePrefix, 18)}adb'

// File share names
var shareNameDatabases = 'arcadedb-databases'
var shareNameConfig    = 'arcadedb-config'

// ACA environment storage binding names (surfaced as named storage in the env)
var envStorageNameDatabases = 'arcadedb-databases'
var envStorageNameConfig    = 'arcadedb-config'

// ACA secret names (must be lowercase alphanumeric + hyphens)
var acaSecretNameRoot    = 'arcadedb-root-password'
var acaSecretNameService = 'arcadedb-service-password'

var resolvedTags = union(tags, {
  environment: environment
  project: projectName
  component: 'arcadedb'
  managedBy: 'bicep'
})

// ---------------------------------------------------------------------------
// Key Vault reference (existing — not created here)
// ---------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// ---------------------------------------------------------------------------
// Storage Account + File Shares
// ---------------------------------------------------------------------------

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: resolvedTags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    // Azure Files shares are under the file service
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource shareDatabases 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileService
  name: shareNameDatabases
  properties: {
    shareQuota: 32  // GiB — sufficient for dev; increase via parameters for prod
    enabledProtocols: 'SMB'
  }
}

resource shareConfig 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileService
  name: shareNameConfig
  properties: {
    shareQuota: 4
    enabledProtocols: 'SMB'
  }
}

// ---------------------------------------------------------------------------
// Log Analytics (for the managed environment when we create it)
// ---------------------------------------------------------------------------

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = if (empty(containerAppsEnvironmentName)) {
  name: 'law-${prefix}-adb'
  location: location
  tags: resolvedTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// ---------------------------------------------------------------------------
// Container Apps Environment (create or reference existing)
// ---------------------------------------------------------------------------

// New environment (when containerAppsEnvironmentName is empty)
resource newContainerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = if (empty(containerAppsEnvironmentName)) {
  name: 'cae-${prefix}'
  location: location
  tags: resolvedTags
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

// Existing environment (when containerAppsEnvironmentName is provided)
resource existingContainerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' existing = if (!empty(containerAppsEnvironmentName)) {
  name: containerAppsEnvironmentName
}

// Resolved environment resource ID (works for both branches above)
var resolvedEnvId = empty(containerAppsEnvironmentName)
  ? newContainerAppsEnvironment.id
  : existingContainerAppsEnvironment.id

var resolvedEnvName = empty(containerAppsEnvironmentName)
  ? newContainerAppsEnvironment.name
  : existingContainerAppsEnvironment.name

// ---------------------------------------------------------------------------
// ACA Environment Storage bindings
// These bind the Azure Files shares to named storage in the ACA environment.
// The Container App then references them by name in its volume mounts.
// ---------------------------------------------------------------------------

resource envStorageDatabases 'Microsoft.App/managedEnvironments/storages@2023-11-02-preview' = {
  name: envStorageNameDatabases
  parent: empty(containerAppsEnvironmentName) ? newContainerAppsEnvironment : existingContainerAppsEnvironment
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: shareNameDatabases
      accessMode: 'ReadWrite'
    }
  }
}

resource envStorageConfig 'Microsoft.App/managedEnvironments/storages@2023-11-02-preview' = {
  name: envStorageNameConfig
  parent: empty(containerAppsEnvironmentName) ? newContainerAppsEnvironment : existingContainerAppsEnvironment
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: shareNameConfig
      accessMode: 'ReadWrite'
    }
  }
}

// ---------------------------------------------------------------------------
// Container App
// ---------------------------------------------------------------------------

resource containerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: containerAppName
  location: location
  tags: resolvedTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: resolvedEnvId
    configuration: {
      // ---- Ingress ----
      ingress: {
        external: true
        targetPort: 2480
        transport: 'http'
        allowInsecure: false
      }
      // ---- ACA secrets backed by Key Vault references ----
      // The managed identity is granted get/list on the vault below (RBAC).
      // Key Vault reference syntax: @Microsoft.KeyVault(VaultName=<name>;SecretName=<name>)
      secrets: [
        {
          name: acaSecretNameRoot
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/${kvSecretNameRootPassword}'
          identity: 'system'
        }
        {
          name: acaSecretNameService
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/${kvSecretNameServicePassword}'
          identity: 'system'
        }
      ]
    }
    template: {
      // ---- Scale: single writer, never zero ----
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      // ---- Volume declarations referencing the ACA env storage bindings ----
      volumes: [
        {
          name: 'databases'
          storageType: 'AzureFile'
          storageName: envStorageNameDatabases
        }
        {
          name: 'config'
          storageType: 'AzureFile'
          storageName: envStorageNameConfig
        }
      ]
      containers: [
        {
          name: 'arcadedb'
          image: '${acrLoginServer}/${imageName}:${imageTag}'
          resources: {
            // Dev-tier defaults: 0.5 vCPU / 1 Gi; tune for larger datasets.
            cpu: json('0.5')
            memory: '1Gi'
          }
          // ---- Volume mounts (both paths declared as VOLUMEs in the base image) ----
          volumeMounts: [
            {
              volumeName: 'databases'
              mountPath: '/home/arcadedb/databases'
            }
            {
              volumeName: 'config'
              mountPath: '/home/arcadedb/config'
            }
          ]
          // ---- Environment variables ----
          // ACA secrets are projected as plain env vars because ACA does not
          // support mounting a secret as a file. The entrypoint's read_secret()
          // falls back to the plain var when *_FILE is unset — both paths are
          // handled safely.
          //
          // Constraint: avoid : [ ] { } in the service password value; those
          // characters are ArcadeDB defaultDatabases delimiters. Enforce this
          // when writing the secret to Key Vault (see deploy/README.md).
          env: [
            {
              name: 'ARCADEDB_ROOT_PASSWORD'
              secretRef: acaSecretNameRoot
            }
            {
              name: 'ARCADEDB_SERVICE_PASSWORD'
              secretRef: acaSecretNameService
            }
            // Non-secret runtime knobs (override via parameters or extra env)
            {
              name: 'ARCADEDB_DATABASE'
              value: 'knowledge'
            }
            {
              name: 'ARCADEDB_SERVICE_USER'
              value: 'platform_reader'
            }
            {
              name: 'ARCADEDB_HTTP_PORT'
              value: '2480'
            }
            {
              name: 'ARCADEDB_SERVER_MODE'
              value: 'production'
            }
            // Container-aware heap — ACA reports correct cgroup memory limits
            {
              name: 'ARCADEDB_OPTS_MEMORY'
              value: '-XX:InitialRAMPercentage=50.0 -XX:MaxRAMPercentage=75.0'
            }
          ]
          // ---- Liveness probe: /api/v1/ready returns 204, no auth ----
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/v1/ready'
                port: 2480
                scheme: 'HTTP'
              }
              initialDelaySeconds: 45
              periodSeconds: 15
              timeoutSeconds: 5
              failureThreshold: 5
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/api/v1/ready'
                port: 2480
                scheme: 'HTTP'
              }
              initialDelaySeconds: 45
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Startup'
              httpGet: {
                path: '/api/v1/ready'
                port: 2480
                scheme: 'HTTP'
              }
              // ArcadeDB JVM cold-start can take up to 60 s on first boot
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 12
            }
          ]
        }
      ]
    }
  }
  dependsOn: [
    envStorageDatabases
    envStorageConfig
  ]
}

// ---------------------------------------------------------------------------
// RBAC: grant the Container App's system identity Key Vault Secrets User
// This is the minimum needed for Key Vault secret references to resolve.
// ---------------------------------------------------------------------------

// Built-in role: Key Vault Secrets User (get + list secrets)
var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  // Scope the assignment directly on the Key Vault
  scope: keyVault
  name: guid(keyVault.id, containerApp.id, kvSecretsUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---------------------------------------------------------------------------
// ACR pull: grant the Container App's system identity AcrPull on the ACR
// (only created when acrLoginServer resolves to an ACR in the same subscription)
// ---------------------------------------------------------------------------

// Built-in role: AcrPull
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

// Derive the ACR resource name from the login server (strip .azurecr.io)
var acrName = split(acrLoginServer, '.')[0]

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, containerApp.id, acrPullRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

output containerAppName string = containerApp.name
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
output containerAppPrincipalId string = containerApp.identity.principalId
output storageAccountName string = storageAccount.name
output containerAppsEnvironmentName string = resolvedEnvName
output arcadeDbUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output arcadeDbReadyUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}/api/v1/ready'
