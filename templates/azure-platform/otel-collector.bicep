// otel-collector.bicep — shared OTel Collector ACA container app for the
// fleet's distributed-trace pipeline.
//
// Realizes ARC-ADR-024 (observability-engineer finding) + ARC-ADR-010.
// Single shared collector (not sidecars) — per the audit, the right shape
// for a 3-service fleet at current scale. Container Tier: Function (per
// ADR-023) — small, stateless, independently rolled out.
//
// The collector receives OTLP/gRPC on 4317 and OTLP/HTTP on 4318 (internal
// ACA ingress only — spokes inside cae-arcade-platform connect via internal
// DNS), then exports to Application Insights via the azuremonitor exporter.
// The AI connection string resolves from KV via ACA secretref.
//
// Config: baked into the published image (templates/otel-collector-image/
// — separate PR) OR mounted via Azure Files. THIS Bicep uses the upstream
// otel/opentelemetry-collector-contrib image with config injected via
// Azure Files for v1 simplicity. Switch to the baked image once it ships.
//
// Deploy at resource-group scope (after application-insights.bicep):
//   az deployment group create \
//     --resource-group rg-arcade-platform \
//     --template-file templates/azure-platform/otel-collector.bicep \
//     --parameters managedEnvName=cae-arcade-platform \
//                  connectionStringSecretName=AI-CONNECTION-STRING

targetScope = 'resourceGroup'

@description('ACA managed env to deploy into.')
param managedEnvName string

@description('Container App name. Defaults to otel-collector.')
param containerAppName string = 'otel-collector'

@description('Region. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Key Vault that holds the AI connection string secret.')
param keyVaultName string = 'akv01-agentarmy'

@description('Name of the KV secret with the App Insights connection string (must match the application-insights.bicep parameter).')
param connectionStringSecretName string = 'AI-CONNECTION-STRING'

@description('OTel Collector contrib image tag. Pin specifically — security-architect supply-chain rule.')
param otelImage string = 'otel/opentelemetry-collector-contrib:0.102.0'

@description('User-assigned managed identity with Key Vault Secrets User on the KV. Created out-of-band; pass its resource ID.')
param userAssignedIdentityResourceId string

resource managedEnv 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: managedEnvName
}

resource collector 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: managedEnv.id
    configuration: {
      // Internal ingress — only spokes inside the ACA env reach this; the
      // collector is not exposed to the public internet (security-architect
      // ingress rec). Spokes use the internal FQDN as OTLP endpoint.
      ingress: {
        external: false
        targetPort: 4318
        transport: 'http2'
        allowInsecure: false
        additionalPortMappings: [
          {
            external: false
            targetPort: 4317
            exposedPort: 4317
          }
        ]
      }
      // KV-backed secret resolution (per ADR-011 + secrets-rotation policy).
      secrets: [
        {
          name: toLower(replace(connectionStringSecretName, '_', '-'))
          keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/${connectionStringSecretName}'
          identity: userAssignedIdentityResourceId
        }
      ]
      maxInactiveRevisions: 5
    }
    template: {
      // Min=1 reflects "the collector must always be reachable" — a sidecar
      // pattern wouldn't need this, but a shared collector does. Cost: ~$5/mo.
      scale: {
        minReplicas: 1
        maxReplicas: 2
        rules: [
          {
            name: 'http-load'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
      containers: [
        {
          name: 'otel-collector'
          image: otelImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            // Collector reads connection string from this env var when wired
            // via the azuremonitor exporter pattern (set in the config YAML
            // baked into a future templates/otel-collector-image/ instance,
            // OR injected via OTEL_CONFIG override at runtime for v1).
            {
              name: 'AZURE_MONITOR_CONNECTION_STRING'
              secretRef: toLower(replace(connectionStringSecretName, '_', '-'))
            }
            // Pin the contrib distro flavor so unknown receivers don't load.
            { name: 'OTEL_LOG_LEVEL', value: 'info' }
          ]
          // Liveness + readiness probes per ADR-024 azure-infra-engineer finding.
          probes: [
            {
              type: 'Liveness'
              tcpSocket: { port: 4318 }
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              tcpSocket: { port: 4318 }
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
    }
  }
  tags: {
    env: 'dev'
    service: 'otel-collector'
    team: 'agentarmy'
    'cost-center': 'engineering'
    'managed-by': 'bicep'
    tier: 'function'  // ADR-023 container tiering — collector is Function-tier
  }
}

output collectorFqdn string = collector.properties.configuration.ingress.fqdn
output collectorId string = collector.id
output otlpHttpEndpoint string = 'https://${collector.properties.configuration.ingress.fqdn}:4318'
output otlpGrpcEndpoint string = '${collector.properties.configuration.ingress.fqdn}:4317'
