# VT-Guard batch07 - hard-negative bo sung de pha duong tat theo ten tien trinh (dataset card muc 5b, 9).
# Moi phien = MOT benign task, class=hard_negative, goi Invoke-VTSession.ps1 (manifest + exclude_pids nhu cu).
#
# Ke hoach toan dot (30 phien):
#   dc_db_maint     12 phien, chi DC01
#   admin_net_sweep  8 phien, 4 DC01 + 4 WIN10-01
#   admin_net_diag  10 phien, 5 DC01 + 5 WIN10-01
#
# Hai che do:
#   -Mode Loop            : chay cac phien KHONG can snapshot cua host hien tai, thu tu ngau nhien, nghi giua phien.
#                           Tren DC01 gom ca (12 - DbMaintSnapshotCount) phien dc_db_maint khong khoi phuc snapshot.
#   -Mode DbMaintSnapshot : chay DUNG MOT phien dc_db_maint theo quy trinh nhu phien NTDS:
#                           chay phien -> scp manifest ra server -> nguoi van hanh khoi phuc snapshot DC01 trong VMware.
#                           Muc dich: phien doi chung cho nhieu do khoi phuc snapshot (dong ho lech, dich vu khoi dong lai).
#                           Lap lai lenh nay DbMaintSnapshotCount lan (mac dinh 12), moi lan sau mot lan khoi phuc.
#
# Quy trinh van hanh cho DbMaintSnapshot nen GIONG phien NTDS (khoi phuc snapshot, dong bo gio, mo PowerShell admin
# bang runas) de nhieu snapshot cua hai lop tuong duong. Script nay KHONG tu dong bo gio: lenh w32tm chay tu
# orchestrator se thanh tien trinh con cua phien va bi gan nhan nham thanh hanh vi hard_negative.
#
# Vi du:
#   DC01    : .\Invoke-Batch07.ps1 -HostName DC01 -Mode Loop
#   WIN10-01: .\Invoke-Batch07.ps1 -HostName WIN10-01 -Mode Loop
#   DC01    : .\Invoke-Batch07.ps1 -HostName DC01 -Mode DbMaintSnapshot     (x12, moi lan sau khi khoi phuc snapshot)

[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet("DC01","WIN10-01")][string]$HostName,
  [ValidateSet("Loop","DbMaintSnapshot")][string]$Mode = "Loop",
  [string]$User = "VTLAB\admin01",
  [ValidateSet("standard","admin")][string]$UserRole = "admin",
  [ValidateRange(0,12)][int]$DbMaintSnapshotCount = 12,
  [ValidateSet("burst","low_and_slow")][string]$Tempo = "burst",
  [string]$OrchestratorDir = $PSScriptRoot,
  [string]$OutDir = "C:\VT-Guard-runs",
  [string]$SnapshotName = "DC01-CLEAN-ART",
  [string]$RemoteTarget = "vt_admin@10.20.30.10",
  [string]$RemoteDir = "/home/vt_admin/vt-guard/manifests/batch07",
  [int]$MinGapSec = 25, [int]$MaxGapSec = 70,
  [int]$Seed = 0,
  [switch]$WhatIfOnly
)
$ErrorActionPreference = "Stop"
if ($env:COMPUTERNAME -ne $HostName) { throw "Dang o $env:COMPUTERNAME nhung -HostName $HostName." }
$sv = Join-Path $OrchestratorDir "Invoke-VTSession.ps1"
if (-not (Test-Path $sv)) { throw "Khong thay $sv" }
foreach ($t in "dc_db_maint","admin_net_sweep","admin_net_diag") {
  if (-not (Test-Path (Join-Path $OrchestratorDir "benign\$t.ps1"))) { throw "Khong thay benign\$t.ps1" }
}
if ($Seed) { $rng = [Random]::new($Seed) } else { $rng = [Random]::new() }

function Invoke-OneSession([string]$task, [string]$snapshot = "") {
  Write-Host "[batch07] $HostName hard_negative task=$task tempo=$Tempo snapshot=$snapshot"
  if ($WhatIfOnly) { return $null }
  $before = Get-Date
  $sp = @{ Class = "hard_negative"; HostName = $HostName; User = $User; UserRole = $UserRole
             BenignTasks = @($task); Tempo = $Tempo; Variant = "cmd"; OutDir = $OutDir }
  if ($snapshot) { $sp.SnapshotBefore = $snapshot }
  & $sv @sp | Out-Null
  # manifest moi nhat sinh ra sau thoi diem bat dau phien
  Get-ChildItem (Join-Path $OutDir "*.manifest.json") | Where-Object { $_.LastWriteTime -ge $before } |
    Sort-Object LastWriteTime | Select-Object -Last 1
}

if ($Mode -eq "DbMaintSnapshot") {
  if ($HostName -ne "DC01") { throw "DbMaintSnapshot chi chay tren DC01." }
  if ($DbMaintSnapshotCount -eq 0) { throw "DbMaintSnapshotCount = 0: khong co phien snapshot nao can chay." }
  $m = Invoke-OneSession "dc_db_maint" $SnapshotName
  if ($WhatIfOnly) { Write-Host "[WhatIf] se scp manifest -> ${RemoteTarget}:$RemoteDir/"; return }
  if (-not $m) { throw "Khong tim thay manifest vua tao trong $OutDir" }
  # Dua manifest ra ngoai DC truoc khi khoi phuc snapshot (khoi phuc se xoa file tren DC)
  scp $m.FullName "${RemoteTarget}:$RemoteDir/"
  if ($LASTEXITCODE -ne 0) { throw "scp that bai ($LASTEXITCODE). KHONG khoi phuc snapshot truoc khi chep duoc manifest." }
  Write-Host ""
  Write-Host "=== XONG PHIEN dc_db_maint ($($m.BaseName)). Manifest da luu ngoai DC. ==="
  Write-Host "=== BUOC TIEP: trong VMware, KHOI PHUC snapshot '$SnapshotName' cho DC01 truoc phien sau. ==="
  Write-Host "=== Kiem tra so phien da co tren server: ls $RemoteDir/*-dc01-h.manifest.json (can $DbMaintSnapshotCount) ==="
  return
}

# ---- Mode Loop ----
$plan = @()
if ($HostName -eq "DC01") {
  $plan += @("dc_db_maint") * (12 - $DbMaintSnapshotCount)
  $plan += @("admin_net_sweep") * 4
  $plan += @("admin_net_diag") * 5
} else {
  $plan += @("admin_net_sweep") * 4
  $plan += @("admin_net_diag") * 5
}
$plan = @($plan | Sort-Object { $rng.Next() })
Write-Host "=== batch07 Loop: $($plan.Count) phien tren $HostName ($($plan -join ', ')) ==="
for ($i = 0; $i -lt $plan.Count; $i++) {
  Write-Host "[$($i+1)/$($plan.Count)]"
  try { Invoke-OneSession $plan[$i] | Out-Null } catch { Write-Warning "Phien $($i+1) loi: $_" }
  if ($i -lt $plan.Count - 1 -and -not $WhatIfOnly) { Start-Sleep -Seconds $rng.Next($MinGapSec, $MaxGapSec) }
}
Write-Host "=== Xong. Manifest o $OutDir -> chep ve manifests/batch07/ ==="
