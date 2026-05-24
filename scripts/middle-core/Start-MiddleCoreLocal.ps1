param(
    [string]$ImageName = "middle-core:local",
    [string]$ContainerName = "middle-core-local",
    [int]$HostPort = 18001,
    [int]$ContainerPort = 8001,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$dockerfile = Join-Path $repoRoot "templates\middle-core\Dockerfile"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI is required to deploy middle-core locally."
}

if (-not (Test-Path $dockerfile)) {
    throw "Middle-core Dockerfile not found at $dockerfile"
}

if (-not $NoBuild) {
    docker build -f $dockerfile -t $ImageName $repoRoot
}

$existing = docker ps -aq --filter "name=^/$ContainerName$"
if ($existing) {
    docker rm -f $ContainerName | Out-Null
}

docker run -d --name $ContainerName -p "${HostPort}:${ContainerPort}" $ImageName | Out-Null

$baseUrl = "http://127.0.0.1:$HostPort"
$deadline = (Get-Date).AddSeconds(20)
$health = $null

while ((Get-Date) -lt $deadline) {
    try {
        $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 2
        break
    }
    catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $health) {
    docker logs $ContainerName --tail 50
    throw "middle-core did not become healthy at $baseUrl/health"
}

$explorer = Invoke-WebRequest -Uri "$baseUrl/" -UseBasicParsing -TimeoutSec 5
if (-not $explorer.Content.Contains("Business Object Catalog")) {
    throw "middle-core explorer did not render the Business Object Catalog page."
}

[pscustomobject]@{
    Status = $health.status
    Service = $health.service
    CatalogId = $health.catalog_id
    ObjectTypes = $health.object_types
    Scenarios = $health.scenarios
    ExplorerUrl = "$baseUrl/"
    HealthUrl = "$baseUrl/health"
    CatalogUrl = "$baseUrl/catalog"
    ContainerName = $ContainerName
    ImageName = $ImageName
}
