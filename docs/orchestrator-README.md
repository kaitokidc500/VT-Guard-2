# VT-Guard — Hướng dẫn vận hành bộ điều phối (Bước 2)

Mọi thao tác chỉ chạy trong lab cách ly VMnet2. Thực thi kỹ thuật ATT&CK
được **uỷ quyền cho Atomic Red Team**; `Invoke-VTSession.ps1` chỉ điều phối,
định thời và ghi manifest. Không có lệnh tấn công trong repo.

## 1. Cài Atomic Red Team (một lần, trên WIN10-01 và DC01)
Chạy PowerShell Administrator. Theo tài liệu chính thức của Red Canary
(atomicredteam.io). Cài ở chế độ cho phép tải atomics:
- Cài module `invoke-atomicredteam` và thư mục `atomics`.
- Kiểm tra: `Invoke-AtomicTest T1016 -ShowDetailsBrief` phải liệt kê các test.

**Quan trọng:** Windows Defender sẽ chặn một số atomic. Trong lab cách ly,
thêm loại trừ cho thư mục atomics, HOẶC ghi nhận việc chặn vào manifest. Đừng
tắt Defender toàn cục nếu bạn muốn giữ telemetry thực tế — ghi chú rõ trong báo cáo.

## 2. Một tinh chỉnh audit cho T1003.003 (trên DC01)
Để bắt truy cập file NTDS, bật Object Access cho thư mục NTDS:
```
auditpol /set /subcategory:"File System" /success:enable /failure:enable
auditpol /set /subcategory:"Handle Manipulation" /success:enable
```
Thêm SACL cho `C:\Windows\NTDS` (Audit > Everyone > Read). Việc này tạo
Security 4663 khi NTDS.dit bị đọc — bằng chứng mạnh cho T1003.003.
Sysmon 1 (process create NTDSUtil/vssadmin) đã bắt sẵn, không cần đổi.

## 3. Kỷ luật snapshot (BẮT BUỘC với T1003.003)
Trước mỗi phiên NTDS:
1. VMware: khôi phục snapshot `BASELINE-CLEAN` cho DC01.
2. Khởi động DC01, chờ dịch vụ AD sẵn sàng, kiểm tra giờ UTC đồng bộ.
3. Chạy phiên với `-SnapshotBefore "BASELINE-CLEAN"`.
4. Sau phiên: khôi phục lại `BASELINE-CLEAN` trước phiên kế tiếp.
Các TTP Discovery khác (T1016/T1018/T1087.002/T1654) KHÔNG đổi trạng thái máy,
không cần khôi phục giữa các phiên.

## 4. Chạy một phiên

Phiên tấn công (vd T1016 + T1654, tempo chậm, trên WIN10-01):
```
.\Invoke-VTSession.ps1 -Class attack -HostName WIN10-01 -User "VTLAB\user01" `
  -UserRole standard -Ttps T1016,T1654 -TestNumbers 1,1 -Tempo low_and_slow -Variant mixed
```

Phiên NTDS (chỉ DC01, sau khi đã khôi phục snapshot):
```
.\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User "VTLAB\admin01" `
  -UserRole admin -Ttps T1003.003 -TestNumbers 3 -SnapshotBefore "BASELINE-CLEAN"
```

Phiên hard-negative (admin hợp lệ, cùng công cụ — tập test khó):
```
.\Invoke-VTSession.ps1 -Class hard_negative -HostName WIN10-01 -User "VTLAB\admin01" `
  -UserRole admin -BenignTasks network_check,log_review,user_inventory -Tempo burst
```

Xem trước không thực thi: thêm `-WhatIfOnly`.

## 5. Nguyên tắc chống rò rỉ nhãn (nhắc lại)
- Manifest ghi `exclude_pids` = PID orchestrator → Bước 4 loại event của nó.
- Attack và benign/hard-negative PHẢI dùng chung tập account (user01 + admin01)
  và chung tempo — xem `scenarios.json`. Nếu lệch, mô hình học account/tempo.
- Không commit manifest chứa đường dẫn nhạy cảm lên git (đã có .gitignore cho data/).

## 6. Ma trận đa dạng hoá & kế hoạch lấy mẫu
Xem `orchestrator/scenarios.json`. Mục tiêu tham khảo: 160 phiên attack,
260 benign, 120 hard-negative, mỗi phiên attack mang 1–5 TTP ngẫu nhiên.
Bước 3 sẽ tự động hoá việc rút scenario ngẫu nhiên và chạy qua đêm.
