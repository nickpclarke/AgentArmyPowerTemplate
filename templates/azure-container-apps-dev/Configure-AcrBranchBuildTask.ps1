param(
    [Parameter(Mandatory = $true)]
    [string]$AcrName,

    [Parameter(Mandatory = $true)]
    [string]$TaskName,

    [Parameter(Mandatory = $true)]
    [string]$RepositoryUrl,

    [string]$Branch = "azure-dev",
    [string]$TaskFile = "acr-task.yaml",
    [string]$ImageRepository = "",
    [string]$Dockerfile = "Dockerfile",
    [string]$Context = ".",
    [string]$GitAccessToken = ""
)

$ErrorActionPreference = "Stop"

if (-not $ImageRepository) {
    $ImageRepository = $TaskName -replace "-dev-build$", ""
}

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required."
}

if (-not (Test-Path -LiteralPath $TaskFile)) {
    throw "ACR task file not found: $TaskFile"
}

$sourceContext = "$RepositoryUrl#$Branch"
$values = "imageRepository=$ImageRepository dockerfile=$Dockerfile context=$Context"

$args = @(
    "acr", "task", "create",
    "--registry", $AcrName,
    "--name", $TaskName,
    "--file", $TaskFile,
    "--context", $sourceContext,
    "--set", $values,
    "--commit-trigger-enabled", "true",
    "--pull-request-trigger-enabled", "false"
)

if ($GitAccessToken) {
    $args += @("--git-access-token", $GitAccessToken)
}

Write-Host "Creating or updating ACR branch build task."
Write-Host "Registry: $AcrName"
Write-Host "Task: $TaskName"
Write-Host "Context: $sourceContext"
Write-Host "Image repository: $ImageRepository"

az @args

Write-Host ""
Write-Host "ACR task configured. Commit promotion to '$Branch' will trigger Azure-side Dev builds."
