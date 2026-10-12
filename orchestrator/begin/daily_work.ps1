# Benign thuan: hoat dong van phong, KHONG trung cong cu discovery.
# Tao nhieu nen "binh thuong" de can bang dataset.
Get-ChildItem $env:USERPROFILE\Documents -Recurse -ErrorAction SilentlyContinue | Out-Null
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 | Out-Null
Get-Date | Out-Null
