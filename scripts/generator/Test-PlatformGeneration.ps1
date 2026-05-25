param(
    [string]$Target = "backend-core",
    [int]$Port = 18001,
    [switch]$SkipDocs,
    [switch]$ListTargets
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$manifestPath = Join-Path $repoRoot "generator\platform-test.manifest.json"

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    return Get-Content $Path -Raw | ConvertFrom-Json
}

$manifest = Read-JsonFile $manifestPath

if ($ListTargets) {
    $manifest.targets | Select-Object id, status, manifest | Format-Table -AutoSize
    return
}

$targetEntry = $manifest.targets | Where-Object { $_.id -eq $Target } | Select-Object -First 1
if (-not $targetEntry) {
    $knownTargets = ($manifest.targets | ForEach-Object { $_.id }) -join ", "
    throw "Unknown generator target '$Target'. Known targets: $knownTargets"
}

$targetManifestPath = Join-Path (Join-Path $repoRoot "generator") $targetEntry.manifest
$targetManifest = Read-JsonFile $targetManifestPath

if ($targetManifest.status -ne "active") {
    throw "Generator target '$Target' is '$($targetManifest.status)'. No runnable platform test exists yet. Manifest: $targetManifestPath"
}

switch ($Target) {
    "middle-core" {
        $pipeline = Join-Path $repoRoot $targetManifest.localhost_pipeline
        # $pipeline is a .ps1, so $LASTEXITCODE would reflect its last native call, not the
        # pipeline's own success. Rely on the terminating error it raises under -ErrorAction Stop.
        try {
            & $pipeline -Port $Port -SkipDocs:$SkipDocs
        }
        catch {
            throw "Platform generation pipeline failed for target '$Target': $_"
        }
    }
    default {
        throw "No platform generation runner is registered for active target '$Target'."
    }
}
