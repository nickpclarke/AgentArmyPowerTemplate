# probe-windows.ps1 - Windows-side data collector for the AgentArmy health monitor.
#
# Emits a single compressed JSON object on stdout describing:
#   - fixed drives (free / size / used%)         -> the thing that actually halts the PC
#   - WSL distros (state + ext4.vhdx size)        -> the files that silently grow on C:
#
# Designed to be piped to powershell.exe via `-Command -` from node, so it works
# identically when invoked from native Windows OR from inside WSL (interop). It
# never throws: every section is wrapped so a partial failure still yields JSON.
#
# Docker stats are NOT collected here - the docker CLI is cross-platform, so the
# node side queries `docker system df` / `docker ps` directly.

$ErrorActionPreference = 'SilentlyContinue'
$result = [ordered]@{ drives = @(); wsl = @(); errors = @() }

# ---- Fixed drives (DriveType 3 = local disk) -------------------------------
try {
  $result.drives = @(
    Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
      $sizeGB = if ($_.Size) { [math]::Round($_.Size / 1GB, 1) } else { 0 }
      $freeGB = if ($_.FreeSpace) { [math]::Round($_.FreeSpace / 1GB, 1) } else { 0 }
      $usedPct = if ($_.Size -gt 0) { [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 1) } else { 0 }
      [ordered]@{
        letter  = $_.DeviceID.TrimEnd(':')
        freeGB  = $freeGB
        sizeGB  = $sizeGB
        usedPct = $usedPct
      }
    }
  )
} catch {
  $result.errors += "drives: $($_.Exception.Message)"
}

# ---- WSL distros: state (from wsl -l -v) + vhdx size (from the Lxss registry)
# WSL_UTF8=1 makes wsl.exe emit clean UTF-8 instead of UTF-16-with-NULs.
try {
  $env:WSL_UTF8 = '1'
  $states = @{}
  $raw = & wsl.exe --list --verbose 2>$null
  foreach ($line in $raw) {
    $t = $line.Trim()
    if (-not $t -or $t -match '^NAME\s') { continue }
    $t = $t -replace '^\*\s*', ''           # drop the default-distro marker
    $cols = $t -split '\s+'
    if ($cols.Count -ge 2) { $states[$cols[0]] = $cols[1] }
  }

  # Registry holds each distro's on-disk BasePath -> locate its ext4.vhdx.
  $lxss = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
  $distros = @()
  Get-ChildItem $lxss 2>$null | ForEach-Object {
    $p = Get-ItemProperty $_.PSPath
    if (-not $p.DistributionName) { return }
    $base = ($p.BasePath -replace '^\\\\\?\\', '')   # strip the \\?\ long-path prefix
    $vhdx = $null
    foreach ($cand in @((Join-Path $base 'ext4.vhdx'), (Join-Path $base 'LocalState\ext4.vhdx'))) {
      if (Test-Path $cand) { $vhdx = $cand; break }
    }
    $vhdxGB = if ($vhdx) { [math]::Round((Get-Item $vhdx).Length / 1GB, 1) } else { 0 }
    $distros += [ordered]@{
      distro   = $p.DistributionName
      state    = if ($states.ContainsKey($p.DistributionName)) { $states[$p.DistributionName] } else { 'Unknown' }
      vhdxPath = $vhdx
      vhdxGB   = $vhdxGB
    }
  }
  $result.wsl = @($distros)
} catch {
  $result.errors += "wsl: $($_.Exception.Message)"
}

$result | ConvertTo-Json -Depth 5 -Compress
