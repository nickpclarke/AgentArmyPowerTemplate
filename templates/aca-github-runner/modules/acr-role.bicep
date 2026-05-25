// Grants a principal a role on an existing ACR. Deployed at the ACR's resource-group
// scope so the role assignment lives in the same RG as the registry (cross-RG role
// assignments cannot be authored from a different RG-scoped deployment).

@description('Name of the existing Azure Container Registry.')
param acrName string

@description('Principal (managed identity) object id to grant the role to.')
param principalId string

@description('Built-in role definition GUID (e.g. AcrPull).')
param roleDefinitionId string

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, principalId, roleDefinitionId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
