# Bước 3 — Chạy hàng loạt dựng dataset

## Thứ tự làm

### 3.1. Xác nhận T1018 và T1087.002 chạy offline (làm trước, bắt buộc)
Giống T1016/T1654, một số atomic cần tải công cụ ngoài (AdFind, PowerView) — sẽ fail
vì lab không có Internet. Ta chỉ dùng test chạy bằng lệnh built-in.

Trên WIN10-01 (PowerShell admin, elevated), xem danh sách và chạy thử từng test:
```
Invoke-AtomicTest T1018 -ShowDetailsBrief
Invoke-AtomicTest T1087.002 -ShowDetailsBrief
```
Với mỗi test KHÔNG cần tải ngoài (net view, ping, net group, net user...), chạy thử:
```
Invoke-AtomicTest T1018 -TestNumbers <n> -GetPrereqs
Invoke-AtomicTest T1018 -TestNumbers <n>
```
Ghi lại các số test chạy OK (exit 0, không lỗi tải mạng). Gửi danh sách cho tôi,
HOẶC tự điền vào `Invoke-VTBatch.ps1` ở biến `$ttpTests`:
```
"T1018"     = @(1,2)       # cac so test da xac nhan chay offline
"T1087.002" = @(1,2)
```
T1018 thường dùng được: net view / ping / nltest / arp. T1087.002: net user/group /domain.

### 3.2. Lập lịch chạy dưới hai tài khoản (để account không thành nhãn)
Chạy hàng loạt dưới CẢ user01 và admin01, mỗi tài khoản một đợt, để admin01/user01
xuất hiện ở cả phía attack lẫn benign.

**Cách thủ công (đơn giản, kiểm soát tốt):** mở hai cửa sổ PowerShell.
- Cửa sổ 1 — đăng nhập/elevated là **user01**:
  ```
  cd C:\VT-Guard\orchestrator
  .\Invoke-VTBatch.ps1 -Count 30 -HostName WIN10-01 -User "VTLAB\user01" -UserRole standard
  ```
- Cửa sổ 2 — đăng nhập/elevated là **admin01**:
  ```
  .\Invoke-VTBatch.ps1 -Count 30 -HostName WIN10-01 -User "VTLAB\admin01" -UserRole admin
  ```
Chạy trên DC01 tương tự (đổi -HostName DC01) cho một phần phiên, để có telemetry cả hai host.

**Cách Task Scheduler (chạy qua đêm không cần ngồi canh):**
Tạo task chạy `powershell.exe -ExecutionPolicy Bypass -File C:\VT-Guard\orchestrator\Invoke-VTBatch.ps1 -Count 40 -HostName WIN10-01 -User "VTLAB\admin01" -UserRole admin`
- Run whether user is logged on or not; với admin01 chọn "Run with highest privileges" (để T1654 elevated).
- Lưu credential admin01 khi tạo task. Tôi sẽ đưa lệnh schtasks cụ thể khi bạn tới bước này.

Vì bạn chạy linh hoạt nhiều đêm, mỗi đêm ~30-40 phiên/tài khoản là vừa. Cộng dồn vài đêm
sẽ đạt mục tiêu ~160 attack / 260 benign / 120 hard-negative.

### 3.3. T1003.003 (NTDS) — thủ công, ít phiên
Chỉ trên DC01, mỗi phiên khôi phục snapshot BASELINE-CLEAN trước:
1. VMware: khôi phục snapshot DC01 -> khởi động -> chờ AD sẵn sàng.
2. PowerShell elevated là admin01:
   ```
   cd C:\VT-Guard\orchestrator
   .\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User "VTLAB\admin01" -UserRole admin `
     -Ttps T1003.003 -TestNumbers 3 -SnapshotBefore "BASELINE-CLEAN" -Tempo burst
   ```
   (Test 3 = NTDSUtil, khớp Volt Typhoon. Xác nhận T1003.003 -ShowDetailsBrief trước.)
3. Sau phiên: khôi phục lại snapshot. Làm ~10-15 phiên là đủ cho một TTP.
Xen kẽ vài phiên hard-negative trên DC01 (admin đọc log/kiểm kê tài khoản) để cân bằng.

### 3.4. Kéo log mỗi đợt về và xử lý
Sau mỗi đợt, trên VT-SIEM01:
```
~/vt-guard/data/raw/export_batch.sh 2026-10-13T14:00:00Z 2026-10-13T18:00:00Z batch01
```
(GTE/LTE là giờ UTC bao trùm đợt chạy.) Chép thư mục batch về host, cùng các manifest
trong C:\VT-Guard-runs, rồi chạy:
```
python src\normalize\normalize.py data\raw\batch01 data\interim\batch01.norm.jsonl
python src\label\label.py data\interim\batch01.norm.jsonl <thu_muc_manifest_cua_dot> data\processed\batch01.labeled.jsonl
```
Gửi tôi thống kê in ra (labeled/dropped mỗi phiên) để kiểm tra chất lượng trước khi gộp.

## Kiểm tra chất lượng sau mỗi đợt
- Mỗi phiên attack phải có labeled > 0 (nếu 0: atomic bị Defender chặn hoặc thiếu quyền).
- dropped_harness và dropped_orch > 0 là bình thường (chống rò r:ri đang chạy).
- Tỉ lệ phiên có ok=false thấp.
