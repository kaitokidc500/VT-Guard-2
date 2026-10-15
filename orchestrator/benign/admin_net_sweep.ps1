# Benign/hard-negative: admin kiem tra ket noi mang & suc khoe domain (dung ping, nltest, net).
# Hoan toan hop le: troubleshooting mang thuong ngay. Dung chung tool voi T1018.
# Ban truoc dung Test-Connection (cmdlet, KHONG sinh ping.exe) nen ping.exe gan nhu chi xuat hien
# o phien tan cong. Ban nay goi moi cong cu qua "cmd.exe /c" de sinh tien trinh con (cmd -> tool).
$ErrorActionPreference = "SilentlyContinue"

$cmdExe = Join-Path $env:SystemRoot "System32\cmd.exe"
function Invoke-Cmd([string]$line, [int]$timeoutSec = 60) {
  $p = Start-Process -FilePath $cmdExe -ArgumentList "/c $line >nul 2>&1" -NoNewWindow -PassThru
  if ($p -and -not $p.WaitForExit($timeoutSec * 1000)) { $p.Kill() }
  Start-Sleep -Milliseconds (Get-Random -Minimum 300 -Maximum 1500)
}

$domain = "corp.vtlab.test"
# Kiem tra cac may trong dai quan tri (gateway, DC, server, workstation)
1..6 | ForEach-Object { Invoke-Cmd "ping -n 1 -w 500 10.20.30.$_" 15 }
Invoke-Cmd "nltest /dsgetdc:$domain"
Invoke-Cmd "nltest /sc_query:$domain"
Invoke-Cmd "net view \\DC01"
