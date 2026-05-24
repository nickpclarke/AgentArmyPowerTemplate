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
$lastError = $null

while ((Get-Date) -lt $deadline) {
    try {
        $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 2
        break
    }
    catch {
        $lastError = $_
        Start-Sleep -Milliseconds 500
    }
}

if (-not $health) {
    docker logs $ContainerName --tail 50
    throw "middle-core did not become healthy at $baseUrl/health. lastError=$lastError"
}

$explorer = Invoke-WebRequest -Uri "$baseUrl/" -UseBasicParsing -TimeoutSec 5
if (-not $explorer.Content.Contains("Business Object Catalog")) {
    throw "middle-core explorer did not render the Business Object Catalog page."
}

$model = Invoke-RestMethod -Uri "$baseUrl/model" -TimeoutSec 5
if ($model.model_id -ne "middle-core-runtime-prototype") {
    throw "middle-core generated model endpoint returned unexpected model_id '$($model.model_id)'."
}

$demo = Invoke-WebRequest -Uri "$baseUrl/model/demo" -UseBasicParsing -TimeoutSec 5
foreach ($requiredDemoText in @("Knowledge Drop Scenario Lab", "Run success path", "Run disabled-handler path", "Runtime Object Graph", "Step Evidence")) {
    if (-not $demo.Content.Contains($requiredDemoText)) {
        throw "middle-core scenario lab page is missing '$requiredDemoText'."
    }
}

$scenarioRun = Invoke-RestMethod -Uri "$baseUrl/model/scenarios/knowledge-drop/run" -TimeoutSec 5
if ($scenarioRun.status -ne "passed") {
    throw "middle-core knowledge-drop scenario did not pass."
}

$failureStatus = $null
try {
    Invoke-RestMethod -Uri "$baseUrl/model/scenarios/knowledge-drop/run?disableLastHandler=true" -TimeoutSec 5 | Out-Null
}
catch {
    if ($null -eq $_.Exception.Response) {
        throw "disabled-handler smoke failed before a response was received: $_"
    }
    $failureStatus = [int]$_.Exception.Response.StatusCode
}

if ($failureStatus -ne 400) {
    throw "middle-core disabled-handler smoke expected HTTP 400 but saw '$failureStatus'."
}

[pscustomobject]@{
    Status = $health.status
    Service = $health.service
    CatalogId = $health.catalog_id
    ObjectTypes = $health.object_types
    Scenarios = $health.scenarios
    ModelId = $model.model_id
    DemoUrl = "$baseUrl/model/demo"
    KnowledgeDropStatus = $scenarioRun.status
    KnowledgeDropObjects = $scenarioRun.graph.objects.Count
    KnowledgeDropEdges = $scenarioRun.graph.edges.Count
    DisabledHandlerStatus = $failureStatus
    ExplorerUrl = "$baseUrl/"
    HealthUrl = "$baseUrl/health"
    ModelUrl = "$baseUrl/model"
    ScenarioRunUrl = "$baseUrl/model/scenarios/knowledge-drop/run"
    CatalogUrl = "$baseUrl/catalog"
    ContainerName = $ContainerName
    ImageName = $ImageName
}
