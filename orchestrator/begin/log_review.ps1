# Benign/hard-negative: admin xem lai log dang nhap gan day (trung cong cu voi T1654).
# Hoan toan hop le: kiem tra ai da dang nhap de dieu tra su co thuong ngay.
Get-EventLog -LogName Security -InstanceId 4624 -Newest 20 -ErrorAction SilentlyContinue |
  Select-Object TimeGenerated, Message | Out-Null
