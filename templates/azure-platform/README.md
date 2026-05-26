# `templates/azure-platform/` — shared Azure platform modules

Bicep modules for cross-cutting Azure concerns owned by the hub (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md) — Platform Image Ownership). These deploy at **subscription scope** or to a **shared `rg-aa-shared-*` resource group**, not per-app.

| Module | Scope | Purpose | ADR |
|---|---|---|---|
| `budget.bicep` | Subscription | Cost budget + 50/75/90/100% email alerts | [ADR-024](../../docs/decisions/ARC-ADR-024-platform-maturity-audit.md) finding 7 |

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
