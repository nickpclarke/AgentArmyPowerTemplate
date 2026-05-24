param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$AcrName,

    [Parameter(Mandatory = $true)]
    [string]$ContainerAppName,

    [Parameter(Mandatory = $true)]
    [string]$ServiceName,

    [string]$SubscriptionId = "",
    [string]$Dockerfile = "Dockerfile",
    [string]$Context = ".",
    [string]$Tag = ""
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: $Name"
    }
}

function Get-SafeRevisionSuffix {
    param([string]$Value)

    $suffix = $Value.ToLowerInvariant() -replace "[^a-z0-9-]", "-"
    $suffix = $suffix.Trim("-")
    if ($suffix.Length -gt 54) {
        $suffix = $suffix.Substring(0, 54).Trim("-")
    }
    if (-not $suffix) {
        $suffix = "dev"
    }
    return "dev-$suffix"
}

Require-Command -Name "az"
Require-Command -Name "docker"

if ($SubscriptionId) {
    az account set --subscription $SubscriptionId
}

$account = az account show --output json | ConvertFrom-Json
Write-Host "Azure account: $($account.user.name)"
Write-Host "Subscription: $($account.name) [$($account.id)]"

$acr = az acr show --name $AcrName --output json | ConvertFrom-Json
$loginServer = $acr.loginServer

if (-not $Tag) {
    $gitSha = ""
    try {
        $gitSha = git rev-parse --short HEAD 2>$null
    } catch {
        $gitSha = ""
    }
    if (-not $gitSha) {
        $gitSha = Get-Date -Format "yyyyMMddHHmmss"
    }
    $Tag = $gitSha
}

$image = "$loginServer/$ServiceName`:$Tag"
$revisionSuffix = Get-SafeRevisionSuffix -Value $Tag

Write-Host "Logging into ACR: $AcrName"
az acr login --name $AcrName

Write-Host "Building image: $image"
docker build --pull --file $Dockerfile --tag $image $Context

Write-Host "Pushing image: $image"
docker push $image

Write-Host "Updating Azure Container App: $ContainerAppName"
az containerapp update `
    --resource-group $ResourceGroup `
    --name $ContainerAppName `
    --image $image `
    --revision-suffix $revisionSuffix `
    --output none

$app = az containerapp show `
    --resource-group $ResourceGroup `
    --name $ContainerAppName `
    --query "{name:name,latestRevision:properties.latestRevisionName,fqdn:properties.configuration.ingress.fqdn}" `
    --output json | ConvertFrom-Json

Write-Host ""
Write-Host "Azure Dev deploy complete."
Write-Host "Image: $image"
Write-Host "Revision: $($app.latestRevision)"
if ($app.fqdn) {
    Write-Host "URL: https://$($app.fqdn)"
}
