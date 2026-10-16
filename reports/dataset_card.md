# VT-Guard — Dataset card (dataset-v1.2, bản đóng băng)

Sinh tự động bởi `src/dataset/card.py` lúc 2026-10-16T21:25:53+07:00. Số liệu chi tiết: `reports/dataset_stats.json`.

> **Phiên bản `dataset-v1.2` — ĐÓNG BĂNG, thay thế dataset-v1.1 (và v1.0).** Split (`data/processed/splits/*.jsonl`), `vocab.json` và checksum ở mục 10 là cố định: mọi mô hình ở Bước 5–8 phải dùng đúng các file này; trước khi chạy, so sha256 với mục 10. v1.1 trung hoà dấu vết bộ sinh dữ liệu (mục 7a); v1.2 gán event 4688 theo tiến trình được tạo (mục 7b). Thành viên các tập giữ nguyên từ v1.0, v1.2 thêm đúng 1 phiên được khôi phục vào Train. Muốn đổi dữ liệu → tạo phiên bản mới, không sửa tại chỗ.

## 1. Mục đích
Phát hiện hành vi APT kiểu **Volt Typhoon** (living-off-the-land) trên log Windows thu bằng Wazuh. Đơn vị phát hiện là **cửa sổ phiên** (chuỗi tối đa 64 event), nhãn **đa nhãn** ở mức cửa sổ: `window_malicious` (nhị phân) và `window_ttps` (tập TTP).

## 2. Nguồn gốc
- Hạ tầng: Wazuh agent trên **DC01** (domain controller) và **WIN10-01** (workstation) → Wazuh Indexer.
- Mô phỏng: Atomic Red Team qua orchestrator sinh phiên; mỗi phiên có một manifest (`manifests/<đợt>/`).
- Đợt dùng: batch01, batch02, batch03, batch04, batch05, batch06, batch07, ntds, ntds2, ntds2v. Bỏ: smoke6 (chạy thử, gán nhãn bằng labeler cũ).
  - `batch06`: 27 phiên hard-negative bổ sung (quét mạng quản trị bằng ping, kiểm tra log bằng wevtutil, bảo trì CSDL AD bằng ntdsutil…) để giảm đường tắt theo tên tiến trình.
  - `batch07`: 30 phiên hard-negative gọi công cụ qua `cmd.exe /c` (dc_db_maint 12 trên DC01 có khôi phục snapshot = phiên đối chứng `revert_control`; admin_net_sweep 8 với ping.exe thật; admin_net_diag 10 với nslookup/nbtstat/netsh/ipconfig).
  - `ntds2`: 15 phiên T1003.003 test 3 (`ntdsutil ifm`); `ntds2v`: 6 phiên T1003.003 test 1 (biến thể vssadmin/shadow copy) — giữ làm biến thể held-out.
- Manifest: 479 phiên — batch01 60, batch02 80, batch03 80, batch04 80, batch05 80, batch06 27, batch07 30, ntds 21, ntds2 15, ntds2v 6; theo lớp: attack 151, benign 164, hard_negative 164.
- Pipeline: `normalize.py` (v1) → `label.py` (labeler v8) → `merge.py` → `windows.py` → `featurize.py` (f3) → `split.py`. Seed cố định 1337.
- Event: đọc 423 597, giữ 62 917 (malicious 5 509, benign 57 408; trong đó nền 52 837). DC01 43 788 · WIN10-01 19 129.
- Event malicious theo TTP: T1003.003 373, T1016 3 432, T1018 3 745, T1087.002 3 458, T1654 2 652.
- Thời lượng log: **13.88 giờ** = tổng thời lượng phiên theo manifest (t_end − t_start, đồng hồ của orchestrator); theo lớp: attack 5.86 h, benign 4.8 h, hard_negative 3.22 h. Hợp các khung phiên theo host (không đếm trùng phiên chạy song song): WIN10-01 7.97 h, DC01 3.79 h. Đối chiếu: khoảng export theo giờ Wazuh (`ts`, đồng hồ manager) cộng theo file × host = 26.26 giờ, gồm cả thời gian nghỉ giữa phiên. Không dùng min/max `ts_system` vì sau khi khôi phục snapshot đồng hồ DC01 lệch (bản trước tính ra 21,1 giờ cho batch07|DC01).

## 3. Lớp và TTP
| TTP | Kỹ thuật |
|---|---|
| T1016 | System Network Configuration Discovery |
| T1018 | Remote System Discovery |
| T1087.002 | Account Discovery: Domain Account |
| T1654 | Log Enumeration |
| T1003.003 | OS Credential Dumping: NTDS |

Lớp phiên: `attack` (chạy TTP), `benign` (hoạt động người dùng/quản trị thường), `hard_negative` (hoạt động quản trị hợp lệ giống tấn công). Event nền (không thuộc cây tiến trình phiên nào) luôn là benign.

## 4. Cửa sổ
- Stream phiên = event cây tiến trình của phiên + event nền cùng host trong [t_start, t_end] (theo `ts_system`); không lấy event của phiên khác chạy song song.
- Cửa sổ trượt W=64, stride=32; tối đa K=8 cửa sổ/phiên (lấy mẫu phân tầng dương/âm, seed). 14 phiên bị chặn, 874 → 809 cửa sổ (272 dương, 537 âm).
- `window_malicious` = có ít nhất 1 event malicious; `window_ttps` = hợp TTP của event malicious; `window_class` = lớp phiên.
- **Phiên bị loại (20)**:

Mọi phiên bị loại đã được rà lại với labeler v8 (normalize v1): không phiên nào có thêm event cây phiên, và không phiên nào có event tạo tiến trình (EID1 hoặc 4688) con của orchestrator trong khung phiên. Lý do dưới đây theo đúng bằng chứng telemetry (không suy diễn "atomic không sinh tiến trình con"). Phiên attack/hard_negative bị loại hẳn, không coi là benign.

| Phiên | Lớp | Đợt | Task | Snapshot | Event cây | Event orchestrator | Tạo tiến trình con | Nền trong khung | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `20261015-075708-dc01-a` | attack | ntds2 | T1003.003/3 | DC01-CLEAN-ART | 0 | 0 | 0 | 0 | không có event nào trong khung phiên, kể cả event của orchestrator → mất telemetry (nghi agent hoặc đồng hồ sau khôi phục snapshot) |
| `20261014-041841-win10-01-b` | benign | batch01 | log_review | — | 0 | 18 | 0 | 0 | task chạy cmdlet ngay trong tiến trình orchestrator (log_review): orchestrator có 18 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-052317-win10-01-b` | benign | batch01 | daily_work | — | 0 | 22 | 0 | 0 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-070642-win10-01-b` | benign | batch02 | daily_work | — | 0 | 23 | 0 | 0 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 23 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-071529-win10-01-b` | benign | batch02 | daily_work | — | 0 | 23 | 0 | 0 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 23 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-073145-win10-01-b` | benign | batch02 | daily_work | — | 0 | 22 | 0 | 0 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-073716-dc01-b` | benign | batch02 | daily_work | — | 0 | 22 | 0 | 6 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-075105-win10-01-b` | benign | batch02 | daily_work | — | 0 | 22 | 0 | 0 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-103113-win10-01-b` | benign | batch03 | daily_work | — | 0 | 22 | 0 | 0 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-120322-win10-01-b` | benign | batch04 | daily_work | — | 0 | 22 | 0 | 1 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-123155-win10-01-b` | benign | batch04 | daily_work | — | 0 | 22 | 0 | 2 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-133343-win10-01-b` | benign | batch05 | daily_work | — | 0 | 39 | 0 | 1 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 39 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-133825-win10-01-b` | benign | batch05 | daily_work | — | 0 | 22 | 0 | 1 | task chạy cmdlet ngay trong tiến trình orchestrator (daily_work): orchestrator có 22 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688); không có event nền trong khung → stream rỗng |
| `20261014-073330-dc01-h` | hard_negative | batch02 | log_review | — | 0 | 18 | 0 | 100 | task chạy cmdlet ngay trong tiến trình orchestrator (log_review): orchestrator có 18 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688) |
| `20261014-093702-win10-01-h` | hard_negative | batch03 | log_review | — | 0 | 18 | 0 | 35 | task chạy cmdlet ngay trong tiến trình orchestrator (log_review): orchestrator có 18 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688) |
| `20261014-120938-win10-01-h` | hard_negative | batch04 | log_review | — | 0 | 18 | 0 | 15 | task chạy cmdlet ngay trong tiến trình orchestrator (log_review): orchestrator có 18 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688) |
| `20261014-122845-dc01-h` | hard_negative | batch04 | log_review | — | 0 | 18 | 0 | 6 | task chạy cmdlet ngay trong tiến trình orchestrator (log_review): orchestrator có 18 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688) |
| `20261014-133522-win10-01-h` | hard_negative | batch05 | log_review | — | 0 | 18 | 0 | 1 | task chạy cmdlet ngay trong tiến trình orchestrator (log_review): orchestrator có 18 event, không có event tạo tiến trình nào (cả EID1 lẫn 4688) |
| `20261015-130127-dc01-h` | hard_negative | batch07 | dc_db_maint | DC01-CLEAN-ART | 0 | 41 | 0 | 8 | orchestrator có 41 event nhưng không có event tạo tiến trình nào (cả EID1 lẫn 4688) trong khung phiên; không xác định được nguyên nhân (nghi lệch đồng hồ sau khôi phục snapshot) |
| `20261015-130245-dc01-h` | hard_negative | batch07 | dc_db_maint | DC01-CLEAN-ART | 0 | 0 | 0 | 0 | không có event nào trong khung phiên, kể cả event của orchestrator → mất telemetry (nghi agent hoặc đồng hồ sau khôi phục snapshot) |

- `revert_control` = phiên hard_negative chạy sau khi khôi phục snapshot (dc_db_maint batch07). Chỉ dùng cho card và kiểm tra #10, KHÔNG làm feature (nằm trong mẫu trường cấm của `featurize.py`).

## 5. Các tập (chia theo PHIÊN và NHÓM PHIÊN)

| Tập | Vai trò | Phiên | Cửa sổ | Dương | Tỉ lệ dương | DC01 / WIN10-01 | T1016 | T1018 | T1087.002 | T1654 | T1003.003 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Train | huấn luyện | 263 | 483 | 176 | 36.4% | 197 / 286 | 85 | 78 | 95 | 83 | 42 |
| T-clean | kiểm thử cùng phân phối | 52 | 89 | 42 | 47.2% | 26 / 63 | 21 | 23 | 24 | 17 | 12 |
| T-hard | đo false-positive trên quản trị hợp lệ | 61 | 88 | 0 | 0.0% | 47 / 41 | 0 | 0 | 0 | 0 | 0 |
| T-novel | holdout thời gian + biến thể (batch05 + ntds2v) | 83 | 149 | 54 | 36.2% | 59 / 90 | 37 | 36 | 33 | 16 | 6 |

Số phiên theo đợt trong từng tập:

| Tập | batch01 | batch02 | batch03 | batch04 | batch05 | batch06 | batch07 | ntds | ntds2 | ntds2v |
|---|---|---|---|---|---|---|---|---|---|---|
| Train | 45 | 53 | 50 | 63 |  | 12 | 13 | 15 | 12 |  |
| T-clean | 1 | 17 | 16 | 10 |  |  | 2 | 4 | 2 |  |
| T-hard | 12 | 4 | 12 | 3 |  | 15 | 13 | 2 |  |  |
| T-novel |  |  |  |  | 77 |  |  |  |  | 6 |

- **T-novel** = toàn bộ phiên batch05 + ntds2v: batch05 là holdout thời gian, ntds2v là biến thể T1003.003 (test 1) không có trong Train. **T-hard** chọn theo **chữ ký công cụ** của phiên hard_negative (tập image_name trong cây tiến trình, bỏ cmd/conhost/powershell; phiên revert_control là chữ ký riêng): mỗi chữ ký có ≥1 phiên vào T-hard và ≥50% vào Train (khi có ≥2 phiên), mục tiêu ~40%; chỉ nhóm thuần hard_negative mới vào được T-hard. batch07 không vào T-novel. Phần còn lại (gồm ntds2) chia **Train 80% / T-clean 20%** theo nhóm, phân tầng theo (lớp, host, chữ ký TTP).
- **Nhóm phiên**: các phiên cùng host chồng thời gian (kể cả bắc cầu) dùng chung event nền, nên cả nhóm vào cùng một tập.

Phân bổ hard_negative theo chữ ký công cụ (số phiên):

| Chữ ký | Tổng | Train | T-clean | T-hard | Điều kiện |
|---|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 58 | 29 | 6 | 23 | ĐẠT |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 14 | 8 | 0 | 6 | ĐẠT |
| `net.exe+net1.exe` | 13 | 7 | 1 | 5 | ĐẠT |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | 10 | 5 | 1 | 4 | ĐẠT |
| `net.exe+nltest.exe+ping.exe` | 8 | 4 | 1 | 3 | ĐẠT |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 7 | 4 | 0 | 3 | ĐẠT |
| `net.exe+net1.exe+vssadmin.exe` | 6 | 4 | 0 | 2 | ĐẠT |
| `net.exe+net1.exe+nltest.exe` | 5 | 3 | 0 | 2 | ĐẠT |
| `arp.exe+ipconfig.exe+net.exe+netstat.exe+nltest.exe+route.exe` | 3 | 2 | 0 | 1 | ĐẠT |
| `vssadmin.exe+wevtutil.exe` | 2 | 1 | 0 | 1 | ĐẠT |
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | 2 | 1 | 0 | 1 | ĐẠT |
| `nltest.exe+vssadmin.exe` | 2 | 1 | 0 | 1 | ĐẠT |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | 2 | 1 | 0 | 1 | ĐẠT |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | 2 | 1 | 0 | 1 | ĐẠT |
| `wevtutil.exe` | 2 | 1 | 0 | 1 | ĐẠT |
| `nltest.exe+wevtutil.exe` | 1 | 0 | 0 | 1 | ĐẠT |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 1 | 0 | 0 | 1 | ĐẠT |
| `net.exe+nltest.exe` | 1 | 0 | 0 | 1 | ĐẠT |
| `arp.exe+ipconfig.exe+netstat.exe+route.exe+wevtutil.exe` | 1 | 0 | 0 | 1 | ĐẠT |
| `ipconfig.exe+netsh.exe` | 1 | 0 | 0 | 1 | ĐẠT |
| `netsh.exe+nslookup.exe` | 1 | 0 | 0 | 1 | ĐẠT |

### 5a. Cửa sổ T1003.003 theo tập

| Tập | Phiên T1003.003 (theo đợt) | Cửa sổ dương T1003.003 | Âm trong phiên T1003.003 | Âm trên DC01 | Âm toàn tập |
|---|---|---|---|---|---|
| Train | 23 (ntds 11, ntds2 12) | 42 | 2 | 155 | 441 |
| T-clean | 6 (ntds 4, ntds2 2) | 12 | 0 | 14 | 77 |
| T-hard | 0 (—) | 0 | 0 | 47 | 88 |
| T-novel | 6 (ntds2v 6) | 6 | 0 | 53 | 143 |

### 5b. Coverage theo công cụ (số cửa sổ chứa tiến trình)

Mục tiêu: không công cụ nào chỉ xuất hiện ở phía dương, để mô hình không thể phát hiện chỉ nhờ tên tiến trình.

| image_name | Dương (tất cả) | Âm (tất cả) | Train dương / âm | Train % âm | T-clean dương / âm | T-hard âm | T-novel dương / âm | Cảnh báo |
|---|---|---|---|---|---|---|---|---|
| `ping.exe` | 16 | 16 | 16 / 9 | 36% | 0 / 2 | 5 | 0 / 0 |  |
| `wevtutil.exe` | 36 | 11 | 23 / 5 | 18% | 6 / 0 | 6 | 7 / 0 |  |
| `ntdsutil.exe` | 50 | 16 | 38 / 9 | 19% | 12 / 1 | 6 | 0 / 0 |  |
| `vssadmin.exe` | 9 | 29 | 3 / 18 | 86% | 0 / 1 | 10 | 6 / 0 |  |
| `nltest.exe` | 24 | 29 | 10 / 16 | 62% | 5 / 2 | 11 | 9 / 0 |  |
| `net.exe` | 91 | 109 | 58 / 62 | 52% | 14 / 8 | 22 | 19 / 17 |  |
| `net1.exe` | 90 | 90 | 57 / 52 | 48% | 14 / 6 | 15 | 19 / 17 |  |
| `ipconfig.exe` | 43 | 203 | 23 / 109 | 83% | 9 / 22 | 41 | 11 / 31 |  |
| `arp.exe` | 65 | 197 | 34 / 108 | 76% | 13 / 22 | 36 | 18 / 31 |  |
| `route.exe` | 0 | 190 | 0 / 103 | 100% | 0 / 22 | 34 | 0 / 31 |  |
| `netstat.exe` | 0 | 193 | 0 / 106 | 100% | 0 / 22 | 34 | 0 / 31 |  |
| `nslookup.exe` | 48 | 15 | 31 / 8 | 21% | 5 / 0 | 7 | 12 / 0 |  |
| `nbtstat.exe` | 44 | 12 | 24 / 6 | 20% | 9 / 0 | 6 | 11 / 0 |  |
| `netsh.exe` | 43 | 16 | 23 / 7 | 23% | 9 / 0 | 9 | 11 / 0 |  |
| `cmd.exe` | 225 | 48 | 140 / 26 | 16% | 35 / 3 | 19 | 50 / 0 |  |
| `powershell.exe` | 65 | 7 | 40 / 3 | 7% | 15 / 0 | 0 | 10 / 4 |  |
| `rundll32.exe` | 39 | 8 | 26 / 5 | 16% | 12 / 2 | 1 | 1 / 0 |  |
| `vssvc.exe` | 43 | 7 | 29 / 4 | 12% | 8 / 0 | 3 | 6 / 0 |  |

**Trước / sau batch07** — tỉ lệ dương = số cửa sổ dương chứa công cụ / tổng số cửa sổ chứa công cụ (trước = bản đóng băng commit d1db577, labeler v6; sau = bản này, labeler v7):

| image_name | Trước: dương / âm | Trước: tỉ lệ dương | Sau: dương / âm | Sau: tỉ lệ dương | Train âm trước → sau |
|---|---|---|---|---|---|
| `ping.exe` | 16 / 5 | 76% | 16 / 16 | 50% | 1 → 9 |
| `wevtutil.exe` | 38 / 11 | 78% | 36 / 11 | 77% | 4 → 5 |
| `ntdsutil.exe` | 51 / 5 | 91% | 50 / 16 | 76% | 0 → 9 |
| `vssadmin.exe` | 10 / 15 | 40% | 9 / 29 | 24% | 2 → 18 |
| `nltest.exe` | 23 / 19 | 55% | 24 / 29 | 45% | 6 → 16 |
| `net.exe` | 93 / 100 | 48% | 91 / 109 | 46% | 48 → 62 |
| `net1.exe` | 93 / 91 | 50% | 90 / 90 | 50% | 46 → 52 |
| `ipconfig.exe` | 40 / 187 | 18% | 43 / 203 | 18% | 103 → 109 |
| `arp.exe` | 65 / 196 | 25% | 65 / 197 | 25% | 105 → 108 |
| `route.exe` | 0 / 189 | 0% | 0 / 190 | 0% | 104 → 103 |
| `netstat.exe` | 0 / 193 | 0% | 0 / 193 | 0% | 106 → 106 |
| `nslookup.exe` | 48 / 2 | 96% | 48 / 15 | 76% | 1 → 8 |
| `nbtstat.exe` | 40 / 2 | 95% | 44 / 12 | 79% | 1 → 6 |
| `netsh.exe` | 42 / 2 | 96% | 43 / 16 | 73% | 1 → 7 |
| `cmd.exe` | 231 / 12 | 95% | 225 / 48 | 82% | 3 → 26 |
| `powershell.exe` | 63 / 9 | 88% | 65 / 7 | 90% | 1 → 3 |
| `rundll32.exe` | 36 / 8 | 82% | 39 / 8 | 83% | 6 → 5 |
| `vssvc.exe` | 39 / 6 | 87% | 43 / 7 | 86% | 3 → 4 |

Công cụ chỉ xuất hiện ở phía dương: **toàn bộ dữ liệu: không có**; riêng Train: không có.

## 6. Đặc trưng (mỗi event → 268 cột)
- 7 categorical → chỉ số embedding (`vocab.json`): `channel` (8), `event_id` (44), `image_name` (59), `parent_image_name` (14), `host_role` (5), `integrity_level` (8), `logon_type` (8). Id 0=`<pad>`, 1=`<unk>`, 2=`<none>`. Token vào vocab khi xuất hiện ở ≥2 phiên Train; `integrity_level` gộp SID về tên; `parent_image_name` ∈ {cmd.exe, powershell.exe} → `<launcher>` (gộp ngay trong windows.jsonl).
- `command_line` → 256 chiều: chuẩn hoá (f3: `canon_cmd` — basename file thực thi đầu dòng lệnh, bỏ chuyển hướng `>nul 2>&1 1> 2> >>`, `& && | ||` → khoảng trắng; rồi chữ thường, bỏ nháy, GUID/hex/số → ký hiệu), char n-gram 3–5, signed hashing md5, log1p, chuẩn L2. **Không lưu text thô.**
- 5 số: `dt_log` = log(1+Δt giây), `has_network`, `has_dns`, `is_powershell_channel`, `is_security_channel`.
- Vocab fit **chỉ trên Train**; tỉ lệ `<unk>` của `image_name`: fit 0.0%, t_novel 3.0%, other 0.0% (fit = Train, other = T-clean + T-hard).

## 7. Biện pháp chống rò rỉ
- **Trường không bao giờ làm feature**: `wazuh_rule_*` (chỉ cho baseline B0), `label_*`, `run_id`, `event_uid`, `process_guid`, `parent_process_guid`, `script_block_text`, `ps_payload`, đường dẫn đầy đủ `image`/`parent_image`, `n_events`, `tempo`, `variant`, `user_role`. `featurize.py` assert nguồn feature không khớp mẫu cấm; cửa sổ chỉ mang 11 trường nguồn được phép.
- **Cấu hình orchestrator `tempo`, `variant`, `user_role` (bổ sung ở Bước 5, B2)**: là tham số sinh phiên ghi trong manifest, KHÔNG quan sát được từ log; bản ghi cửa sổ/split mang chúng chỉ làm metadata. `variant` ≠ `mixed` chỉ xuất hiện ở phiên attack (0 phiên benign/hard-negative) nên dùng làm feature là rò nhãn trực tiếp — phát hiện khi dựng B2, đã loại trước khi chấm. Kiểm tra #2 nay gồm: ba trường không thuộc nguồn feature và không có trong event của cửa sổ; quét tĩnh mã `src/baselines`, `src/models` không đọc chúng (`evaluate.check_model_sources`, `evaluate()` dừng nếu vi phạm). B0/B1 chưa từng dùng ba trường này (chỉ đọc `events` của cửa sổ) nên không chạy lại. Dữ liệu và checksum không đổi.
- **Labeler v8** loại event công cụ thay vì gán nhãn (tổng trên 10 đợt): orchestrator 345 393, harness ART 2 195, upload manifest scp/ssh 316, console PowerShell người vận hành 2 393, mảnh vỡ 4103 mất PID 683.
  - v5: chặn upload manifest (v4 gán nhầm 72 event thành malicious T1003.003 ở ntds), console người vận hành, mảnh vỡ 4103.
  - v6: event không có `process_guid` chỉ được ghép vào tiến trình khi `ts_system` nằm trong vòng đời tiến trình (EID1→EID5). v5 ghép theo PID ±300 s bằng giờ Wazuh: sau khi khôi phục snapshot, đồng hồ DC01 lệch ~55 phút nên 204 event PowerShell (pid 1112, nạp module CIM) bị gán nhầm malicious T1003.003 vào phiên ntds2 `20261015-084208-dc01-a`, và 27 event PowerShell khác bị ghép nhầm vào cây scp. Đối chiếu từng event v5↔v6: chỉ 231 event này đổi, các đợt khác giữ nguyên.
  - v7: phiên = đúng khung [t_start, t_end] của manifest (±5 s) so bằng `ts_system`; con của orchestrator sinh ngoài mọi khung bị loại (`orch_child_outside`, 343 event). v4–v6 gán tiến trình vào phiên theo giờ Wazuh (trễ 40–60 s) và kéo khung tới lúc phiên kế tiếp bắt đầu, nên (1) 102 event của phiên attack bị gán nhãn benign/hard-negative của phiên chạy ngay sau (vd nbtstat/netsh/nslookup của T1016), (2) lệnh người vận hành gõ sau phiên trong cùng cửa sổ PowerShell (w32tm, VMwareToolboxCmd timesync, whoami) bị gán vào phiên (batch07 `20261015-122828-dc01-h`: 61 → 45 event). Đối chiếu v6↔v7: 400 event đổi trạng thái hoặc phiên.
  - v7 cũng nạp manifest của đợt bên cạnh khi khung phiên giao với khung các phiên của đợt đang gán nhãn (±10 phút): export cắt theo giờ Wazuh nên tiến trình của `20261015-084801-dc01-a` (ntds2v) nằm trong file ntds2; phiên này nay có 9 event và không còn bị loại.
- Khử trùng lặp theo `(host, channel, record_id, event_id, ts_system)`: khôi phục snapshot DC01 làm `record_id` quay lui, khoá chỉ có `record_id` sẽ xoá nhầm 13 729 event thật.
- Chia theo phiên và nhóm phiên: không `run_id`/session nào ở 2 tập, không cặp phiên Train/kiểm thử nào chồng thời gian trên cùng host.
- Vocab fit chỉ trên Train; T-novel thật sự chứa token chưa thấy.

### 7a. Rò rỉ dấu vết bộ sinh dữ liệu (scaffold) và cách xử lý (dataset-v1.1)
Ở Bước 5, B1 lộ ra rằng **cách khởi chạy công cụ** khác nhau giữa bộ sinh tấn công (Atomic Red Team) và script hard-negative tự viết (batch06/07) — không phải hành vi:
- **Đường dẫn cmd**: ART gọi `"cmd.exe" /c …` (283/283 dòng lệnh attack); script hard-negative gọi `"C:\Windows\System32\cmd.exe" /c …` (236/236).
- **Chuyển hướng**: chỉ hard-negative batch07 có `>nul 2>&1` (212/212).
- **conhost.exe**: ART chạy cmd trong console riêng → `cmd.exe→conhost.exe` ở 131/149 phiên attack, 0 phiên hard-negative (script dùng `Start-Process -NoNewWindow`).
- **Launcher cha**: công cụ trong script benign do `powershell.exe` sinh trực tiếp, trong ART do `cmd.exe` sinh (`powershell.exe→arp/netstat/route/ipconfig/net` chỉ ở hard-negative; `cmd.exe→arp`, `powershell.exe→powershell.exe` chỉ ở attack).

**Bằng chứng định lượng (mốc A, dataset-v1.0, B1 TF-IDF+LR):** bỏ dấu vết đường dẫn + chuyển hướng (B1-canon) gần như không đổi kết quả — chênh nằm trong khoảng tin cậy; mô hình vẫn tách được nhờ tín hiệu khác (đứng đầu là `img=conhost.exe`):

| Mô hình (v1.0) | T-clean F1 | T-hard FPR (FP, trong đó có cmd.exe) | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean/novel |
|---|---|---|---|---|---|
| b1_tfidf_lr | 1.000 [1.000, 1.000] | 0.023 [0.000, 0.058] (2, 2) | 0.922 [0.860, 0.968] | 0.834 [0.720, 0.954] | 0.825/0.697 |
| b1_raw_lr | 1.000 [1.000, 1.000] | 0.023 [0.000, 0.058] (2, 2) | 0.930 [0.875, 0.974] | 0.844 [0.722, 0.960] | 0.800/0.642 |
| b1_canon_lr | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] (0, 0) | 0.920 [0.860, 0.968] | 0.820 [0.698, 0.954] | 0.819/0.694 |

**Cách xử lý (áp ĐỒNG NHẤT mọi lớp, không xoá event hành vi):**
1. Loại hẳn mọi event `image_name` ∈ {conhost.exe} khi dựng stream (1 786 event: bg|benign 934, own|malicious 852).
2. Chuẩn hoá dòng lệnh (featurizer f2): basename file thực thi đầu dòng lệnh, bỏ chuyển hướng `>nul 2>&1 1> 2> >>` và toán tử `& && | ||`.
3. Bỏ đuôi `.exe` của mọi token file thực thi trong dòng lệnh (featurizer f3): công cụ do PowerShell gọi trực tiếp mang `arp.exe -a`, `net.exe …` còn ART gõ `arp -a`, `net …`. Chỉ đổi text dòng lệnh; `image_name` giữ nguyên. Số cửa sổ và thành viên các tập không đổi.
4. Gộp `parent_image_name` ∈ {cmd.exe, powershell.exe} → `<launcher>` ở mọi nơi dùng parent (windows.jsonl, vocab, cặp cha→con).
- **Giữ nguyên có chủ ý**: route/netstat/ipconfig/"Domain Admins" của kịch bản benign; tham số tấn công (arp, `%USERDNSDOMAIN%`, `-timeout`, truy vấn nslookup, adsisearcher, `ifm`); event ESENT/Directory Service do `ntdsutil ifm` sinh ra. Đây là hành vi hoặc lỗ hổng coverage — xử lý bằng ablation + hạn chế (mục 9), không xoá dữ liệu.

**Ảnh hưởng tới cửa sổ:** 809 → 809 cửa sổ (278 → 272 dương; trước khi chặn K: 880 → 874). Bỏ conhost làm stream ngắn lại; phiên có stream vượt 64 event chỉ nhờ event conhost giờ chỉ còn 1 cửa sổ (16 phiên mất đúng 1 cửa sổ). Cả 149 phiên attack vẫn có ≥1 cửa sổ dương. **Thành viên các tập giữ nguyên**: danh sách run_id mỗi tập và `assignment.json` trùng khớp v1.0 (split tất định theo seed + run_id).

| Tập | Phiên | Cửa sổ v1.0 → v1.1 | Dương v1.0 → v1.1 |
|---|---|---|---|
| Train | 263 | 479 → 483 | 178 → 176 |
| T-clean | 52 | 91 → 89 | 45 → 42 |
| T-hard | 61 | 87 → 88 | 0 → 0 |
| T-novel | 83 | 152 → 149 | 55 → 54 |

**Quét đặc trưng đơn lẻ trước/sau** (`src/dataset/scaffold_scan.py`): mức tách cao nhất 0.9422 (`image=conhost.exe`, v1.0) → 0.7346 (`image=cmd.exe`, v1.2; từ v1.2 quét thêm bigram event_id); số đặc trưng một-phía 68 → 77. Danh sách đầy đủ: `reports/step5/scaffold_scan_v1.0.json`, `scaffold_scan_v1.1.json`, `scaffold_scan_v1.2.json`.

### 7b. dataset-v1.2: gán event 4688 theo tiến trình được tạo
- **Lỗi gốc**: normalize v0 lấy `process_id` của Security 4688 = PID tiến trình **tạo ra** (`processId`), trong khi `image_name` là tiến trình **được tạo** (`newProcessName`). Labeler loại mọi event có `process_id` thuộc orchestrator ⇒ mất 4688 của mọi con trực tiếp của orchestrator. Script benign/hard-negative cũ gọi tool trực tiếp (mất 4688), ART và batch07 gọi qua `cmd` trung gian (giữ 4688) ⇒ tỉ lệ 4688/EID1 lệch theo lớp (dấu vết bộ sinh dạng mới, lộ ra ở trọng số `eid=5 eid=4688` của B1).
- **Sửa (normalize v1, labeler v8)**: 4688 có `process_id = newProcessId`, `parent_process_id = processId` (cùng ngữ nghĩa với Sysmon EID1); 4688 ghép vào tiến trình được tạo như mọi event không có guid. Quy tắc dự phòng v8: nếu tiến trình được tạo không khớp EID1 nào thì kế thừa theo tiến trình tạo — cha là orchestrator → như executor-root (phiên của orchestrator tại thời điểm tạo; harness/upload loại; ngoài mọi khung → `orch_child_outside`), cha khác → cùng cây với cha. Không loại 4688 ở bất kỳ lớp nào.
- **Đối chiếu từng event v7↔v8 trên 10 đợt**: chỉ event 4688 đổi (2394 event; event khác đổi: 0). Chuyển trạng thái: DROP:orchestrator -> SESS 1152, DROP:orchestrator -> DROP:art_harness 733, DROP:orchestrator -> MAL 286, DROP:orchestrator -> DROP:orch_child_outside 118, DROP:orchestrator -> DROP:harness_upload 46, BG -> DROP:orchestrator 40, DROP:operator_console -> DROP:orchestrator 14, DROP:operator_console -> BG 2, SESS -> DROP:orchestrator 1, BG -> DROP:operator_console 1, MAL -> DROP:orchestrator 1.
- **Phiên `20261014-164113-dc01-a` (ntds, T1003.003) bị loại sai ở v1.1** với lý do "atomic không sinh tiến trình con": thực ra có 4688 của `cmd.exe /c mkdir … & ntdsutil "ac i ntds" "ifm" …` nhưng thiếu Sysmon EID1; v8 khôi phục được.
- **Thành viên các tập cố định theo v1.1** (`split.py --pin-assignment`): mọi phiên cũ giữ nguyên tập; phiên mới xếp theo quy tắc nhóm phiên — `20261014-164113-dc01-a` → train (nhom don (khong chong thoi gian voi phien co tap), phan tang {('attack', 'DC01', 'attack:T1003.003'): 1}: T-clean hien co {('attack', 'DC01', 'attack:T1003.003'): 6} / muc tieu {('attack', 'DC01', 'attack:T1003.003'): 5.8} -> lech neu vao T-clean 1.2 vs Train 0.2 -> train).

| Tập | Phiên v1.1 → v1.2 | Cửa sổ v1.1 → v1.2 | Dương v1.1 → v1.2 | Event v1.1 → v1.2 |
|---|---|---|---|---|
| Train | 262 → 263 | 471 → 483 | 171 → 176 | 23 253 → 24 512 |
| T-clean | 52 → 52 | 87 → 89 | 41 → 42 | 4 270 → 4 496 |
| T-hard | 61 → 61 | 87 → 88 | 0 → 0 | 3 508 → 3 815 |
| T-novel | 83 → 83 | 148 → 149 | 53 → 54 | 7 083 → 7 313 |

Tổng: 793 → 809 cửa sổ, 265 → 272 dương; event giữ lại 61 490 → 62 917 (malicious 5 224 → 5 509). Số cửa sổ tăng vì event 4688 được giữ lại làm stream dài thêm.

## 8. Kiểm thử chấp nhận (chạy lại trên file split)

| # | Kiểm tra | Kết quả |
|---|---|---|
| 1 | Không session/run_id ở >1 tập | ĐẠT (0 vi phạm) |
| 2 | Không feature từ trường cấm (gồm `tempo`/`variant`/`user_role`; mã mô hình không đọc chúng); giá trị feature chỉ là số | ĐẠT |
| 3 | T-hard chỉ hard_negative; T-novel chỉ batch05 + ntds2v (và các đợt này không ở tập khác) | ĐẠT |
| 4 | Thống kê mỗi tập (cửa sổ, tỉ lệ dương, TTP, host) | xem mục 5 |
| 5 | Số cửa sổ dương hợp lý | ĐẠT: 272 ≤ 150×8; trung bình 1.81/phiên |
| 6 | Quét rò rỉ 200 cửa sổ dương (atomic/invoke-/T10xx/VT-Guard) + token vocab | ĐẠT (0 hit) |
| 7 | Không cặp phiên Train/kiểm thử chồng thời gian | ĐẠT |
| 8 | Vocab chỉ fit trên Train | ĐẠT |
| 9 | Train có cửa sổ âm ≥15% số cửa sổ chứa từng công cụ (ntdsutil, vssadmin, ping, wevtutil, nltest, nslookup, nbtstat, netsh, cmd) | ĐẠT |
| 10 | So phân bố (channel, event_id) của event nền: cửa sổ dương T1003.003 vs cửa sổ revert_control | đã chạy: khoảng cách biến phân toàn phần (TVD) = 0.482 (xem bảng dưới) |
| 11 | Không đặc trưng đơn lẻ nào tách attack/hard_negative với mức tách ≥ 0.98 (thường trực) | ĐẠT: cao nhất 0.7346 (`image=cmd.exe`) |
| 12 | Tỉ lệ 4688/EID1 của tiến trình trong cây phiên, mỗi host × lớp, nằm trong [0.9, 1.1] | ĐẠT (bảng dưới) |

**Tổng 1–8: ĐẠT. #9: ĐẠT. #10: báo cáo (không có ngưỡng). #11: ĐẠT. #12: ĐẠT.**

Kiểm tra #12 — Security 4688 / Sysmon EID1 của tiến trình trong cây phiên (bỏ conhost như khi dựng cửa sổ):

| Host | Lớp | EID1 | 4688 | Tỉ lệ | Kết quả |
|---|---|---|---|---|---|
| DC01 | attack | 272 | 273 | 1.004 | ĐẠT |
| DC01 | benign | 100 | 100 | 1.0 | ĐẠT |
| DC01 | hard_negative | 432 | 432 | 1.0 | ĐẠT |
| WIN10-01 | attack | 1039 | 1039 | 1.0 | ĐẠT |
| WIN10-01 | benign | 412 | 412 | 1.0 | ĐẠT |
| WIN10-01 | hard_negative | 556 | 556 | 1.0 | ĐẠT |

Kiểm tra #9 — tỉ lệ cửa sổ âm trong Train theo công cụ (không sửa số liệu để ép đạt):

| Công cụ | Train dương | Train âm | % âm | Kết quả |
|---|---|---|---|---|
| `ntdsutil.exe` | 38 | 9 | 19% | ĐẠT |
| `vssadmin.exe` | 3 | 18 | 86% | ĐẠT |
| `ping.exe` | 16 | 9 | 36% | ĐẠT |
| `wevtutil.exe` | 23 | 5 | 18% | ĐẠT |
| `nltest.exe` | 10 | 16 | 62% | ĐẠT |
| `nslookup.exe` | 31 | 8 | 20% | ĐẠT |
| `nbtstat.exe` | 24 | 6 | 20% | ĐẠT |
| `netsh.exe` | 23 | 7 | 23% | ĐẠT |
| `cmd.exe` | 140 | 26 | 16% | ĐẠT |

Kiểm tra #10 — event nền trong 60 cửa sổ dương T1003.003 (3 211 event) so với 13 cửa sổ revert_control (463 event); 10 cặp (channel, event_id) chênh lệch nhiều nhất (tỉ lệ trên tổng event nền mỗi phía):

| channel:event_id | Dương T1003.003 | revert_control | Chênh |
|---|---|---|---|
| `Microsoft-Windows-Sysmon/Operational:3` | 18.8% | 38.2% | -19.4% |
| `Application:216` | 12.5% | 0.0% | +12.5% |
| `Security:4624` | 4.8% | 10.2% | -5.3% |
| `Security:4672` | 4.8% | 10.2% | -5.3% |
| `Microsoft-Windows-Sysmon/Operational:22` | 3.1% | 8.4% | -5.3% |
| `Application:330` | 4.6% | 0.0% | +4.6% |
| `Application:1001` | 0.3% | 3.9% | -3.6% |
| `Security:4634` | 1.0% | 4.5% | -3.5% |
| `Microsoft-Windows-Sysmon/Operational:5` | 1.3% | 4.5% | -3.3% |
| `Application:102` | 3.1% | 0.0% | +3.1% |

Kiểm tra #11 — 10 đặc trưng có mức tách cao nhất (max(AUC, 1−AUC); điểm = tỉ lệ event mang giá trị trong cửa sổ):

| Đặc trưng | Mức tách | Phía | % cửa sổ attack | % cửa sổ HN |
|---|---|---|---|---|
| `image=cmd.exe` | 0.735 | attack | 82.7% | 21.4% |
| `cmdtok=c` | 0.725 | attack | 49.6% | 4.0% |
| `eidbg=1>5` | 0.720 | hard_negative | 77.2% | 87.5% |
| `pair=<launcher>->cmd.exe` | 0.716 | attack | 73.2% | 21.4% |
| `eidbg=5>4688` | 0.710 | hard_negative | 50.4% | 80.4% |
| `cmdtok=-ano` | 0.705 | hard_negative | 0.0% | 41.1% |
| `cmdtok=netstat` | 0.705 | hard_negative | 0.0% | 41.1% |
| `image=netstat.exe` | 0.705 | hard_negative | 0.0% | 41.1% |
| `pair=<launcher>->netstat.exe` | 0.705 | hard_negative | 0.0% | 41.1% |
| `pair=None->cmd.exe` | 0.703 | attack | 76.8% | 21.4% |

Đặc trưng **một phía** còn lại sau trung hoà (77; có ở ≥10% cửa sổ một nhóm, 0 phiên nhóm kia) — phân loại sơ bộ để người duyệt:

| Đặc trưng | Phía | % cửa sổ | Phiên | Phân loại sơ bộ |
|---|---|---|---|---|
| `cmdtok=-ano` | hard_negative | 41.1% | 87 | kich ban benign (coverage attack thieu) |
| `cmdtok=netstat` | hard_negative | 41.1% | 87 | kich ban benign (coverage attack thieu) |
| `image=netstat.exe` | hard_negative | 41.1% | 87 | kich ban benign (coverage attack thieu) |
| `pair=<launcher>->netstat.exe` | hard_negative | 41.1% | 87 | kich ban benign (coverage attack thieu) |
| `cmdtok=print` | hard_negative | 40.2% | 87 | kich ban benign (coverage attack thieu) |
| `cmdtok=route` | hard_negative | 40.2% | 87 | kich ban benign (coverage attack thieu) |
| `image=route.exe` | hard_negative | 40.2% | 87 | kich ban benign (coverage attack thieu) |
| `pair=<launcher>->route.exe` | hard_negative | 40.2% | 87 | kich ban benign (coverage attack thieu) |
| `pair=None->route.exe` | hard_negative | 40.2% | 87 | kich ban benign (coverage attack thieu) |
| `pair=None->netstat.exe` | hard_negative | 39.3% | 83 | kich ban benign (coverage attack thieu) |
| `cmdtok=userdnsdomain` | attack | 23.2% | 44 | hanh vi tan cong |
| `pair=<launcher>->powershell.exe` | attack | 22.4% | 43 | gioi han co chu y (ART chay test PowerShell trong tien trinh con) |
| `cmdtok=dsmsvc` | attack | 20.2% | 34 | hanh vi tan cong |
| `cmdtok=admins` | hard_negative | 19.6% | 43 | kich ban benign (coverage attack thieu) |
| `eid=98` | attack | 18.8% | 26 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=102` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=103` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=105` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=2001` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=2003` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=2005` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=2006` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=216` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=300` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=301` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=302` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=326` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=330` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=102>105` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=105>103` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=105>326` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=2003>2006` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=216>216` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=216>330` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=300>216` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=301>302` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=302>105` | attack | 18.4% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eid=325` | attack | 18.0% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=325>330` | attack | 18.0% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=330>325` | attack | 18.0% | 25 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=102>300` | attack | 17.6% | 24 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=330>301` | attack | 17.6% | 24 | tac dong phu NTDS (ESENT/Directory Service) |
| `cmdtok=-querytype` | attack | 16.9% | 32 | hanh vi tan cong |
| `cmdtok=-timeout` | attack | 16.9% | 32 | hanh vi tan cong |
| `eidbg=2005>2001` | attack | 16.9% | 23 | tac dong phu NTDS (ESENT/Directory Service) |
| `cmdtok=_ldap._tcp.dc._msdcs.` | attack | 16.5% | 32 | hanh vi tan cong |
| `cmdtok=config` | attack | 16.5% | 33 | hanh vi tan cong |
| `eidbg=98>102` | attack | 16.2% | 22 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=326>330` | attack | 15.1% | 21 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=7036>2005` | attack | 15.1% | 21 | tac dong phu NTDS (ESENT/Directory Service) |
| `cmdtok=create` | attack | 14.7% | 35 | hanh vi tan cong |
| `eid=327` | attack | 14.7% | 24 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=2006>98` | attack | 14.3% | 20 | tac dong phu NTDS (ESENT/Directory Service) |
| `cmdtok=.findall` | attack | 14.0% | 30 | hanh vi tan cong |
| `cmdtok=.findone` | attack | 14.0% | 30 | hanh vi tan cong |
| `cmdtok=adsisearcher` | attack | 14.0% | 30 | hanh vi tan cong |
| `cmdtok=enum-logs` | attack | 14.0% | 29 | hanh vi tan cong |
| `cmdtok=objectcategory` | attack | 14.0% | 30 | hanh vi tan cong |
| `cmdtok=/dsgetdc` | hard_negative | 12.9% | 24 | kich ban benign (coverage attack thieu) |
| `cmdtok=list` | hard_negative | 12.9% | 24 | kich ban benign (coverage attack thieu) |
| `eidbg=327>103` | attack | 12.9% | 24 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=327>327` | attack | 12.9% | 24 | tac dong phu NTDS (ESENT/Directory Service) |
| `cmdtok=\windows\system0\shell0.dll` | attack | 12.1% | 25 | tac dong phu nen (svchost->rundll32 COM, ngoai cay tien trinh) |
| `cmdtok=shcreatelocalserverrundll` | attack | 12.1% | 25 | tac dong phu nen (svchost->rundll32 COM, ngoai cay tien trinh) |
| `cmdtok=shadows` | hard_negative | 12.1% | 24 | kich ban benign (coverage attack thieu) |
| `eidbg=16>4624` | attack | 11.8% | 22 | bigram event_id khac (chua ro) |
| `cmdtok=\windows\temp\ntds_t0` | attack | 11.4% | 26 | hanh vi tan cong |
| `cmdtok=full` | attack | 11.4% | 26 | hanh vi tan cong |
| `cmdtok=ifm` | attack | 11.4% | 26 | hanh vi tan cong |
| `cmdtok=q` | attack | 11.4% | 26 | hanh vi tan cong |
| `eidbg=103>4688` | attack | 11.4% | 21 | tac dong phu NTDS (ESENT/Directory Service) |
| `cmdtok=/sc_query` | hard_negative | 10.7% | 20 | kich ban benign (coverage attack thieu) |
| `cmdtok=system` | attack | 10.7% | 20 | hanh vi tan cong |
| `eidbg=3>2003` | attack | 10.7% | 14 | tac dong phu NTDS (ESENT/Directory Service) |
| `eidbg=4104>4688` | attack | 10.7% | 20 | gioi han co chu y (ART chay test PowerShell trong tien trinh con) |
| `cmdtok=administrator` | attack | 10.3% | 22 | hanh vi tan cong |
| `cmdtok=mkdir` | attack | 10.3% | 25 | hanh vi tan cong |

Đọc kết quả #10: phần chênh không hoàn toàn là nhiễu khôi phục snapshot. `Application:216` và `Application:330` (ESENT) chỉ xuất hiện ở ntds/ntds2 — ESENT ghi khi `ntdsutil ifm` sao chép CSDL AD, tức tác động phụ thật của kỹ thuật nằm ngoài cây tiến trình (vẫn là event nền, nhãn benign). Các mục còn lại (Sysmon 3/22, logon 4624/4672/4634, WER 1001) là hoạt động nền khác nhau giữa hai nhóm phiên; revert_control mới có 12 cửa sổ nên ước lượng còn nhiễu.

## 9. Hạn chế đã biết
- **Đường tắt theo tiến trình**: sau khi thêm batch06–07, không công cụ nào chỉ xuất hiện ở phía dương trên toàn bộ dữ liệu. Phía âm vẫn mỏng: `ping.exe` dương 16 / âm 16, `wevtutil.exe` 36 / 11, `ntdsutil.exe` 50 / 16 cửa sổ. Gần như chỉ dương (≥90% số cửa sổ chứa là dương): `powershell.exe` 65/7. Đường tắt ngược (chỉ xuất hiện ở phía âm): `route.exe`, `netstat.exe` — kịch bản benign dùng chúng còn biến thể tấn công thì không. Nên báo cáo ablation bỏ `image_name`.
- **T1003.003 ít dữ liệu đánh giá**: T-clean có 12 cửa sổ dương, T-novel (ntds2v) 6; báo cáo kèm khoảng tin cậy. Phiên ntds2/ntds2v rất ngắn (thường 1–2 cửa sổ, toàn cửa sổ dương), nên không có cửa sổ âm bên trong phiên NTDS mới.
- **Khôi phục snapshot ở ntds/ntds2/ntds2v**: phiên attack NTDS có bước khôi phục snapshot DC01, làm đồng hồ lệch tới ~55 phút cho tới khi đồng bộ lại. Từ v6 không còn ghép nhầm event theo PID, nhưng event nền phát ra lúc đồng hồ lệch có `ts_system` sai nên có thể rơi ra ngoài (hoặc vào nhầm) khung thời gian phiên. Hệ quả hệ thống của việc khôi phục (dịch vụ khởi động lại) có thể tương quan với lớp. batch07 thêm phiên đối chứng revert_control (hard_negative có khôi phục snapshot); kiểm tra #10 cho TVD = 0.482 giữa event nền của cửa sổ dương T1003.003 và cửa sổ revert_control — chênh lớn nhất ở `Microsoft-Windows-Sysmon/Operational:3` (-19.4%).
- **Độ dài cửa sổ khác nhau theo lớp**: tỉ lệ cửa sổ đủ 64 event — attack+ 72%, attack- 100%, benign- 54%, hard_negative- 44%. Không đưa `n_events` vào feature; khi huấn luyện nên cắt ngẫu nhiên độ dài.
- **Phiên chạy song song trên WIN10-01**: tác động phụ của phiên attack (logon mạng, DNS…) không thuộc cây tiến trình có thể nằm trong cửa sổ của phiên benign chạy cùng lúc dưới dạng event nền benign → nhiễu nhãn nhẹ.
- **Phiên không có event riêng**: 45 phiên benign chạy cmdlet ngay trong orchestrator nên event bị loại cùng orchestrator; cửa sổ của chúng chỉ gồm event nền.
- **DC01 ít trong T-clean** (26 cửa sổ so với 63 của WIN10-01) do phân tầng theo phiên.
- **Nhiễu nhãn nhỏ đã biết**: một lệnh `net user /domain` người vận hành gõ tay trên DC01 ở batch05 được giữ làm event nền benign.
- **Lỗ hổng coverage (hành vi, giữ nguyên có chủ ý):** (1) phía attack không có `route print`, `netstat -ano`, truy vấn "Domain Admins" — các lệnh này chỉ có ở kịch bản benign nên là đường tắt ngược (sự hiện diện ⇒ benign); (2) phía benign không có hoạt động IFM/ESENT (event 216/330/2001–2006… của `ntdsutil ifm` chỉ có ở attack). Đo bằng ablation (b)/(c) ở Bước 5–6, không xoá dữ liệu.
- **Giới hạn có chủ ý — `<launcher>→powershell.exe`** (chỉ ở attack, 22% cửa sổ): ART chạy test PowerShell trong một tiến trình powershell con, còn script benign chạy cmdlet ngay trong tiến trình hiện tại. Không gộp thêm vì `image_name=powershell.exe` là hành vi được quan sát; đo bằng ablation (b) (bỏ image_name + parent_image_name).
- **Tác động phụ nền chỉ có ở phiên attack**: `svchost.exe→rundll32.exe shell32.dll,SHCreateLocalServerRunDll` (COM local server, 26 event nền ở 25 phiên attack, ngoài cây tiến trình, nhãn benign) và các event ESENT/Directory Service của `ntdsutil ifm` — mô hình có thể dựa vào event nền này; đo bằng ablation (c) (chỉ cây tiến trình).
- **Trùng PID với orchestrator (lỗi có sẵn, không sửa)**: quy tắc loại orchestrator dựa trên PID và không giới hạn thời gian, nên tiến trình khác trùng PID với một orchestrator trên cùng host bị loại nhầm — 7 tiến trình, 23 event (theo event_id: 1: 7, 5: 4, 22: 4, 3: 1, 4688: 7; ảnh: conhost.exe 4, netsh.exe 2, ntdsutil.exe 2, cmd.exe 2, whoami.exe 2, svchost.exe 2). Chủ yếu ở ntds (PID lặp lại sau mỗi lần khôi phục snapshot), gồm 1 tiến trình `ntdsutil.exe` của phiên attack (malicious) và `netsh.exe` pid 8112 (batch07). Từ v1.2, 4688 của các tiến trình này nhất quán với EID1 (cùng bị loại).
- **Bigram event_id và PowerShell**: chuỗi vòng đời PowerShell (40961→53504→40962→4104) có ở ~22% cửa sổ attack, ~1% hard-negative — đi cùng giới hạn `<launcher>→powershell.exe` (ART chạy test PowerShell trong tiến trình con).
- Chỉ 2 host, 2 tài khoản, 1 domain lab; phạm vi là 5 TTP Discovery/Credential Access, chưa có lateral movement hay persistence.

## 10. Tái lập
```
python src/label/label.py data/interim/<b>.norm.jsonl manifests/<b>,manifests/<cac dot khac...> data/processed/<b>.labeled.jsonl > reports/<b>.stats.json
python src/dataset/merge.py
python src/dataset/windows.py
python src/dataset/featurize.py
python src/dataset/split.py      # fit lại vocab trên Train và ghi data/processed/splits/
python src/dataset/card.py
```

Checksum sha256 (data/ không nằm trong git):

| File | sha256 |
|---|---|
| `all.events.jsonl` | `5675fc147323a7bdaee26026a9411a8461fa391e5a874fd25c37caf0c9fdd703` |
| `windows.jsonl` | `ec2fb7460d1e897f0032dd91435885d382a86382cb5b6048439edd8cd7ed1f68` |
| `features.jsonl` | `262dc14ff8e74fa30d64c5847ed5c8c210af5071204656623a164af14345c9b2` |
| `vocab.json` | `9886ee564f6613bf83290656e7480184b25b21a1b1d5bb6b5954b3d865aa5fb1` |
| `splits/train.jsonl` | `b69928bd22f505744c8fdc8a64712068e03099757b588957a025aa8176a25604` |
| `splits/t_clean.jsonl` | `0e34a0865421661b681f8a34837057f0bd8a2de176fec661efbb8fd82e46992a` |
| `splits/t_hard.jsonl` | `8ebbcd79e98701665e6afe5e7c7f42b69e2ee3ad29f3f8ea157d79470ecb8190` |
| `splits/t_novel.jsonl` | `788691cc50a559769c24c6e6726a52adf3282f185974f2c4aff992f7b55998f4` |

Bản sao vocab dùng khi inference: `reports/vocab.json`.
