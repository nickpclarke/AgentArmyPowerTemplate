# `templates/azure-platform/` — shared Azure platform modules

Bicep modules for cross-cutting Azure concerns owned by the hub (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md) — Platform Image Ownership). These deploy at **subscription scope** or to a **shared `rg-aa-shared-*` resource group**, not per-app.

| Module | Scope | Purpose | ADR |
|---|---|---|---|
| `budget.bicep` | Subscription | Cost budget + 50/75/90/100% email alerts | [ADR-024](../../docs/decisions/ARC-ADR-024-platform-maturity-audit.md) finding 7 |
| `application-insights.bicep` | Resource Group | App Insights bound to Log Analytics + KV-stored connection string | [ADR-010](../../docs/decisions/ARC-ADR-010-observability-standard.md) + [ADR-024](../../docs/decisions/ARC-ADR-024-platform-maturity-audit.md) finding 2 |
| `otel-collector.bicep` | Resource Group | Shared OTel Collector ACA container app (internal ingress, OTLP/gRPC :4317 + OTLP/HTTP :4318 → AI) | [ADR-024](../../docs/decisions/ARC-ADR-024-platform-maturity-audit.md) finding 2 |

## Deploy

```bash
# Budget (subscription scope) — adjust budgetAmount per env when stg/prd land
az deployment sub create \
  --location eastus \
  --template-file templates/azure-platform/budget.bicep \
  --parameters budgetAmount=150 contactEmail=nick@livecreative.com env=dev
```

Add per-env budgets once `rg-aa-<env>-<tier>` naming lands (issue [#219](https://github.com/nickpclarke/AgentArmy/issues/219)):

```bash
az deployment sub create -l eastus -f templates/azure-platform/budget.bicep \
  --parameters budgetAmount=75  contactEmail=nick@livecreative.com env=dev
az deployment sub create -l eastus -f templates/azure-platform/budget.bicep \
  --parameters budgetAmount=150 contactEmail=nick@livecreative.com env=stg
az deployment sub create -l eastus -f templates/azure-platform/budget.bicep \
  --parameters budgetAmount=400 contactEmail=nick@livecreative.com env=prd
```

### Observability foundation (two-step deploy)

App Insights first — provisions the AI component bound to the existing Log Analytics workspace + stashes the connection string in Key Vault:

```bash
az deployment group create \
  --resource-group rg-arcade-platform \
  --template-file templates/azure-platform/application-insights.bicep \
  --parameters workspaceName=workspace-rgarcadeplatformzJ8M
```

Then the OTel Collector — ACA container app with internal ingress that fan-ins OTLP from every spoke → exports to AI (Function-tier per ADR-023). Requires a user-assigned managed identity with `Key Vault Secrets User` role on `akv01-agentarmy` (create out-of-band; pass its resource ID):

```bash
az deployment group create \
  --resource-group rg-arcade-platform \
  --template-file templates/azure-platform/otel-collector.bicep \
  --parameters managedEnvName=cae-arcade-platform \
               userAssignedIdentityResourceId=<UAMI_RESOURCE_ID>
```

Spokes point their OTel SDK at the internal collector FQDN once it lands (output by the deploy). Issues fe#57 / be#100 / mc#86 own the per-spoke SDK init.

