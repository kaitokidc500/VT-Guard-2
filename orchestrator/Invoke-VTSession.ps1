# .SYNOPSIS
#   VT-Guard orchestrator - dieu phoi MOT phien va ghi manifest.
#   Thuc thi ky thuat ATT&CK duoc UY QUYEN cho Atomic Red Team (Invoke-AtomicTest).
#   Script nay KHONG chua lenh tan cong; no chi dieu phoi, dinh thoi, va ghi su that de gan nhan.
#
# .DESCRIPTION
#   - attack        : goi Invoke-AtomicTest theo <technique>/<test-number> lay tu scenarios.json
#   - benign        : goi script trong .\benign\ (hoat dong quan tri hop le)
#   - hard_negative : benign nhung dung DUNG cong cu cua 5 TTP (tap test kho nhat)
#   Ghi manifest JSON (theo manifests/manifest.schema.json) vao -OutDir.
#   Ghi exclude_pids = PID cua chinh orchestrator -> Buoc 4 loai cac event nay (chong ro ri nhan).
#
# .NOTES
#   Yeu cau voi attack: da cai Invoke-AtomicTest (module Atomic Red Team).
#   Voi T1003.003: PHAI chay sau khi da khoi phuc snapshot BASELINE-CLEAN tren DC01 (xem README).
[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet("attack","benign","hard_negative")] [string]$Class,
  [Parameter(Mandatory)][ValidateSet("DC01","WIN10-01")]                [string]$HostName,
  [Parameter(Mandatory)][string]$User,          # vd VTLAB\user01
  [ValidateSet("standard","admin")][string]$UserRole = "standard",
  [string[]]$Ttps = @(),                         # vd @("T1016","T1654")
  [int[]]$TestNumbers = @(),                      # tuong ung tung TTP (attack)
  [string[]]$BenignTasks = @(),                   # ten script benign (benign/hard_negative)
  [ValidateSet("burst","low_and_slow")][string]$Tempo = "burst",
  [ValidateSet("cmd","powershell","wmic","mixed")][string]$Variant = "mixed",
  [string]$SnapshotBefore = "",
  [string]$OutDir = "C:\VT-Guard-runs",
  [switch]$WhatIfOnly                             # in ke hoach, khong thuc thi
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$gap = @{ burst = 2..10; low_and_slow = 45..240 }[$Tempo]
$runId = "{0:yyyyMMdd-HHmmss}-{1}-{2}" -f (Get-Date).ToUniversalTime(), $HostName.ToLower(), ($Class.Substring(0,1))
$manifest = [ordered]@{
  run_id = $runId; class = $Class; host = $HostName; user = $User; user_role = $UserRole
  ttps = $Ttps; steps = @(); tempo = $Tempo; variant = $Variant
  snapshot_before = $SnapshotBefore
  exclude_pids = @($PID)                          # PID cua orchestrator
  tool_versions = @{ powershell = $PSVersionTable.PSVersion.ToString() }
  t_start = (Get-Date).ToUniversalTime().ToString("o")
}

# Chan an toan: T1003.003 chi tren DC01 va bat buoc co snapshot
if ($Ttps -contains "T1003.003") {
  if ($HostName -ne "DC01") { throw "T1003.003 chi chay tren DC01." }
  if (-not $SnapshotBefore) { throw "T1003.003 yeu cau -SnapshotBefore (ten snapshot da khoi phuc). Dung lai." }
}

function Invoke-Step($ttp, $source, [scriptblock]$action) {
  $t0 = (Get-Date).ToUniversalTime().ToString("o")
  Write-Host "[$runId] step: $source"
  if (-not $WhatIfOnly) { & $action }
  $t1 = (Get-Date).ToUniversalTime().ToString("o")
  $manifest.steps += [ordered]@{ ttp = $ttp; source = $source; t0 = $t0; t1 = $t1 }
  Start-Sleep -Seconds (Get-Random -InputObject $gap)
}

try {
  if ($Class -eq "attack") {
    for ($i=0; $i -lt $Ttps.Count; $i++) {
      $ttp = $Ttps[$i]; $tn = if ($i -lt $TestNumbers.Count) { $TestNumbers[$i] } else { 1 }
      # UY QUYEN thuc thi cho Atomic Red Team. Khong co lenh tan cong trong file nay.
      Invoke-Step $ttp "atomic:$ttp/$tn" {
        Invoke-AtomicTest $ttp -TestNumbers $tn -Confirm:$false
      }
    }
  }
  else {
    # benign / hard_negative: goi script trong .\benign\
    foreach ($task in $BenignTasks) {
      $script = Join-Path $PSScriptRoot "benign\$task.ps1"
      if (-not (Test-Path $script)) { throw "Khong thay benign task: $script" }
      Invoke-Step "" "benign:$task" { & $script }
    }
  }
}
finally {
  $manifest.t_end = (Get-Date).ToUniversalTime().ToString("o")
  $path = Join-Path $OutDir "$runId.manifest.json"
  $manifest | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $path
  Write-Host "Manifest -> $path"
}
