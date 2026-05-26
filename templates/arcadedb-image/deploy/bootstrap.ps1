#Requires -Version 7
<#
.SYNOPSIS
  One-time Azure setup for the ArcadeDB ACA dev deployment (PowerShell / pwsh version).

.DESCRIPTION
  Creates/verifies: resource group, ACR, Log Analytics, ACA environment, Key Vault
  secrets, Entra ID app registration with OIDC federated credentials.
  Prints the three AZURE_* secret values to add to the spoke repo.

.EXAMPLE
  .\bootstrap.ps1 `
    -Subscription  '00000000-0000-0000-0000-000000000000' `
    -ResourceGroup 'rg-arcadedb-dev' `
    -AcrName       'myacr' `
    -GitHubOrg     'nickpclarke' `
    -GitHubRepo    'backend-core'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Subscription,

    [string]$ResourceGroup = 'rg-arcadedb-dev',
    [string]$Location      = 'eastus',

    [Parameter(Mandatory)]
    [string]$AcrName,

    [string]$AcaEnvName   = 'cae-backend-dev',
    [string]$KeyVaultName = 'akv01-agentarmy',

    [Parameter(Mandatory)]
    [string]$GitHubOrg,

    [Parameter(Mandatory)]
    [string]$GitHubRepo
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Az {
    param([string[]]$Args)
    $output = az @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "az $($Args[0..1] -join ' ') failed: $output"
    }
    return $output
}

function New-RandomPassword {
    # 32 chars, alphanumeric + limited punctuation — excludes : [ ] { } (ArcadeDB delimiters)
    $chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#%^&*()-_=+'
    -join ((1..32) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

# ---------------------------------------------------------------------------
Write-Host "==> Setting subscription context to: $Subscription"
Invoke-Az @('account', 'set', '--subscription', $Subscription) | Out-Null

# ---------------------------------------------------------------------------
Write-Host "==> Ensuring resource group: $ResourceGroup"
Invoke-Az @('group', 'create', '--name', $ResourceGroup, '--location', $Location, '--output', 'none') | Out-Null

# ---------------------------------------------------------------------------
Write-Host "==> Ensuring ACR: $AcrName"
$acrExists = az acr show --name $AcrName --query loginServer -o tsv 2>$null
if ($LASTEXITCODE -ne 0) {
    Invoke-Az @('acr', 'create', '--resource-group', $ResourceGroup, '--name', $AcrName,
        '--sku', 'Basic', '--admin-enabled', 'false', '--output', 'none') | Out-Null
}
$acrLoginServer = az acr show --name $AcrName --query loginServer -o tsv
Write-Host "    ACR login server: $acrLoginServer"

# ---------------------------------------------------------------------------
Write-Host "==> Ensuring Log Analytics workspace: law-arcadedb-dev"
$lawName = 'law-arcadedb-dev'
$lawExists = az monitor log-analytics workspace show `
    --resource-group $ResourceGroup --workspace-name $lawName --query customerId -o tsv 2>$null
if ($LASTEXITCODE -ne 0) {
    Invoke-Az @('monitor', 'log-analytics', 'workspace', 'create',
        '--resource-group', $ResourceGroup, '--workspace-name', $lawName,
        '--location', $Location, '--output', 'none') | Out-Null
}
$lawId  = az monitor log-analytics workspace show `
    --resource-group $ResourceGroup --workspace-name $lawName --query customerId -o tsv
$lawKey = az monitor log-analytics workspace get-shared-keys `
    --resource-group $ResourceGroup --workspace-name $lawName --query primarySharedKey -o tsv

Write-Host "==> Ensuring ACA environment: $AcaEnvName"
$acaExists = az containerapp env show --name $AcaEnvName --resource-group $ResourceGroup 2>$null
if ($LASTEXITCODE -ne 0) {
    Invoke-Az @('containerapp', 'env', 'create',
        '--name', $AcaEnvName, '--resource-group', $ResourceGroup,
        '--location', $Location,
        '--logs-workspace-id', $lawId, '--logs-workspace-key', $lawKey,
        '--output', 'none') | Out-Null
} else {
    Write-Host "    (ACA environment already exists)"
}

# ---------------------------------------------------------------------------
Write-Host "==> Checking Key Vault secrets in: $KeyVaultName"

function Set-SecretIfMissing {
    param([string]$Name, [string]$Value)
    $existing = az keyvault secret show --vault-name $KeyVaultName --name $Name 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ${Name}: already exists — skipping"
    } else {
        Invoke-Az @('keyvault', 'secret', 'set',
            '--vault-name', $KeyVaultName,
            '--name', $Name,
            '--value', $Value,
            '--output', 'none') | Out-Null
        Write-Host "    ${Name}: created"
    }
}

Set-SecretIfMissing -Name 'arcadedb-root-password'    -Value (New-RandomPassword)
Set-SecretIfMissing -Name 'arcadedb-service-password' -Value (New-RandomPassword)

# ---------------------------------------------------------------------------
Write-Host "==> Ensuring app registration"
$appName   = "sp-arcadedb-aca-deploy-$GitHubRepo"
$appId     = az ad app list --display-name $appName --query '[0].appId' -o tsv 2>$null
$tenantId  = az account show --query tenantId -o tsv
$subId     = az account show --query id -o tsv

if ([string]::IsNullOrEmpty($appId)) {
    $appId = az ad app create --display-name $appName --query appId -o tsv
    Write-Host "    Created app: $appId"
    Invoke-Az @('ad', 'sp', 'create', '--id', $appId, '--output', 'none') | Out-Null
} else {
    Write-Host "    App already exists: $appId"
}

$spOid = az ad sp show --id $appId --query id -o tsv

Write-Host "==> Assigning Contributor on resource group"
$rgScope = "/subscriptions/$subId/resourceGroups/$ResourceGroup"
az role assignment create `
    --assignee-object-id $spOid --assignee-principal-type ServicePrincipal `
    --role Contributor --scope $rgScope --output none 2>$null | Out-Null

Write-Host "==> Assigning Key Vault Secrets User on vault"
$kvId = az keyvault show --name $KeyVaultName --query id -o tsv
az role assignment create `
    --assignee-object-id $spOid --assignee-principal-type ServicePrincipal `
    --role 'Key Vault Secrets User' --scope $kvId --output none 2>$null | Out-Null

# ---------------------------------------------------------------------------
Write-Host "==> Creating OIDC federated credentials"

function Add-FederatedCredential {
    param([string]$CredName, [string]$Subject)
    $existing = az ad app federated-credential list --id $appId `
        --query "[?name=='$CredName'].name" -o tsv 2>$null
    if (-not [string]::IsNullOrEmpty($existing)) {
        Write-Host "    ${CredName}: already exists — skipping"
        return
    }
    $params = @{
        name      = $CredName
        issuer    = 'https://token.actions.githubusercontent.com'
        subject   = $Subject
        audiences = @('api://AzureADTokenExchange')
    } | ConvertTo-Json -Compress
    Invoke-Az @('ad', 'app', 'federated-credential', 'create',
        '--id', $appId, '--parameters', $params, '--output', 'none') | Out-Null
    Write-Host "    ${CredName}: created"
}

Add-FederatedCredential -CredName 'github-main' `
    -Subject "repo:${GitHubOrg}/${GitHubRepo}:ref:refs/heads/main"
Add-FederatedCredential -CredName 'github-workflow-dispatch' `
    -Subject "repo:${GitHubOrg}/${GitHubRepo}:ref:refs/heads/main"

# ---------------------------------------------------------------------------
Write-Host ""
Write-Host ("=" * 72)
Write-Host "  Bootstrap complete. Add the following to:"
Write-Host "  Settings > Secrets > Actions  in  ${GitHubOrg}/${GitHubRepo}"
Write-Host ("=" * 72)
Write-Host ""
Write-Host "  AZURE_CLIENT_ID       = $appId"
Write-Host "  AZURE_TENANT_ID       = $tenantId"
Write-Host "  AZURE_SUBSCRIPTION_ID = $subId"
Write-Host ""
Write-Host "  Also set these as repo Variables (Settings > Variables > Actions):"
Write-Host "  AZURE_ACR_LOGIN_SERVER = $acrLoginServer"
Write-Host "  AZURE_RESOURCE_GROUP   = $ResourceGroup"
Write-Host ""
Write-Host "  The ArcadeDB passwords are stored in Key Vault '$KeyVaultName'."
Write-Host "  Secret names:"
Write-Host "    arcadedb-root-password"
Write-Host "    arcadedb-service-password"
Write-Host ""
Write-Host "  UDA connection for backend-core:"
Write-Host "    ARCADEDB_URL      = https://<fqdn from deploy output>"
Write-Host "    ARCADEDB_DATABASE = knowledge"
Write-Host "    ARCADEDB_USER     = platform_reader"
Write-Host "    secret_ref        = akv:arcadedb-service-password"
Write-Host ("=" * 72)
