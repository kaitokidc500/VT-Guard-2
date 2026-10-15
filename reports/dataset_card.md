# VT-Guard — Dataset card (Bước 4, bản đóng băng)

Sinh tự động bởi `src/dataset/card.py` lúc 2026-10-15T20:38:01+07:00. Số liệu chi tiết: `reports/dataset_stats.json`.

> **Phiên bản `dataset-v1.0` — ĐÓNG BĂNG.** Split (`data/processed/splits/*.jsonl`), `vocab.json` và checksum ở mục 10 là cố định: mọi mô hình ở Bước 5–8 phải dùng đúng các file này. Trước khi huấn luyện/đánh giá, kiểm tra sha256 khớp bảng mục 10. Muốn đổi dữ liệu → tạo phiên bản mới (dataset-v1.1…), không sửa tại chỗ.

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
- Pipeline: `normalize.py` (v0) → `label.py` (labeler v7) → `merge.py` → `windows.py` → `featurize.py` (f1) → `split.py`. Seed cố định 1337.
- Event: đọc 423 597, giữ 61 490 (malicious 5 224, benign 56 266; trong đó nền 52 846). DC01 43 347 · WIN10-01 18 143.
- Event malicious theo TTP: T1003.003 338, T1016 3 251, T1018 3 580, T1087.002 3 272, T1654 2 518.
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
- Cửa sổ trượt W=64, stride=32; tối đa K=8 cửa sổ/phiên (lấy mẫu phân tầng dương/âm, seed). 14 phiên bị chặn, 880 → 809 cửa sổ (278 dương, 531 âm).
- `window_malicious` = có ít nhất 1 event malicious; `window_ttps` = hợp TTP của event malicious; `window_class` = lớp phiên.
- **Phiên bị loại (21)**:
  - `20261014-073330-dc01-h` (hard_negative, batch02, log_review): không có event tiến trình con trong khung phiên (task chỉ chạy cmdlet ngay trong tiến trình orchestrator, không có khôi phục snapshot); loại hẳn theo quy tắc chung hard_negative labeled=0.
  - `20261014-093702-win10-01-h` (hard_negative, batch03, log_review): không có event tiến trình con trong khung phiên (task chỉ chạy cmdlet ngay trong tiến trình orchestrator, không có khôi phục snapshot); loại hẳn theo quy tắc chung hard_negative labeled=0.
  - `20261014-120938-win10-01-h` (hard_negative, batch04, log_review): không có event tiến trình con trong khung phiên (task chỉ chạy cmdlet ngay trong tiến trình orchestrator, không có khôi phục snapshot); loại hẳn theo quy tắc chung hard_negative labeled=0.
  - `20261014-122845-dc01-h` (hard_negative, batch04, log_review): không có event tiến trình con trong khung phiên (task chỉ chạy cmdlet ngay trong tiến trình orchestrator, không có khôi phục snapshot); loại hẳn theo quy tắc chung hard_negative labeled=0.
  - `20261014-133522-win10-01-h` (hard_negative, batch05, log_review): không có event tiến trình con trong khung phiên (task chỉ chạy cmdlet ngay trong tiến trình orchestrator, không có khôi phục snapshot); loại hẳn theo quy tắc chung hard_negative labeled=0.
  - `20261014-164113-dc01-a` (attack, ntds, T1003.003/3, snapshot DC01-CLEAN-ART): atomic không sinh tiến trình con nào (labeled=0); loại hẳn, KHÔNG coi là benign.
  - `20261015-075708-dc01-a` (attack, ntds2, T1003.003/3, snapshot DC01-CLEAN-ART): atomic không sinh tiến trình con nào (labeled=0); loại hẳn, KHÔNG coi là benign.
  - `20261015-130127-dc01-h` (hard_negative, batch07, dc_db_maint, snapshot DC01-CLEAN-ART): không có event tiến trình con trong khung phiên, nghi do agent hoặc đồng hồ sau khi khôi phục snapshot; loại hẳn (quy tắc chung: hard_negative labeled=0 bị loại như phiên attack).
  - `20261015-130245-dc01-h` (hard_negative, batch07, dc_db_maint, snapshot DC01-CLEAN-ART): không có event tiến trình con trong khung phiên, nghi do agent hoặc đồng hồ sau khi khôi phục snapshot; loại hẳn (quy tắc chung: hard_negative labeled=0 bị loại như phiên attack).
  - 12 phiên benign: không có event nào trong khoảng thời gian phiên.
- `revert_control` = phiên hard_negative chạy sau khi khôi phục snapshot (dc_db_maint batch07). Chỉ dùng cho card và kiểm tra #10, KHÔNG làm feature (nằm trong mẫu trường cấm của `featurize.py`).

## 5. Các tập (chia theo PHIÊN và NHÓM PHIÊN)

| Tập | Vai trò | Phiên | Cửa sổ | Dương | Tỉ lệ dương | DC01 / WIN10-01 | T1016 | T1018 | T1087.002 | T1654 | T1003.003 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Train | huấn luyện | 262 | 479 | 178 | 37.2% | 193 / 286 | 87 | 79 | 98 | 84 | 41 |
| T-clean | kiểm thử cùng phân phối | 52 | 91 | 45 | 49.5% | 26 / 65 | 24 | 26 | 27 | 20 | 12 |
| T-hard | đo false-positive trên quản trị hợp lệ | 61 | 87 | 0 | 0.0% | 46 / 41 | 0 | 0 | 0 | 0 | 0 |
| T-novel | holdout thời gian + biến thể (batch05 + ntds2v) | 83 | 152 | 55 | 36.2% | 60 / 92 | 37 | 37 | 34 | 17 | 6 |

Số phiên theo đợt trong từng tập:

| Tập | batch01 | batch02 | batch03 | batch04 | batch05 | batch06 | batch07 | ntds | ntds2 | ntds2v |
|---|---|---|---|---|---|---|---|---|---|---|
| Train | 45 | 53 | 50 | 63 |  | 12 | 13 | 14 | 12 |  |
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
| Train | 22 (ntds 10, ntds2 12) | 41 | 2 | 152 | 438 |
| T-clean | 6 (ntds 4, ntds2 2) | 12 | 0 | 14 | 79 |
| T-hard | 0 (—) | 0 | 0 | 46 | 87 |
| T-novel | 6 (ntds2v 6) | 6 | 0 | 54 | 146 |

### 5b. Coverage theo công cụ (số cửa sổ chứa tiến trình)

Mục tiêu: không công cụ nào chỉ xuất hiện ở phía dương, để mô hình không thể phát hiện chỉ nhờ tên tiến trình.

| image_name | Dương (tất cả) | Âm (tất cả) | Train dương / âm | Train % âm | T-clean dương / âm | T-hard âm | T-novel dương / âm | Cảnh báo |
|---|---|---|---|---|---|---|---|---|
| `ping.exe` | 16 | 14 | 16 / 8 | 33% | 0 / 1 | 5 | 0 / 0 |  |
| `wevtutil.exe` | 40 | 11 | 25 / 5 | 17% | 7 / 0 | 6 | 8 / 0 |  |
| `ntdsutil.exe` | 50 | 15 | 38 / 8 | 17% | 12 / 1 | 6 | 0 / 0 |  |
| `vssadmin.exe` | 9 | 27 | 3 / 16 | 84% | 0 / 1 | 10 | 6 / 0 |  |
| `nltest.exe` | 24 | 27 | 10 / 15 | 60% | 5 / 1 | 11 | 9 / 0 |  |
| `net.exe` | 94 | 107 | 59 / 62 | 51% | 15 / 7 | 22 | 20 / 16 |  |
| `net1.exe` | 94 | 89 | 59 / 52 | 47% | 15 / 6 | 15 | 20 / 16 |  |
| `ipconfig.exe` | 43 | 200 | 23 / 108 | 82% | 9 / 22 | 39 | 11 / 31 |  |
| `arp.exe` | 68 | 196 | 34 / 107 | 76% | 15 / 22 | 36 | 19 / 31 |  |
| `route.exe` | 0 | 190 | 0 / 103 | 100% | 0 / 22 | 34 | 0 / 31 |  |
| `netstat.exe` | 0 | 193 | 0 / 106 | 100% | 0 / 22 | 34 | 0 / 31 |  |
| `nslookup.exe` | 49 | 14 | 32 / 8 | 20% | 5 / 0 | 6 | 12 / 0 |  |
| `nbtstat.exe` | 43 | 11 | 23 / 6 | 21% | 9 / 0 | 5 | 11 / 0 |  |
| `netsh.exe` | 45 | 15 | 25 / 7 | 22% | 9 / 0 | 8 | 11 / 0 |  |
| `cmd.exe` | 231 | 44 | 142 / 24 | 14% | 37 / 2 | 18 | 52 / 0 |  |
| `powershell.exe` | 66 | 7 | 41 / 3 | 7% | 15 / 0 | 0 | 10 / 4 |  |
| `conhost.exe` | 262 | 51 | 163 / 34 | 17% | 45 / 0 | 3 | 54 / 14 |  |
| `rundll32.exe` | 35 | 8 | 24 / 5 | 17% | 10 / 2 | 1 | 1 / 0 |  |
| `vssvc.exe` | 40 | 7 | 26 / 4 | 13% | 8 / 0 | 3 | 6 / 0 |  |

**Trước / sau batch07** — tỉ lệ dương = số cửa sổ dương chứa công cụ / tổng số cửa sổ chứa công cụ (trước = bản đóng băng commit d1db577, labeler v6; sau = bản này, labeler v7):

| image_name | Trước: dương / âm | Trước: tỉ lệ dương | Sau: dương / âm | Sau: tỉ lệ dương | Train âm trước → sau |
|---|---|---|---|---|---|
| `ping.exe` | 16 / 5 | 76% | 16 / 14 | 53% | 1 → 8 |
| `wevtutil.exe` | 38 / 11 | 78% | 40 / 11 | 78% | 4 → 5 |
| `ntdsutil.exe` | 51 / 5 | 91% | 50 / 15 | 77% | 0 → 8 |
| `vssadmin.exe` | 10 / 15 | 40% | 9 / 27 | 25% | 2 → 16 |
| `nltest.exe` | 23 / 19 | 55% | 24 / 27 | 47% | 6 → 15 |
| `net.exe` | 93 / 100 | 48% | 94 / 107 | 47% | 48 → 62 |
| `net1.exe` | 93 / 91 | 50% | 94 / 89 | 51% | 46 → 52 |
| `ipconfig.exe` | 40 / 187 | 18% | 43 / 200 | 18% | 103 → 108 |
| `arp.exe` | 65 / 196 | 25% | 68 / 196 | 26% | 105 → 107 |
| `route.exe` | 0 / 189 | 0% | 0 / 190 | 0% | 104 → 103 |
| `netstat.exe` | 0 / 193 | 0% | 0 / 193 | 0% | 106 → 106 |
| `nslookup.exe` | 48 / 2 | 96% | 49 / 14 | 78% | 1 → 8 |
| `nbtstat.exe` | 40 / 2 | 95% | 43 / 11 | 80% | 1 → 6 |
| `netsh.exe` | 42 / 2 | 96% | 45 / 15 | 75% | 1 → 7 |
| `cmd.exe` | 231 / 12 | 95% | 231 / 44 | 84% | 3 → 24 |
| `powershell.exe` | 63 / 9 | 88% | 66 / 7 | 90% | 1 → 3 |
| `conhost.exe` | 262 / 55 | 83% | 262 / 51 | 84% | 25 → 34 |
| `rundll32.exe` | 36 / 8 | 82% | 35 / 8 | 81% | 6 → 5 |
| `vssvc.exe` | 39 / 6 | 87% | 40 / 7 | 85% | 3 → 4 |

Công cụ chỉ xuất hiện ở phía dương: **toàn bộ dữ liệu: không có**; riêng Train: không có.

## 6. Đặc trưng (mỗi event → 268 cột)
- 7 categorical → chỉ số embedding (`vocab.json`): `channel` (8), `event_id` (45), `image_name` (60), `parent_image_name` (17), `host_role` (5), `integrity_level` (8), `logon_type` (8). Id 0=`<pad>`, 1=`<unk>`, 2=`<none>`. Token vào vocab khi xuất hiện ở ≥2 phiên Train; `integrity_level` gộp SID về tên.
- `command_line` → 256 chiều: chuẩn hoá (chữ thường, bỏ nháy, GUID/hex/số → ký hiệu), char n-gram 3–5, signed hashing md5, log1p, chuẩn L2. **Không lưu text thô.**
- 5 số: `dt_log` = log(1+Δt giây), `has_network`, `has_dns`, `is_powershell_channel`, `is_security_channel`.
- Vocab fit **chỉ trên Train**; tỉ lệ `<unk>` của `image_name`: fit 0.0%, t_novel 1.9%, other 0.0% (fit = Train, other = T-clean + T-hard).

## 7. Biện pháp chống rò rỉ
- **Trường không bao giờ làm feature**: `wazuh_rule_*` (chỉ cho baseline B0), `label_*`, `run_id`, `event_uid`, `process_guid`, `parent_process_guid`, `script_block_text`, `ps_payload`, đường dẫn đầy đủ `image`/`parent_image`, `n_events`. `featurize.py` assert nguồn feature không khớp mẫu cấm; cửa sổ chỉ mang 11 trường nguồn được phép.
- **Labeler v7** loại event công cụ thay vì gán nhãn (tổng trên 10 đợt): orchestrator 347 672, harness ART 1 462, upload manifest scp/ssh 270, console PowerShell người vận hành 2 408, mảnh vỡ 4103 mất PID 683.
  - v5: chặn upload manifest (v4 gán nhầm 72 event thành malicious T1003.003 ở ntds), console người vận hành, mảnh vỡ 4103.
  - v6: event không có `process_guid` chỉ được ghép vào tiến trình khi `ts_system` nằm trong vòng đời tiến trình (EID1→EID5). v5 ghép theo PID ±300 s bằng giờ Wazuh: sau khi khôi phục snapshot, đồng hồ DC01 lệch ~55 phút nên 204 event PowerShell (pid 1112, nạp module CIM) bị gán nhầm malicious T1003.003 vào phiên ntds2 `20261015-084208-dc01-a`, và 27 event PowerShell khác bị ghép nhầm vào cây scp. Đối chiếu từng event v5↔v6: chỉ 231 event này đổi, các đợt khác giữ nguyên.
  - v7: phiên = đúng khung [t_start, t_end] của manifest (±5 s) so bằng `ts_system`; con của orchestrator sinh ngoài mọi khung bị loại (`orch_child_outside`, 225 event). v4–v6 gán tiến trình vào phiên theo giờ Wazuh (trễ 40–60 s) và kéo khung tới lúc phiên kế tiếp bắt đầu, nên (1) 102 event của phiên attack bị gán nhãn benign/hard-negative của phiên chạy ngay sau (vd nbtstat/netsh/nslookup của T1016), (2) lệnh người vận hành gõ sau phiên trong cùng cửa sổ PowerShell (w32tm, VMwareToolboxCmd timesync, whoami) bị gán vào phiên (batch07 `20261015-122828-dc01-h`: 61 → 45 event). Đối chiếu v6↔v7: 400 event đổi trạng thái hoặc phiên.
  - v7 cũng nạp manifest của đợt bên cạnh khi khung phiên giao với khung các phiên của đợt đang gán nhãn (±10 phút): export cắt theo giờ Wazuh nên tiến trình của `20261015-084801-dc01-a` (ntds2v) nằm trong file ntds2; phiên này nay có 8 event và không còn bị loại.
- Khử trùng lặp theo `(host, channel, record_id, event_id, ts_system)`: khôi phục snapshot DC01 làm `record_id` quay lui, khoá chỉ có `record_id` sẽ xoá nhầm 13 661 event thật.
- Chia theo phiên và nhóm phiên: không `run_id`/session nào ở 2 tập, không cặp phiên Train/kiểm thử nào chồng thời gian trên cùng host.
- Vocab fit chỉ trên Train; T-novel thật sự chứa token chưa thấy.

## 8. Kiểm thử chấp nhận (chạy lại trên file split)

| # | Kiểm tra | Kết quả |
|---|---|---|
| 1 | Không session/run_id ở >1 tập | ĐẠT (0 vi phạm) |
| 2 | Không feature từ trường cấm; giá trị feature chỉ là số | ĐẠT |
| 3 | T-hard chỉ hard_negative; T-novel chỉ batch05 + ntds2v (và các đợt này không ở tập khác) | ĐẠT |
| 4 | Thống kê mỗi tập (cửa sổ, tỉ lệ dương, TTP, host) | xem mục 5 |
| 5 | Số cửa sổ dương hợp lý | ĐẠT: 278 ≤ 149×8; trung bình 1.87/phiên |
| 6 | Quét rò rỉ 200 cửa sổ dương (atomic/invoke-/T10xx/VT-Guard) + token vocab | ĐẠT (0 hit) |
| 7 | Không cặp phiên Train/kiểm thử chồng thời gian | ĐẠT |
| 8 | Vocab chỉ fit trên Train | ĐẠT |
| 9 | Train có cửa sổ âm ≥15% số cửa sổ chứa từng công cụ (ntdsutil, vssadmin, ping, wevtutil, nltest, nslookup, nbtstat, netsh, cmd) | KHÔNG ĐẠT (cmd.exe) |
| 10 | So phân bố (channel, event_id) của event nền: cửa sổ dương T1003.003 vs cửa sổ revert_control | đã chạy: khoảng cách biến phân toàn phần (TVD) = 0.495 (xem bảng dưới) |

**Tổng 1–8: ĐẠT. #9: KHÔNG ĐẠT. #10: báo cáo (không có ngưỡng).**

Kiểm tra #9 — tỉ lệ cửa sổ âm trong Train theo công cụ (không sửa số liệu để ép đạt):

| Công cụ | Train dương | Train âm | % âm | Kết quả |
|---|---|---|---|---|
| `ntdsutil.exe` | 38 | 8 | 17% | ĐẠT |
| `vssadmin.exe` | 3 | 16 | 84% | ĐẠT |
| `ping.exe` | 16 | 8 | 33% | ĐẠT |
| `wevtutil.exe` | 25 | 5 | 17% | ĐẠT |
| `nltest.exe` | 10 | 15 | 60% | ĐẠT |
| `nslookup.exe` | 32 | 8 | 20% | ĐẠT |
| `nbtstat.exe` | 23 | 6 | 21% | ĐẠT |
| `netsh.exe` | 25 | 7 | 22% | ĐẠT |
| `cmd.exe` | 142 | 24 | 14% | KHÔNG ĐẠT |

Kiểm tra #10 — event nền trong 59 cửa sổ dương T1003.003 (3 127 event) so với 12 cửa sổ revert_control (432 event); 10 cặp (channel, event_id) chênh lệch nhiều nhất (tỉ lệ trên tổng event nền mỗi phía):

| channel:event_id | Dương T1003.003 | revert_control | Chênh |
|---|---|---|---|
| `Microsoft-Windows-Sysmon/Operational:3` | 19.0% | 39.8% | -20.8% |
| `Application:216` | 12.5% | 0.0% | +12.5% |
| `Security:4624` | 4.7% | 10.2% | -5.5% |
| `Security:4672` | 4.9% | 10.2% | -5.3% |
| `Microsoft-Windows-Sysmon/Operational:22` | 3.2% | 8.3% | -5.1% |
| `Application:330` | 4.6% | 0.0% | +4.6% |
| `Security:4634` | 1.0% | 4.6% | -3.6% |
| `Application:1001` | 0.3% | 3.7% | -3.5% |
| `Microsoft-Windows-Sysmon/Operational:5` | 1.3% | 4.6% | -3.3% |
| `Application:102` | 3.1% | 0.0% | +3.1% |

Đọc kết quả #10: phần chênh không hoàn toàn là nhiễu khôi phục snapshot. `Application:216` và `Application:330` (ESENT) chỉ xuất hiện ở ntds/ntds2 — ESENT ghi khi `ntdsutil ifm` sao chép CSDL AD, tức tác động phụ thật của kỹ thuật nằm ngoài cây tiến trình (vẫn là event nền, nhãn benign). Các mục còn lại (Sysmon 3/22, logon 4624/4672/4634, WER 1001) là hoạt động nền khác nhau giữa hai nhóm phiên; revert_control mới có 12 cửa sổ nên ước lượng còn nhiễu.

## 9. Hạn chế đã biết
- **Kiểm tra #9**: `cmd.exe` có ít hơn 15% cửa sổ âm trong Train (không ép đạt bằng cách sửa số liệu; cần thêm phiên hard-negative hoặc chấp nhận và báo cáo ablation).
- **Đường tắt theo tiến trình**: sau khi thêm batch06–07, không công cụ nào chỉ xuất hiện ở phía dương trên toàn bộ dữ liệu. Phía âm vẫn mỏng: `ping.exe` dương 16 / âm 14, `wevtutil.exe` 40 / 11, `ntdsutil.exe` 50 / 15 cửa sổ. Gần như chỉ dương (≥90% số cửa sổ chứa là dương): `powershell.exe` 66/7. Đường tắt ngược (chỉ xuất hiện ở phía âm): `route.exe`, `netstat.exe` — kịch bản benign dùng chúng còn biến thể tấn công thì không. Nên báo cáo ablation bỏ `image_name`.
- **T1003.003 ít dữ liệu đánh giá**: T-clean có 12 cửa sổ dương, T-novel (ntds2v) 6; báo cáo kèm khoảng tin cậy. Phiên ntds2/ntds2v rất ngắn (thường 1–2 cửa sổ, toàn cửa sổ dương), nên không có cửa sổ âm bên trong phiên NTDS mới.
- **Khôi phục snapshot ở ntds/ntds2/ntds2v**: phiên attack NTDS có bước khôi phục snapshot DC01, làm đồng hồ lệch tới ~55 phút cho tới khi đồng bộ lại. Từ v6 không còn ghép nhầm event theo PID, nhưng event nền phát ra lúc đồng hồ lệch có `ts_system` sai nên có thể rơi ra ngoài (hoặc vào nhầm) khung thời gian phiên. Hệ quả hệ thống của việc khôi phục (dịch vụ khởi động lại) có thể tương quan với lớp. batch07 thêm phiên đối chứng revert_control (hard_negative có khôi phục snapshot); kiểm tra #10 cho TVD = 0.495 giữa event nền của cửa sổ dương T1003.003 và cửa sổ revert_control — chênh lớn nhất ở `Microsoft-Windows-Sysmon/Operational:3` (-20.8%).
- **Độ dài cửa sổ khác nhau theo lớp**: tỉ lệ cửa sổ đủ 64 event — attack+ 74%, attack- 100%, benign- 53%, hard_negative- 41%. Không đưa `n_events` vào feature; khi huấn luyện nên cắt ngẫu nhiên độ dài.
- **Phiên chạy song song trên WIN10-01**: tác động phụ của phiên attack (logon mạng, DNS…) không thuộc cây tiến trình có thể nằm trong cửa sổ của phiên benign chạy cùng lúc dưới dạng event nền benign → nhiễu nhãn nhẹ.
- **Phiên không có event riêng**: 45 phiên benign chạy cmdlet ngay trong orchestrator nên event bị loại cùng orchestrator; cửa sổ của chúng chỉ gồm event nền.
- **DC01 ít trong T-clean** (26 cửa sổ so với 65 của WIN10-01) do phân tầng theo phiên.
- **Nhiễu nhãn nhỏ đã biết**: một lệnh `net user /domain` người vận hành gõ tay trên DC01 ở batch05 được giữ làm event nền benign.
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
| `all.events.jsonl` | `65d590db3e3953a1df10cf0b0e30c8c33b722bc971674174e05b56b6e97ae497` |
| `windows.jsonl` | `a9b39fab92dc57249ea55b61cdc85349fddde3fa6a6f8df9aea226d22d2b4144` |
| `features.jsonl` | `abcda0dde17b57dec726b428296901d17dda9788e202a9462527f25c25a28974` |
| `vocab.json` | `f92a0915e442d4884ccf3dd49e16d53b15b6203fa05089c0ecff3ed90d5474bf` |
| `splits/train.jsonl` | `22008227ab6af1eeddb12073c6e3aad22475d012b8ed8ee5c97fd815735a493b` |
| `splits/t_clean.jsonl` | `7795fe3178094d14a43cacae2d9bbbd28934a9abdc34ec8626326772c32c8f2b` |
| `splits/t_hard.jsonl` | `185ae4d09bbc704c0ea621c111299fce7f9ae54e9dcdbadede5820b2e568b2ae` |
| `splits/t_novel.jsonl` | `e53b4ff7f366b18a07ba411b64b99d5cee8d7c2fbcea63129597afff905b9478` |

Bản sao vocab dùng khi inference: `reports/vocab.json`.
