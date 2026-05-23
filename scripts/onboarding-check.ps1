param(
  [string]$Owner = "",
  [string]$Repo = "AgentArmy",
  [int]$ProjectNumber = 1,
  [switch]$CreateTestIssue
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "== $Message =="
}

function Pass {
  param([string]$Message)
  Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Warn {
  param([string]$Message)
  Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Fail {
  param([string]$Message)
  Write-Host "[FAIL] $Message" -ForegroundColor Red
  $script:Failures += $Message
}

function Run-Gh {
  param([string[]]$GhArgs)
  $oldErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $output = & gh @GhArgs 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldErrorActionPreference
  }
  return [pscustomobject]@{
    Code = $code
    Output = ($output -join "`n")
  }
}

$Failures = @()

if (-not $Owner) {
  $ownerResult = Run-Gh -GhArgs @("repo", "view", "--json", "owner", "--jq", ".owner.login")
  if ($ownerResult.Code -eq 0 -and $ownerResult.Output.Trim()) {
    $Owner = $ownerResult.Output.Trim()
  }
}

if (-not $Owner) {
  Fail "Could not infer repository owner. Pass -Owner YOUR_USERNAME."
  exit 1
}

$FullRepo = "$Owner/$Repo"

Write-Host "AgentArmy onboarding sanity check"
Write-Host "Repository: $FullRepo"
Write-Host "Project:    $Owner/$ProjectNumber"

Write-Step "GitHub CLI authentication"
$auth = Run-Gh -GhArgs @("auth", "status")
if ($auth.Code -eq 0) {
  Pass "gh is authenticated."
  if ($auth.Output -match "project") { Pass "Token includes project scope." } else { Warn "Token scopes did not visibly include project." }
  if ($auth.Output -match "repo") { Pass "Token includes repo scope." } else { Warn "Token scopes did not visibly include repo." }
} else {
  Fail "gh auth status failed. Run: gh auth login -h github.com -p https -s repo,workflow,read:org,project"
}

Write-Step "Repository access"
$repoView = Run-Gh -GhArgs @("repo", "view", $FullRepo, "--json", "nameWithOwner", "--jq", ".nameWithOwner")
if ($repoView.Code -eq 0 -and $repoView.Output.Trim() -eq $FullRepo) {
  Pass "Repository is accessible through gh."
} else {
  Fail "Repository lookup failed for $FullRepo."
}

Write-Step "Project board access"
$projectList = Run-Gh -GhArgs @("project", "list", "--owner", $Owner, "--format", "json")
if ($projectList.Code -eq 0 -and $projectList.Output -match "`"number`"\s*:\s*$ProjectNumber") {
  Pass "Project $ProjectNumber is visible for $Owner."
} elseif ($projectList.Code -eq 0) {
  Warn "Project list succeeded, but project $ProjectNumber was not found in the first page."
} else {
  Fail "Project list failed. Confirm gh auth has project scope and the owner is correct."
}

$items = Run-Gh -GhArgs @("project", "item-list", "$ProjectNumber", "--owner", $Owner, "--format", "json", "--limit", "10")
if ($items.Code -eq 0) {
  Pass "Project item-list works."
} else {
  Fail "Project item-list failed. This usually means missing project scope, wrong owner, or wrong project number."
}

Write-Step "Actions secret and variable names"
$secrets = Run-Gh -GhArgs @("secret", "list", "--repo", $FullRepo)
if ($secrets.Code -eq 0 -and $secrets.Output -match "(?m)^PROJECT_TOKEN\s") {
  Pass "Repository secret PROJECT_TOKEN exists."
} elseif ($secrets.Code -eq 0 -and $secrets.Output -match "(?m)^PAT\s") {
  Fail "Found PAT, but workflows expect PROJECT_TOKEN. Add it with: gh secret set PROJECT_TOKEN --repo $FullRepo"
} else {
  Fail "PROJECT_TOKEN was not found. Add it with: gh secret set PROJECT_TOKEN --repo $FullRepo"
}

$variables = Run-Gh -GhArgs @("variable", "list", "--repo", $FullRepo)
if ($variables.Code -eq 0 -and $variables.Output -match "(?m)^PROJECT_NUMBER\s+$ProjectNumber\s") {
  Pass "Repository variable PROJECT_NUMBER is set to $ProjectNumber."
} elseif ($variables.Code -eq 0 -and $variables.Output -match "(?m)^PROJECT_NUMBER\s") {
  Warn "PROJECT_NUMBER exists, but does not appear to be $ProjectNumber."
} else {
  Warn "PROJECT_NUMBER is not set. Workflows default to 1, but set it explicitly with: gh variable set PROJECT_NUMBER --repo $FullRepo --body `"$ProjectNumber`""
}

Write-Step "Workflow files"
$expectedWorkflows = @(
  ".github/workflows/auto-add-to-project.yml",
  ".github/workflows/auto-status.yml",
  ".github/workflows/board-commands.yml",
  ".github/workflows/pi-report.yml",
  ".github/workflows/template-sanity-check.yml"
)

foreach ($workflow in $expectedWorkflows) {
  if (Test-Path $workflow) {
    Pass "$workflow exists."
  } else {
    Fail "$workflow is missing."
  }
}

if ($CreateTestIssue) {
  Write-Step "End-to-end auto-add test"
  $title = "Test: AgentArmy onboarding sanity check $(Get-Date -Format yyyyMMdd-HHmmss)"
  $body = "Temporary issue created by scripts/onboarding-check.ps1 to verify PROJECT_TOKEN and GitHub Projects auto-add. Safe to close."
  $issue = Run-Gh -GhArgs @("issue", "create", "--repo", $FullRepo, "--title", $title, "--body", $body)
  if ($issue.Code -ne 0) {
    Fail "Could not create test issue. PROJECT_TOKEN may still work in Actions, but local gh needs repo access for this optional test."
  } else {
    $issueUrl = $issue.Output.Trim()
    Pass "Created temporary issue: $issueUrl"
    Start-Sleep -Seconds 10
    $runs = Run-Gh -GhArgs @("run", "list", "--repo", $FullRepo, "--workflow", "Auto-add to project", "--limit", "1")
    if ($runs.Code -eq 0 -and $runs.Output -match "success") {
      Pass "Latest Auto-add to project workflow run succeeded."
    } else {
      Warn "Could not confirm latest auto-add workflow success. Check GitHub Actions run history."
    }
    $issueNumber = ($issueUrl -split "/")[-1]
    $boardAfter = Run-Gh -GhArgs @("project", "item-list", "$ProjectNumber", "--owner", $Owner, "--format", "json", "--limit", "100")
    if ($boardAfter.Code -eq 0 -and $boardAfter.Output -match "`"number`"\s*:\s*$issueNumber") {
      Pass "Temporary issue appeared on Project $ProjectNumber."
    } else {
      Fail "Temporary issue was not found on Project $ProjectNumber."
    }
    $close = Run-Gh -GhArgs @("issue", "close", $issueNumber, "--repo", $FullRepo, "--comment", "Onboarding sanity check complete; closing temporary verification issue.")
    if ($close.Code -eq 0) {
      Pass "Closed temporary issue #$issueNumber."
    } else {
      Warn "Could not close temporary issue #$issueNumber."
    }
  }
}

Write-Step "Result"
if ($Failures.Count -eq 0) {
  Pass "AgentArmy onboarding sanity check passed."
  exit 0
}

foreach ($failure in $Failures) {
  Write-Host "- $failure" -ForegroundColor Red
}
exit 1
