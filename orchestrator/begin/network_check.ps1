# Benign/hard-negative: admin kiem tra mang (dung CUNG cong cu T1016/T1018/T1049).
# Day la hoat dong quan tri hop le - muc tieu tao false-positive kho cho detector.
ipconfig /all        | Out-Null
route print          | Out-Null
arp -a               | Out-Null
netstat -ano         | Out-Null
Test-Connection -Count 1 -ComputerName DC01 -ErrorAction SilentlyContinue | Out-Null
