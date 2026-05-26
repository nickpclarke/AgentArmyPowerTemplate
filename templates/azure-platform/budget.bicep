// budget.bicep — subscription-scoped Azure cost budget with email alerts.
//
// Realizes ARC-ADR-024 finding 7 (finops-engineer): no budget alerts exist
// today, current burn ~$135-170/mo, single dev environment. This module is
// the foundation; split into per-env budgets (dev/stg/prd) once envs are
// labeled per ARC-ADR-023 + ARC-ADR-024 (rg-aa-<env>-<tier>).
//
// Deploy at subscription scope:
//   az deployment sub create \
//     --location eastus \
//     --template-file templates/azure-platform/budget.bicep \
//     --parameters budgetAmount=150 contactEmail=nick@livecreative.com
//
// Notification thresholds (Actual cost): 50% / 75% / 90% / 100%.
// All four fire emails to the configured contact list — no SMS / webhook at
// this scale (ADR-024 paging strategy keeps interrupt path minimal).

targetScope = 'subscription'

@description('Monthly budget amount in subscription billing currency (USD assumed).')
@minValue(10)
@maxValue(10000)
param budgetAmount int = 150

@description('Email contact for budget alerts.')
param contactEmail string

@description('Budget name suffix (final name: agentarmy-<env>-monthly).')
param env string = 'dev'

@description('First day of the budget window (RFC3339, billing-period aligned). Defaults to next month start.')
param startDate string = '${utcNow('yyyy')}-${utcNow('MM')}-01'

var budgetName = 'agentarmy-${env}-monthly'

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: budgetName
  properties: {
    category: 'Cost'
    amount: budgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
    }
    notifications: {
      threshold50: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 50
        thresholdType: 'Actual'
        contactEmails: [contactEmail]
      }
      threshold75: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 75
        thresholdType: 'Actual'
        contactEmails: [contactEmail]
      }
      threshold90: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 90
        thresholdType: 'Actual'
        contactEmails: [contactEmail]
      }
      threshold100: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Actual'
        contactEmails: [contactEmail]
      }
    }
  }
}

output budgetId string = budget.id
output budgetName string = budget.name
