using './main.bicep'

// ACA GitHub Runner — parameter file for the nickpclarke fleet.
//
// Adjust imageTag at deploy time via --parameters imageTag=<sha> rather than
// editing this file (keeps this file environment-stable and commit-diff clean).
//
// To reuse an existing ACA environment (e.g. the one created for ArcadeDB or
// a spoke service), set containerAppsEnvironmentName to its resource name.
// Leave it empty to let the template create a dedicated Consumption environment.

param environment    = 'ci'
param location       = 'eastus'
param projectName    = 'agentarmy'

// ACR — the shared registry for the nickpclarke fleet
param acrLoginServer = 'agentarmy.azurecr.io'
param imageName      = 'aca-github-runner'
param imageTag       = 'latest'

// Leave empty to create a new ACA environment dedicated to CI runners.
// Set to an existing environment name to co-locate with other services:
//   param containerAppsEnvironmentName = 'cae-agentarmy-dev'
param containerAppsEnvironmentName = ''

// Key Vault holding the GitHub PAT (existing shared vault)
param keyVaultName       = 'akv01-agentarmy'
param kvSecretNamePat    = 'GHRUNNERPAT'

// ACR and Key Vault live in their own resource groups (not this deployment's RG).
param acrResourceGroup     = 'rg-arcade-platform'
param keyVaultResourceGroup = 'rg-01'

// GitHub owner + repos to provision runner Jobs for
param githubOwner = 'nickpclarke'
param repos = [
  'AgentArmy'
  'frontend-core'
  'backend-core'
  'middle-core'
]

// Runner labels — must match the `runs-on` labels in your workflow YAML.
// Workflows must set:  runs-on: [self-hosted, aca-linux]
param runnerLabels = 'aca-linux,self-hosted'

// Scale: true scale-to-zero when idle (minExecutions=0), cap at 5 concurrent
// runners per repo. Increase maxExecutions if a repo runs many parallel jobs.
param minExecutions            = 0
param maxExecutions            = 5
param targetWorkflowQueueLength = 1

// Resource sizing: 1 vCPU / 2 Gi is sufficient for bash/python/node CI jobs.
// Bump to '2.0' / '4Gi' for heavier compilation workloads.
param containerCpu    = '1.0'
param containerMemory = '2Gi'

param tags = {
  environment:   'ci'
  'cost-center': 'engineering'
  team:          'agentarmy'
  'managed-by':  'bicep'
  component:     'github-runner'
}
