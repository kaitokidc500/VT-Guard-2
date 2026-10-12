# Benign/hard-negative: admin kiem ke tai khoan domain (trung cong cu T1087.002).
# Hop le: ra soat tai khoan dinh ky. Chay bang tai khoan admin trong lab.
net user /domain     | Out-Null
net group "Domain Admins" /domain 2>$null | Out-Null
whoami /groups       | Out-Null
