// main.bicep
// Ephemeral GitHub Actions self-hosted runners on Azure Container Apps Jobs,
// scaled to zero by KEDA github-runner scaler.
//
// Architecture:
//   - One Container Apps Job per GitHub repo (Event-driven / KEDA-triggered).
//   - KEDA github-runner scaler polls each repo's workflow queue and spawns
//     a new Job execution (= one ephemeral runner container) per queued job.
//   - Each execution registers as an ephemeral runner, runs one job, then exits.
//   - Scale: minExecutions=0 (true scale-to-zero), maxExecutions configurable.
//   - A user-assigned managed identity pulls the image from ACR and resolves
//     the GitHub PAT from Key Vault — no inline secrets anywhere.
//
// Scoper note:
//   GitHub user account runners (not org runners) must register per-repo.
//   runnerScope=repo is hard-coded in each Job's KEDA scale rule.
//
// Design decisions align with templates/arcadedb-image/deploy/arcadedb-aca.bicep:
//   - Existing or new ACA environment (param containerAppsEnvironmentName).
//   - User-assigned managed identity (shared across all Jobs) over system-assigned,
//     so RBAC is assigned once rather than once per Job.
//   - KV secret references on Jobs use the `keyVaultUrl + identity` pattern
//     introduced in ACA 2023-11-02-preview.
//   - All resource names follow the `<prefix>-<component>` convention.

metadata description = 'Ephemeral GitHub Actions self-hosted runners on ACA Jobs with KEDA scale-to-zero'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Azure region. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Short environment tag used in resource names (e.g. "ci", "prod").')
@allowed(['ci', 'dev', 'staging', 'prod'])
param environment string = 'ci'

@description('Project identifier used in resource names (e.g. "agentarmy").')
param projectName string = 'agentarmy'

@description('ACR login server (e.g. agentarmy.azurecr.io).')
param acrLoginServer string = 'agentarmy.azurecr.io'

@description('Runner image name without the registry prefix (e.g. "aca-github-runner").')
param imageName string = 'aca-github-runner'

@description('Runner image tag to deploy.')
param imageTag string = 'latest'

@description('ACR admin username for image pull. Use managed identity instead when AAD data-plane RBAC is available on the registry; this is the fallback for registries where only admin auth works.')
param acrUsername string = ''

@secure()
@description('ACR admin password (passed at deploy time; stored only as an ACA secret, never in the template). Leave empty to pull via the managed identity instead.')
param acrPassword string = ''

@description('Name of an existing Container Apps Environment to reuse. Leave empty to create a new Consumption-tier environment.')
param containerAppsEnvironmentName string = ''

@description('Name of the Key Vault holding the GitHub PAT secret.')
param keyVaultName string = 'akv01-agentarmy'

@description('Key Vault secret name for the GitHub PAT (classic PAT with repo scope).')
param kvSecretNamePat string = 'GHRUNNERPAT'

@description('Resource group of the existing ACR (it may live outside this deployment RG).')
param acrResourceGroup string = 'rg-arcade-platform'

@description('Resource group of the existing Key Vault (it may live outside this deployment RG).')
param keyVaultResourceGroup string = 'rg-01'

@description('GitHub account owner (user or org) for all repos. Runners are scoped per-repo.')
param githubOwner string = 'nickpclarke'

@description('Array of GitHub repository names to create runner Jobs for. A separate Container Apps Job is created for each entry.')
param repos array = [
  'AgentArmy'
  'frontend-core'
  'backend-core'
  'middle-core'
]

@description('Runner labels applied during config. Must include the label your workflows target.')
param runnerLabels string = 'aca-linux,self-hosted'

@description('Minimum concurrent Job executions per repo. Set to 0 for true scale-to-zero (recommended — cost is zero when idle).')
@minValue(0)
@maxValue(10)
param minExecutions int = 0

@description('Maximum concurrent Job executions per repo (caps simultaneous parallel runs).')
@minValue(1)
@maxValue(10)
param maxExecutions int = 5

@description('KEDA targetWorkflowQueueLength: number of queued jobs that triggers one new execution. Value of 1 means one runner is started per queued job (recommended).')
@minValue(1)
param targetWorkflowQueueLength int = 1

@description('CPU allocation per runner container (vCPUs). 1 vCPU for typical CI workloads.')
param containerCpu string = '1.0'

@description('Memory allocation per runner container. Must match a valid ACA Consumption profile.')
param containerMemory string = '2Gi'

@description('Tags applied to every resource.')
param tags object = {}

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

var prefix = '${projectName}-${environment}'

// Sanitise for storage/registry name constraints (alphanumeric only, lowercase)
var safePrefix = toLower(replace(replace(prefix, '-', ''), '_', ''))

// Log Analytics workspace name (only used when creating a new ACA environment)
var lawName = 'law-${prefix}-runner'

// ACA environment name when we create a new one
var newEnvName = 'cae-${prefix}-runner'

// User-assigned managed identity name (shared by all Jobs)
var uamiName = 'id-${prefix}-runner'

// ACA secret name for the GitHub PAT (must be lowercase alphanumeric + hyphens)
var acaSecretNamePat = 'github-pat'

// Built-in role IDs
var acrPullRoleId          = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var kvSecretsUserRoleId    = '4633458b-17de-408a-b874-0445c86b69e6'

// Derive the ACR resource name from the login server (strip .azurecr.io suffix)
var acrName = split(acrLoginServer, '.')[0]

var resolvedTags = union(tags, {
  environment: environment
  project: projectName
  component: 'github-runner'
  managedBy: 'bicep'
})

// ---------------------------------------------------------------------------
// Existing resources (Key Vault, ACR)
// ---------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
  scope: resourceGroup(keyVaultResourceGroup)
}

// ---------------------------------------------------------------------------
// User-assigned managed identity
// Shared by all runner Jobs so RBAC assignments are created once.
// ---------------------------------------------------------------------------

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: uamiName
  location: location
  tags: resolvedTags
}

// ---------------------------------------------------------------------------
// RBAC — deployed via modules scoped to each target resource's RG, because the
// ACR and Key Vault may live in resource groups other than this deployment's.
// A role assignment must be deployed in the same RG as the resource it scopes.
// ---------------------------------------------------------------------------

module acrPullRoleAssignment 'modules/acr-role.bicep' = {
  name: 'acrPullRole'
  scope: resourceGroup(acrResourceGroup)
  params: {
    acrName: acrName
    principalId: uami.properties.principalId
    roleDefinitionId: acrPullRoleId
  }
}

module kvSecretsUserRoleAssignment 'modules/kv-role.bicep' = {
  name: 'kvSecretsAccess'
  scope: resourceGroup(keyVaultResourceGroup)
  params: {
    keyVaultName: keyVaultName
    principalId: uami.properties.principalId
    tenantId: subscription().tenantId
  }
}

// ---------------------------------------------------------------------------
// Log Analytics workspace (only when creating a new ACA environment)
// ---------------------------------------------------------------------------

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = if (empty(containerAppsEnvironmentName)) {
  name: lawName
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

resource newContainerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = if (empty(containerAppsEnvironmentName)) {
  name: newEnvName
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

resource existingContainerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' existing = if (!empty(containerAppsEnvironmentName)) {
  name: containerAppsEnvironmentName
}

// Resolved environment resource ID — used by all Jobs
var resolvedEnvId = empty(containerAppsEnvironmentName)
  ? newContainerAppsEnvironment.id
  : existingContainerAppsEnvironment.id

var resolvedEnvName = empty(containerAppsEnvironmentName)
  ? newContainerAppsEnvironment.name
  : existingContainerAppsEnvironment.name

// ---------------------------------------------------------------------------
// Container Apps Jobs — one per repo
//
// Job type: Event-driven (triggerType: Event) with KEDA github-runner scaler.
//
// KEDA auth wiring:
//   The github-runner scaler requires a personalAccessToken to call the GitHub
//   API for queue length. ACA Jobs surface this via a ScaledJobTriggerAuthentication-
//   equivalent pattern: the secret is defined in the Job's `secrets` array and
//   referenced in the scale rule's `auth` block with `secretRef` pointing to the
//   ACA-level secret name. The secret itself is KV-backed (keyVaultUrl + identity).
//
//   At the ACA API level this maps to:
//     configuration.secrets[].keyVaultUrl  → pulls the value from KV at runtime
//     template.scale.rules[].custom.auth[] → tells KEDA which secret to use
//
// Ephemeral registration:
//   Each execution runs entrypoint.sh which:
//     1. Exchanges GITHUB_PAT for an ephemeral registration token.
//     2. Runs config.sh --ephemeral to register a one-shot runner.
//     3. exec ./run.sh → processes the job → exits 0.
//   The exit triggers ACA to complete the execution. KEDA sees queue length
//   drop and does not scale out further when the queue is empty.
// ---------------------------------------------------------------------------

// Registry auth: prefer the managed identity; fall back to ACR admin creds when an
// acrPassword is supplied (some registries don't honor AAD data-plane RBAC for pulls).
var useAdminCreds = !empty(acrPassword)
var kvPatSecret = {
  name: acaSecretNamePat
  keyVaultUrl: '${keyVault.properties.vaultUri}secrets/${kvSecretNamePat}'
  identity: uami.id
}
var jobSecrets = useAdminCreds ? [
  kvPatSecret
  {
    name: 'acr-password'
    value: acrPassword
  }
] : [
  kvPatSecret
]
var jobRegistries = useAdminCreds ? [
  {
    server: acrLoginServer
    username: acrUsername
    passwordSecretRef: 'acr-password'
  }
] : [
  {
    server: acrLoginServer
    identity: uami.id
  }
]

resource runnerJob 'Microsoft.App/jobs@2023-11-02-preview' = [for repo in repos: {
  // ACA job names must be <=32 chars, lowercase, no '--'. Keep it short: gh-runner-<repo>.
  name: toLower('gh-runner-${repo}')
  location: location
  tags: union(resolvedTags, {
    'github-repo': repo
  })
  // Attach the user-assigned managed identity so ACA can pull from ACR and
  // resolve Key Vault secret references without any stored credentials.
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    environmentId: resolvedEnvId
    configuration: {
      triggerType: 'Event'
      replicaTimeout: 1800       // 30 minutes — generous timeout for slow jobs
      replicaRetryLimit: 1       // one retry on execution failure before giving up
      // ---- ACA secrets backed by Key Vault reference ----
      // The managed identity resolves the secret at runtime; the PAT value is
      // never present in the ARM template, environment variables, or logs.
      secrets: jobSecrets
      // ---- Registry: managed identity by default; ACR admin creds when acrPassword is supplied ----
      registries: jobRegistries
      // ---- KEDA event-driven scale configuration ----
      eventTriggerConfig: {
        parallelism: 1           // one runner execution per triggering event
        replicaCompletionCount: 1
        scale: {
          minExecutions: minExecutions
          maxExecutions: maxExecutions
          pollingInterval: 30    // seconds between KEDA queue-length polls
          rules: [
            {
              name: 'github-runner-scale'
              type: 'github-runner'
              // KEDA github-runner scaler metadata.
              // owner + repos together identify exactly which repo queue to watch.
              // runnerScope=repo is required for user-account (non-org) runners.
              metadata: {
                owner: githubOwner
                repos: repo
                runnerScope: 'repo'
                labels: runnerLabels
                targetWorkflowQueueLength: string(targetWorkflowQueueLength)
              }
              // auth: tells KEDA to use the ACA secret `github-pat` as the
              // personalAccessToken when calling the GitHub API for queue length.
              auth: [
                {
                  secretRef: acaSecretNamePat
                  triggerParameter: 'personalAccessToken'
                }
              ]
            }
          ]
        }
      }
    }
    // ---- Job template: the actual runner container ----
    template: {
      containers: [
        {
          name: 'runner'
          image: '${acrLoginServer}/${imageName}:${imageTag}'
          resources: {
            cpu: json(containerCpu)
            memory: containerMemory
          }
          // ---- Environment variables passed to entrypoint.sh ----
          // GITHUB_PAT is sourced from the ACA secret (KV-backed) — not inline.
          // REPO_OWNER and REPO_NAME drive the registration token API call and
          // the runner URL (https://github.com/$OWNER/$REPO).
          env: [
            {
              name: 'GITHUB_PAT'
              secretRef: acaSecretNamePat
            }
            {
              name: 'REPO_OWNER'
              value: githubOwner
            }
            {
              name: 'REPO_NAME'
              value: repo
            }
            {
              name: 'RUNNER_LABELS'
              value: runnerLabels
            }
          ]
        }
      ]
    }
  }
  dependsOn: [
    acrPullRoleAssignment
    kvSecretsUserRoleAssignment
  ]
}]

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

output containerAppsEnvironmentName string = resolvedEnvName
output uamiName string = uami.name
output uamiPrincipalId string = uami.properties.principalId
output runnerJobNames array = [for (repo, i) in repos: runnerJob[i].name]
output keyVaultName string = keyVault.name
