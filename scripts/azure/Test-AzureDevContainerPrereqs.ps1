param(
    [string]$SubscriptionId = "",
    [string]$ResourceGroup = "",
    [string]$AcrName = "",
    [string]$ContainerAppName = ""
)

$ErrorActionPreference = "Stop"

function Test-CommandAvailable {
    param([string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command not found on PATH: $Name"
    }
    Write-Host "OK: $Name -> $($command.Source)"
}

Test-CommandAvailable -Name "az"
Test-CommandAvailable -Name "docker"

Write-Host ""
Write-Host "Docker:"
docker version --format "{{.Client.Version}} client / {{.Server.Version}} server"
docker compose version

Write-Host ""
Write-Host "Azure CLI:"
$azVersion = az version --output json | ConvertFrom-Json
Write-Host "OK: az $($azVersion.'azure-cli')"

$extensions = az extension list --output json | ConvertFrom-Json
$containerAppExtension = $extensions | Where-Object { $_.name -eq "containerapp" }
if ($containerAppExtension) {
    Write-Host "OK: containerapp extension $($containerAppExtension.version)"
} else {
    Write-Host "WARN: Azure CLI containerapp extension is not installed."
    Write-Host "      Install with: az extension add --name containerapp"
}

Write-Host ""
Write-Host "Azure account:"
$account = az account show --output json | ConvertFrom-Json
Write-Host "OK: signed in as $($account.user.name)"
Write-Host "OK: subscription $($account.name) [$($account.id)]"

if ($SubscriptionId -and $account.id -ne $SubscriptionId) {
    throw "Active subscription is $($account.id), expected $SubscriptionId. Run: az account set --subscription `"$SubscriptionId`""
}

if ($ResourceGroup) {
    Write-Host ""
    Write-Host "Resource group:"
    az group show --name $ResourceGroup --output table
}

if ($AcrName) {
    Write-Host ""
    Write-Host "Azure Container Registry:"
    az acr show --name $AcrName --query "{name:name,loginServer:loginServer,sku:sku.name}" --output table
}

if ($ResourceGroup -and $ContainerAppName) {
    Write-Host ""
    Write-Host "Azure Container App:"
    az containerapp show `
        --resource-group $ResourceGroup `
        --name $ContainerAppName `
        --query "{name:name,provisioningState:properties.provisioningState,latestRevision:properties.latestRevisionName,fqdn:properties.configuration.ingress.fqdn}" `
        --output table
}

Write-Host ""
Write-Host "Azure Dev container prerequisites look usable from this host."
