param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("stop", "precompact")]
    [string]$Hook,

    [string]$Harness = "claude-code"
)

$env:PYTHONUTF8 = "1"

$mempalace = Get-Command mempalace -ErrorAction SilentlyContinue
if (-not $mempalace) {
    Write-Warning "mempalace is not on PATH; skipping MemPalace $Hook hook."
    exit 0
}

& $mempalace.Source hook run --hook $Hook --harness $Harness
exit $LASTEXITCODE
