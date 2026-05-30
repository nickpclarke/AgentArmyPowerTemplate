// arcadedb-aca-platform.bicep
// Codifies the SHARED, hand-deployed ArcadeDB Container App as it actually runs in
// rg-arcade-platform / cae-arcade-platform — captured from live reality during the
// 2026-05-30 root-password hardening (see docs/arcadedb-secret-hardening.md).
//
// WHY THIS EXISTS (drift it replaces):
//   The live `arcadedb` app was stood up imperatively (Docker "Gordon" / ad-hoc
//   `az containerapp create`) with the root password in a PLAINTEXT env var:
//       JAVA_OPTS = -Darcadedb.server.rootPassword=<plaintext> -Darcadedb.txWalFlush=2
//   readable by anyone with RG Reader via `az containerapp show`. This template makes
//   the app reproducible from code with the password sourced from a secret, so the
//   plaintext pattern cannot regress on the next deploy. Do NOT re-create the app with
//   an ad-hoc command carrying a plaintext JAVA_OPTS.
//
// HOW IT DIFFERS FROM arcadedb-aca.bicep (the thin-image variant):
//   - Uses the UPSTREAM `arcadedb` image (what is live today), which takes the root
//     password as a JVM -D arg via JAVA_OPTS. Because an ACA `secretRef` substitutes
//     the WHOLE env var (no interpolation), the secret holds the full opts string.
//   - Joins the EXISTING managed environment + EXISTING Azure Files storage binding
//     (does not create them).
//   - INTERNAL ingress (not external) — reached only from inside cae-arcade-platform
//     (backend-core, the self-hosted aca-arcade runner).
//   - minReplicas=1 / maxReplicas=1 — single-writer; scale-to-zero caused a cold-start
//     revision-swap lock deadlock on the shared Azure Files mount on 2026-05-30.
//
// The longer-term convergence target is the thin `agentarmy-arcadedb` image (arcadedb-aca.bicep),
// which reads a BARE `ARCADEDB_ROOT_PASSWORD` secret + `ARCADEDB_EXTRA_SETTINGS` for txWalFlush,
// removing the need for the bundled opts secret. Tracked as a follow-up.

metadata description = 'Shared ArcadeDB platform Container App (upstream image), root password sourced from a Key Vault-backed secret — no plaintext env.'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Azure region. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Container App name (live: "arcadedb").')
param containerAppName string = 'arcadedb'

@description('Name of the EXISTING Container Apps Environment to join (live: cae-arcade-platform).')
param containerAppsEnvironmentName string = 'cae-arcade-platform'

@description('ACR login server hosting the image (live: arcadeplatformacr.azurecr.io).')
param acrLoginServer string = 'arcadeplatformacr.azurecr.io'

@description('Image repository (live: arcadedb — the upstream ArcadeDB image mirrored into ACR).')
param imageName string = 'arcadedb'

@description('Image tag (live: 26.5.1).')
param imageTag string = '26.5.1'

@description('Name of the EXISTING ACA environment storage binding for the databases volume (live: arcadedb-files).')
param envStorageName string = 'arcadedb-files'

@description('Key Vault that holds the secrets (live: akv01-agentarmy).')
param keyVaultName string = 'akv01-agentarmy'

@description('''Key Vault secret name holding the FULL ArcadeDB server JVM opts string, i.e.
"-Darcadedb.server.rootPassword=<password> -Darcadedb.txWalFlush=2". Keep this value in lockstep
with the bare `arcadedb-root-password` secret that other consumers read (see the rotation runbook).''')
param kvSecretNameServerOpts string = 'arcadedb-server-opts'

@description('Container vCPU.')
param cpu string = '1.0'

@description('Container memory.')
param memory string = '2Gi'

@description('Tags applied to the Container App.')
param tags object = {
  environment: 'dev'
  component: 'arcadedb'
  tier: 'platform'
  managedBy: 'bicep'
}

// ---------------------------------------------------------------------------
// Existing references (NOT created here)
// ---------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-11-02-preview' existing = {
  name: containerAppsEnvironmentName
}

var acrName = split(acrLoginServer, '.')[0]

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

// ACA secret name (lowercase alphanumeric + hyphens)
var acaSecretNameServerOpts = 'arcadedb-server-opts'

// ---------------------------------------------------------------------------
// Container App — system identity + Key Vault-backed secret (no plaintext)
// ---------------------------------------------------------------------------

resource containerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: containerAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      // INTERNAL ingress — reachable only inside the ACA environment.
      ingress: {
        external: false
        targetPort: 2480
        transport: 'http'
        allowInsecure: true
      }
      // The root password reaches the server only via this secret. `az containerapp show`
      // exposes the secretRef name, never the value (the reported vulnerability).
      // Key Vault reference (identity-based) keeps the value out of the ACA secret store too.
      secrets: [
        {
          name: acaSecretNameServerOpts
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/${kvSecretNameServerOpts}'
          identity: 'system'
        }
      ]
      registries: [
        {
          server: acrLoginServer
          identity: 'system'
        }
      ]
    }
    template: {
      // Single writer, never zero: a shared Azure Files mount + two replicas (or a
      // cold-start revision swap) deadlocks on the database lock.
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      volumes: [
        {
          name: 'arcadedb-data'
          storageType: 'AzureFile'
          storageName: envStorageName
        }
      ]
      containers: [
        {
          name: 'arcadedb'
          image: '${acrLoginServer}/${imageName}:${imageTag}'
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          volumeMounts: [
            {
              volumeName: 'arcadedb-data'
              mountPath: '/home/arcadedb/databases'
            }
          ]
          // The upstream image reads JAVA_OPTS; secretRef substitutes the whole value.
          env: [
            {
              name: 'JAVA_OPTS'
              secretRef: acaSecretNameServerOpts
            }
          ]
          // Probes on the unauthenticated readiness endpoint (HTTP 204). These were
          // absent on the hand-deployed app, which made a slow cold start look like an
          // ActivationFailed/port-mismatch. ArcadeDB opens 2480 only after loading
          // databases (incl. JVector index rebuild), so the startup probe is generous.
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/api/v1/ready'
                port: 2480
                scheme: 'HTTP'
              }
              initialDelaySeconds: 15
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 24
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/api/v1/ready'
                port: 2480
                scheme: 'HTTP'
              }
              initialDelaySeconds: 20
              periodSeconds: 15
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/v1/ready'
                port: 2480
                scheme: 'HTTP'
              }
              initialDelaySeconds: 60
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 5
            }
          ]
        }
      ]
    }
  }
}

// ---------------------------------------------------------------------------
// RBAC: the app's system identity needs Key Vault Secrets User (resolve the secret)
// and AcrPull (pull the image). Scoped to the vault and the registry respectively.
// ---------------------------------------------------------------------------

var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets User
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull

resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, containerApp.id, kvSecretsUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
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
output containerAppPrincipalId string = containerApp.identity.principalId
output internalFqdn string = containerApp.properties.configuration.ingress.fqdn
output readyUrl string = 'http://${containerApp.properties.configuration.ingress.fqdn}/api/v1/ready'
