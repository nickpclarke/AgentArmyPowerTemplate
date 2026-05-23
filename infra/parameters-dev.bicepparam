using './main.bicep'

param environment = 'dev'
param projectName = 'agentarmy'
param location = 'eastus'
param tags = {
  environment: 'dev'
  cost-center: 'engineering'
  team: 'agentarmy'
  managed-by: 'bicep'
}
