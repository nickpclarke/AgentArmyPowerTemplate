param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("stop", "precompact")]
    [string]$Hook,

    [string]$Harness = "claude-code"
)

$env:PYTHONUTF8 = "1"

$mempalace = Get-Command mempalace -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $mempalace) {
    Write-Warning "mempalace is not on PATH; skipping MemPalace $Hook hook."
    exit 0
}

& $mempalace hook run --hook $Hook --harness $Harness
exit $LASTEXITCODE
