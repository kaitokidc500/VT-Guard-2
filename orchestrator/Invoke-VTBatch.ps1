# VT-Guard batch runner - chay NHIEU phien ngau nhien trong mot dot (overnight).
# Chay DUOI danh tinh cua task/cua so hien tai (user01 hoac admin01). Chi chon scenario hop le voi role.
# T1003.003 (NTDS) KHONG nam o day - lam thu cong rieng.
# Moi phien goi Invoke-VTSession.ps1; giua cac phien nghi ngau nhien de tach cua so.

[CmdletBinding()]
param(
  [Parameter(Mandatory)][int]$Count,
  [Parameter(Mandatory)][ValidateSet("DC01","WIN10-01")][string]$HostName,
  [Parameter(Mandatory)][string]$User,
  [Parameter(Mandatory)][ValidateSet("standard","admin")][string]$UserRole,
  [string]$OrchestratorDir = "C:\VT-Guard\orchestrator",
  [string]$AtomicsPath = "C:\AtomicRedTeam\atomics",
  [int]$MinGapSec = 20, [int]$MaxGapSec = 90,
  [int]$Seed = 0
)
$ErrorActionPreference = "Stop"
if ($Seed) { $rng = [Random]::new($Seed) } else { $rng = [Random]::new() }
function Pick($arr) { $arr[$rng.Next(0,$arr.Count)] }
function PickN($arr,$n) { $arr | Sort-Object { $rng.Next() } | Select-Object -First $n }

# --- Khong gian scenario theo role (chi test KHONG can tai cong cu ngoai) ---
# Cap nhat cac so test o day SAU KHI ban xac nhan chung chay offline (xem README buoc 3).
$ttpTests = @{
  "T1016"     = @(1,9)         # ipconfig/netsh/arp...; nslookup
  "T1018"     = @(3,5,21)    # nltest; ping sweep; arp; net group Domain Controller
  "T1087.002" = @(1,9,12)      # net user /domain; Domain Admin details; ADSISearcher
  "T1654"     = @(1,2)         # Get-EventLog; WevtUtil (can admin+elevated)
}
$ttpByRole = @{
  standard = @("T1016","T1018","T1087.002")
  admin    = @("T1016","T1018","T1087.002","T1654")
}
$benignByRole = @{
  standard = @("daily_work","network_check")
  admin    = @("daily_work","network_check","log_review","user_inventory")
}
$hardNegByRole = @{
  standard = @("network_check")
  admin    = @("network_check","log_review","user_inventory")
}
# Loai TTP chua co test kha dung
$avail = $ttpByRole[$UserRole] | Where-Object { $ttpTests[$_].Count -gt 0 -and ($_ -ne "T1654" -or $UserRole -eq "admin") }

$tempos  = @("burst","low_and_slow")
$variants= @("cmd","powershell","wmic","mixed")
# Ty le lop: attack 35%, benign 40%, hard_negative 25%
function PickClass { $x=$rng.NextDouble(); if($x -lt 0.35){"attack"}elseif($x -lt 0.75){"benign"}else{"hard_negative"} }

$sv = Join-Path $OrchestratorDir "Invoke-VTSession.ps1"
if (-not (Test-Path $sv)) { throw "Khong thay $sv" }

Write-Host "=== VT-Batch: $Count phien, host=$HostName, user=$User ($UserRole) ==="
for ($i=1; $i -le $Count; $i++) {
  $cls = PickClass
  $tempo = Pick $tempos
  try {
    if ($cls -eq "attack") {
      if ($avail.Count -eq 0) { Write-Warning "Khong co TTP kha dung cho role $UserRole, bo qua"; continue }
      $k = $rng.Next(1, [Math]::Min(4,$avail.Count)+1)
      $ttps = @(PickN $avail $k)
      $tn = foreach ($t in $ttps) { Pick $ttpTests[$t] }
      $variant = Pick $variants
      Write-Host "[$i/$Count] attack ttps=$($ttps -join ',') tests=$($tn -join ',') tempo=$tempo"
      & $sv -Class attack -HostName $HostName -User $User -UserRole $UserRole `
            -Ttps $ttps -TestNumbers $tn -Tempo $tempo -Variant $variant -AtomicsPath $AtomicsPath
    }
    elseif ($cls -eq "benign") {
      $tasks = @(PickN $benignByRole[$UserRole] (Pick @(1,2)))
      Write-Host "[$i/$Count] benign tasks=$($tasks -join ',') tempo=$tempo"
      & $sv -Class benign -HostName $HostName -User $User -UserRole $UserRole `
            -BenignTasks $tasks -Tempo $tempo
    }
    else {
      $tasks = @(PickN $hardNegByRole[$UserRole] (Pick @(1,2)))
      Write-Host "[$i/$Count] hard_negative tasks=$($tasks -join ',') tempo=$tempo"
      & $sv -Class hard_negative -HostName $HostName -User $User -UserRole $UserRole `
            -BenignTasks $tasks -Tempo $tempo
    }
  } catch { Write-Warning "Phien $i loi: $_" }
  if ($i -lt $Count) { Start-Sleep -Seconds $rng.Next($MinGapSec,$MaxGapSec) }
}
Write-Host "=== Xong $Count phien. Manifest o C:\VT-Guard-runs ==="
