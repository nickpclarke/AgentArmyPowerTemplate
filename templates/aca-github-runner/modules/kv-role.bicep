// Grants a principal secret get/list on an existing Key Vault that uses the classic
// ACCESS-POLICY model (enableRbacAuthorization = false). Deployed at the vault's
// resource-group scope (see acr-role.bicep for the cross-RG rationale).
//
// Uses an `accessPolicies/add` child resource, which APPENDS this policy without
// disturbing the vault's existing policies.

@description('Name of the existing access-policy-mode Key Vault.')
param keyVaultName string

@description('Principal (managed identity) object id to grant secret get/list.')
param principalId string

@description('Entra tenant id for the access policy entry.')
param tenantId string = subscription().tenantId

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource accessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2023-07-01' = {
  parent: keyVault
  name: 'add'
  properties: {
    accessPolicies: [
      {
        tenantId: tenantId
        objectId: principalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}
