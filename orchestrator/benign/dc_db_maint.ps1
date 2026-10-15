# Benign/hard-negative (CHI DC01): admin kiem tra tinh trang CSDL AD - CHI DOC, khong tao ban sao, khong dump.
# Hop le: kiem tra vi tri/dung luong file NTDS (ntdsutil files info), liet ke shadow copy (vssadmin list).
# Dung chung tool voi T1003.003. Moi cong cu goi qua "cmd.exe /c" de sinh tien trinh con (cmd -> tool).
$ErrorActionPreference = "SilentlyContinue"

if ($env:COMPUTERNAME -ne "DC01") { Write-Warning "dc_db_maint chi chay tren DC01"; return }

$cmdExe = Join-Path $env:SystemRoot "System32\cmd.exe"
function Invoke-Cmd([string]$line, [int]$timeoutSec = 90) {
  $p = Start-Process -FilePath $cmdExe -ArgumentList "/c $line >nul 2>&1" -NoNewWindow -PassThru
  if ($p -and -not $p.WaitForExit($timeoutSec * 1000)) { $p.Kill() }
  Start-Sleep -Milliseconds (Get-Random -Minimum 500 -Maximum 2000)
}

# ntdsutil o che do chi doc: activate instance -> files -> info -> thoat
Invoke-Cmd 'ntdsutil "activate instance ntds" files info quit quit'
Invoke-Cmd "vssadmin list shadows"
Invoke-Cmd "vssadmin list volumes"
if ((Get-Random -Maximum 2) -eq 1) { Invoke-Cmd "vssadmin list writers" }
