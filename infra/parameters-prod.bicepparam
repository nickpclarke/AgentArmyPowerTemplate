using './main.bicep'

param environment = 'prod'
param projectName = 'agentarmy'
param location = 'eastus'
param tags = {
  environment: 'prod'
  cost-center: 'engineering'
  team: 'agentarmy'
  managed-by: 'bicep'
  sla: 'critical'
}
