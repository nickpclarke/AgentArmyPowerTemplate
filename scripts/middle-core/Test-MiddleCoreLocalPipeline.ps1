param(
    [int]$Port = 18001,
    [switch]$SkipDocs
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$modelPath = Join-Path $repoRoot "model\middle-core\model.yaml"
$generatedOut = Join-Path $repoRoot "templates\middle-core\generated"
$projectPath = Join-Path $repoRoot "templates\middle-core\MiddleCore.csproj"
$catalogPath = (Resolve-Path (Join-Path $repoRoot "templates\business-object-catalog.example.json")).Path
$baseUrl = "http://127.0.0.1:$Port"
$stdout = Join-Path $env:TEMP "middle-core-local-pipeline-out.log"
$stderr = Join-Path $env:TEMP "middle-core-local-pipeline-err.log"

function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

Push-Location $repoRoot
try {
    Invoke-CheckedNative python tools\modelgen\validate_middle_core.py --model $modelPath
    Invoke-CheckedNative python tools\modelgen\generate_middle_core.py --model $modelPath --out $generatedOut
    Invoke-CheckedNative python -m unittest tests.test_middle_core_modelgen
    Invoke-CheckedNative dotnet build $projectPath
    Invoke-CheckedNative dotnet test $projectPath
    Invoke-CheckedNative node tools\business-object-catalog.mjs validate

    if (-not $SkipDocs) {
        Invoke-CheckedNative python -m mkdocs build
    }

    $env:BUSINESS_OBJECT_CATALOG = $catalogPath
    $env:ASPNETCORE_URLS = $baseUrl
    $proc = Start-Process -FilePath "dotnet" -ArgumentList @("run", "--project", $projectPath, "--no-build") -WorkingDirectory $repoRoot -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru

    try {
        $health = $null
        $lastError = $null
        $deadline = (Get-Date).AddSeconds(30)
        while ((Get-Date) -lt $deadline) {
            try {
                $candidate = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 2
                if ($candidate.status -eq "ok") {
                    $health = $candidate
                    break
                }
            }
            catch {
                $lastError = $_
                Start-Sleep -Milliseconds 500
            }
        }

        if (-not $health) {
            throw "middle-core did not become healthy. lastError=$lastError stdout=$(Get-Content $stdout -Raw) stderr=$(Get-Content $stderr -Raw)"
        }

        $model = Invoke-RestMethod -Uri "$baseUrl/model" -TimeoutSec 5
        $demo = Invoke-WebRequest -Uri "$baseUrl/model/demo" -UseBasicParsing -TimeoutSec 5
        $scenarioRun = Invoke-RestMethod -Uri "$baseUrl/model/scenarios/knowledge-drop/run" -TimeoutSec 5
        $failureStatus = $null
        try {
            Invoke-RestMethod -Uri "$baseUrl/model/scenarios/knowledge-drop/run?disableLastHandler=true" -TimeoutSec 5 | Out-Null
        }
        catch {
            if ($null -eq $_.Exception.Response) {
                throw "disabled-handler request failed before a response was received: $_"
            }
            $failureStatus = [int]$_.Exception.Response.StatusCode
        }

        if ($model.model_id -ne "middle-core-runtime-prototype") {
            throw "Unexpected generated model id '$($model.model_id)'."
        }
        foreach ($requiredDemoText in @("Knowledge Drop Scenario Lab", "Run success path", "Run disabled-handler path", "Runtime Object Graph", "Step Evidence")) {
            if (-not $demo.Content.Contains($requiredDemoText)) {
                throw "Scenario lab page is missing '$requiredDemoText'."
            }
        }
        if ($scenarioRun.status -ne "passed") {
            throw "knowledge-drop scenario did not pass."
        }
        if ($failureStatus -ne 400) {
            throw "disabled-handler scenario expected HTTP 400 but saw '$failureStatus'."
        }

        Invoke-CheckedNative node tools\middle-core-ui-smoke.mjs $baseUrl
        $env:MIDDLE_CORE_BASE_URL = $baseUrl
        Invoke-CheckedNative npx playwright test tests/e2e/middle-core-scenario-lab.spec.js --project=chromium
        Remove-Item Env:\MIDDLE_CORE_BASE_URL -ErrorAction SilentlyContinue

        [pscustomobject]@{
            Status = "passed"
            BaseUrl = $baseUrl
            Health = $health.status
            ModelId = $model.model_id
            DemoUrl = "$baseUrl/model/demo"
            KnowledgeDropStatus = $scenarioRun.status
            KnowledgeDropObjects = $scenarioRun.graph.objects.Count
            KnowledgeDropEdges = $scenarioRun.graph.edges.Count
            DisabledHandlerStatus = $failureStatus
            HealthUrl = "$baseUrl/health"
            ModelUrl = "$baseUrl/model"
            ScenarioRunUrl = "$baseUrl/model/scenarios/knowledge-drop/run"
        } | ConvertTo-Json
    }
    finally {
        if ($proc -and -not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force
        }
        Remove-Item Env:\BUSINESS_OBJECT_CATALOG -ErrorAction SilentlyContinue
        Remove-Item Env:\ASPNETCORE_URLS -ErrorAction SilentlyContinue
    }
}
finally {
    Pop-Location
}
