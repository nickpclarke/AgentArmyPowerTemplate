# install-windows-task.ps1 — register (or remove) the AgentArmy health monitor
# as a Windows Scheduled Task so the PC is protected continuously, even when no
# Claude Code session is open. Runs the monitor every N minutes while you're
# logged on (Docker Desktop only runs while logged on anyway).
#
#   Install:   powershell -ExecutionPolicy Bypass -File tools\health\install-windows-task.ps1
#   Custom:    ... -IntervalMinutes 10 -RepoRoot C:\path\to\AgentArmy
#   Remove:    ... -Uninstall
#
# Run from a normal (non-elevated) PowerShell — the task runs as the current
# user, which is what gives the toast/webhook a session and reads the vhdx.

param(
  [int]$IntervalMinutes = 15,
  [string]$RepoRoot,
  [string]$TaskName = 'AgentArmy-HealthMonitor',
  [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

if ($Uninstall) {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task '$TaskName'."
  } else {
    Write-Host "No scheduled task '$TaskName' found."
  }
  return
}

# Resolve the repo root (default: two levels up from this script).
if (-not $RepoRoot) {
  $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
}
$monitor = Join-Path $RepoRoot 'tools\health\monitor.mjs'
if (-not (Test-Path $monitor)) { throw "monitor.mjs not found at $monitor — pass -RepoRoot." }

# Locate node.
$node = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $node) { throw 'node not found on PATH. Install Node.js (the repo uses 22.x) or add it to PATH.' }

Write-Host "node:    $node"
Write-Host "monitor: $monitor"
Write-Host "every:   $IntervalMinutes min"

$action = New-ScheduledTaskAction -Execute $node -Argument "`"$monitor`" --quiet" -WorkingDirectory $RepoRoot

# Repeat indefinitely from logon. AtLogOn + a repetition interval keeps it light
# and means the toast/webhook always has an interactive session to fire into.
$trigger = New-ScheduledTaskTrigger -AtLogOn
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
  -RepetitionDuration ([TimeSpan]::MaxValue)).Repetition

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
  -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
  -Settings $settings -Principal $principal `
  -Description 'AgentArmy WSL/Docker storage + health monitor (auto-prune on critical).' -Force | Out-Null

Write-Host ""
Write-Host "Registered '$TaskName'. It runs at logon and every $IntervalMinutes min."
Write-Host "Run now to verify:  Start-ScheduledTask -TaskName $TaskName"
Write-Host "Inspect:            Get-ScheduledTaskInfo -TaskName $TaskName"
Write-Host "Remove:             powershell -ExecutionPolicy Bypass -File tools\health\install-windows-task.ps1 -Uninstall"
