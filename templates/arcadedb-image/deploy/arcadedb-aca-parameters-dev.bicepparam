using './arcadedb-aca.bicep'

// Dev environment parameters.
// Copy and adjust per spoke. Override imageTag at deploy time via
// --parameters imageTag=<sha> rather than editing this file.

param environment   = 'dev'
param location      = 'eastus'  // matches infra/parameters-dev.bicepparam
param projectName   = 'backend-core'  // set to your spoke name

// ACR — populate from bootstrap output or repo var AZURE_ACR_LOGIN_SERVER
param acrLoginServer = 'REPLACE_WITH_ACR_LOGIN_SERVER'  // e.g. myacr.azurecr.io

param imageName     = 'agentarmy-arcadedb'
param imageTag      = 'latest'

// Leave empty to let the template create a new ACA environment; or set to an
// existing environment name to share one (e.g. across multiple spoke services).
param containerAppsEnvironmentName = ''

// Key Vault that holds the passwords (shared repo vault; do not change unless
// you have created a spoke-specific vault).
param keyVaultName              = 'akv01-agentarmy'
param kvSecretNameRootPassword  = 'arcadedb-root-password'
param kvSecretNameServicePassword = 'arcadedb-service-password'

param tags = {
  environment: 'dev'
  cost-center: 'engineering'
  team: 'agentarmy'
  managed-by: 'bicep'
  component: 'arcadedb'
}
