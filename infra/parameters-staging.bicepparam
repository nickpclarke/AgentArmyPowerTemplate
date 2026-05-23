using './main.bicep'

param environment = 'staging'
param projectName = 'agentarmy'
param location = 'eastus'
param tags = {
  environment: 'staging'
  cost-center: 'engineering'
  team: 'agentarmy'
  managed-by: 'bicep'
}
