# Benign/hard-negative (DC01 va WIN10-01): admin chan doan mang/DNS thuong ngay.
# Hoan toan hop le: chi lenh DOC/HIEN THI (show, /all, -n, -c), khong thay doi cau hinh.
# Dung chung cong cu voi T1016/T1018 (nslookup, nbtstat, netsh, ipconfig) de pha duong tat theo ten tien trinh.
# Moi cong cu duoc goi qua "cmd.exe /c" de sinh tien trinh con giong cach atomic chay (cmd -> tool).
$ErrorActionPreference = "SilentlyContinue"

$cmdExe = Join-Path $env:SystemRoot "System32\cmd.exe"
function Invoke-Cmd([string]$line, [int]$timeoutSec = 60) {
  # Start-Process truyen nguyen chuoi tham so cho cmd.exe (tranh PowerShell 5.1 lam hong dau nhay)
  $p = Start-Process -FilePath $cmdExe -ArgumentList "/c $line >nul 2>&1" -NoNewWindow -PassThru
  if ($p -and -not $p.WaitForExit($timeoutSec * 1000)) { $p.Kill() }
  Start-Sleep -Milliseconds (Get-Random -Minimum 300 -Maximum 1500)
}

$domain = "corp.vtlab.test"
$lines = @(
  "ipconfig /all",
  "ipconfig /displaydns",
  "nslookup $domain",
  "nslookup -type=SRV _ldap._tcp.dc._msdcs.$domain",
  "nslookup DC01.$domain",
  "nbtstat -n",
  "nbtstat -c",
  "netsh interface show interface",
  "netsh interface ipv4 show addresses",
  "netsh interface ipv4 show dnsservers",
  "netsh advfirewall show currentprofile",
  "netsh interface portproxy show all"
)
# Moi phien chay mot tap con ngau nhien, thu tu xao tron (giong bien the cua phien tan cong)
$n = Get-Random -Minimum 5 -Maximum ($lines.Count + 1)
foreach ($l in ($lines | Get-Random -Count $n)) { Invoke-Cmd $l }
