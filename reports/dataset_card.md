# VT-Guard — Dataset card (Bước 4, bản đóng băng)

Sinh tự động bởi `src/dataset/card.py` lúc 2026-10-15T16:25:38+07:00. Số liệu chi tiết: `reports/dataset_stats.json`.

## 1. Mục đích
Phát hiện hành vi APT kiểu **Volt Typhoon** (living-off-the-land) trên log Windows thu bằng Wazuh. Đơn vị phát hiện là **cửa sổ phiên** (chuỗi tối đa 64 event), nhãn **đa nhãn** ở mức cửa sổ: `window_malicious` (nhị phân) và `window_ttps` (tập TTP).

## 2. Nguồn gốc
- Hạ tầng: Wazuh agent trên **DC01** (domain controller) và **WIN10-01** (workstation) → Wazuh Indexer.
- Mô phỏng: Atomic Red Team qua orchestrator sinh phiên; mỗi phiên có một manifest (`manifests/<đợt>/`).
- Đợt dùng: batch01, batch02, batch03, batch04, batch05, batch06, ntds, ntds2, ntds2v. Bỏ: smoke6 (chạy thử, gán nhãn bằng labeler cũ).
  - `batch06`: 27 phiên hard-negative bổ sung (quét mạng quản trị bằng ping, kiểm tra log bằng wevtutil, bảo trì CSDL AD bằng ntdsutil…) để giảm đường tắt theo tên tiến trình.
  - `ntds2`: 15 phiên T1003.003 test 3 (`ntdsutil ifm`); `ntds2v`: 6 phiên T1003.003 test 1 (biến thể vssadmin/shadow copy) — giữ làm biến thể held-out.
- Manifest: 449 phiên — batch01 60, batch02 80, batch03 80, batch04 80, batch05 80, batch06 27, ntds 21, ntds2 15, ntds2v 6; theo lớp: attack 151, benign 164, hard_negative 134.
- Pipeline: `normalize.py` (v0) → `label.py` (labeler v6) → `merge.py` → `windows.py` → `featurize.py` (f1) → `split.py`. Seed cố định 1337.
- Event: đọc 407 920, giữ 52 165 (malicious 5 122, benign 47 043; trong đó nền 44 465). DC01 35 245 · WIN10-01 16 920.
- Event malicious theo TTP: T1003.003 338, T1016 3 157, T1018 3 478, T1087.002 3 147, T1654 2 518.
- Log ước lượng: **24.63 giờ** (cộng khoảng thời gian log theo đợt × host); thời lượng phiên theo manifest: attack 5.86 h, benign 4.8 h, hard_negative 3.08 h.

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
- Cửa sổ trượt W=64, stride=32; tối đa K=8 cửa sổ/phiên (lấy mẫu phân tầng dương/âm, seed). 14 phiên bị chặn, 849 → 778 cửa sổ (278 dương, 500 âm).
- `window_malicious` = có ít nhất 1 event malicious; `window_ttps` = hợp TTP của event malicious; `window_class` = lớp phiên.
- **Phiên bị loại (17)**:
  - `20261014-164113-dc01-a` (attack): atomic không sinh tiến trình con nào (labeled=0); loại hẳn, KHÔNG coi là benign.
  - `20261015-075708-dc01-a` (attack): atomic không sinh tiến trình con nào (labeled=0); loại hẳn, KHÔNG coi là benign.
  - `20261015-084801-dc01-a` (attack): atomic không sinh tiến trình con nào (labeled=0); loại hẳn, KHÔNG coi là benign.
  - 14 phiên benign/hard-negative: không có event nào trong khoảng thời gian phiên.

## 5. Các tập (chia theo PHIÊN và NHÓM PHIÊN)

| Tập | Vai trò | Phiên | Cửa sổ | Dương | Tỉ lệ dương | DC01 / WIN10-01 | T1016 | T1018 | T1087.002 | T1654 | T1003.003 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Train | huấn luyện | 241 | 413 | 177 | 42.9% | 154 / 259 | 87 | 79 | 96 | 83 | 41 |
| T-clean | kiểm thử cùng phân phối | 62 | 132 | 47 | 35.6% | 33 / 99 | 24 | 26 | 29 | 21 | 13 |
| T-hard | đo false-positive trên quản trị hợp lệ | 47 | 82 | 0 | 0.0% | 56 / 26 | 0 | 0 | 0 | 0 | 0 |
| T-novel | holdout thời gian + biến thể (batch05 + ntds2v) | 82 | 151 | 54 | 35.8% | 59 / 92 | 37 | 37 | 34 | 16 | 5 |

Số phiên theo đợt trong từng tập:

| Tập | batch01 | batch02 | batch03 | batch04 | batch05 | batch06 | ntds | ntds2 | ntds2v |
|---|---|---|---|---|---|---|---|---|---|
| Train | 53 | 46 | 47 | 62 |  | 10 | 13 | 10 |  |
| T-clean |  | 23 | 21 | 10 |  |  | 4 | 4 |  |
| T-hard | 5 | 6 | 11 | 5 |  | 17 | 3 |  |  |
| T-novel |  |  |  |  | 77 |  |  |  | 5 |

- **T-novel** = toàn bộ phiên batch05 + ntds2v: batch05 là holdout thời gian, ntds2v là biến thể T1003.003 (test 1) không có trong Train. **T-hard** = 40% phiên hard_negative còn lại (kể cả batch06), chọn ngẫu nhiên theo nhóm chỉ gồm hard_negative. Phần còn lại (gồm ntds2) chia **Train 80% / T-clean 20%** theo nhóm, phân tầng theo (lớp, host, chữ ký TTP).
- **Nhóm phiên**: các phiên cùng host chồng thời gian (kể cả bắc cầu) dùng chung event nền, nên cả nhóm vào cùng một tập.

### 5a. Cửa sổ T1003.003 theo tập

| Tập | Phiên T1003.003 (theo đợt) | Cửa sổ dương T1003.003 | Âm trong phiên T1003.003 | Âm trên DC01 | Âm toàn tập |
|---|---|---|---|---|---|
| Train | 22 (ntds 12, ntds2 10) | 41 | 2 | 113 | 372 |
| T-clean | 6 (ntds 2, ntds2 4) | 13 | 0 | 20 | 119 |
| T-hard | 0 (—) | 0 | 0 | 56 | 82 |
| T-novel | 5 (ntds2v 5) | 5 | 0 | 54 | 146 |

### 5b. Coverage theo công cụ (số cửa sổ chứa tiến trình)

Mục tiêu: không công cụ nào chỉ xuất hiện ở phía dương, để mô hình không thể phát hiện chỉ nhờ tên tiến trình.

| image_name | Dương (tất cả) | Âm (tất cả) | Train dương / âm | T-clean dương / âm | T-hard âm | T-novel dương / âm | Cảnh báo |
|---|---|---|---|---|---|---|---|
| `ping.exe` | 16 | 5 | 16 / 1 | 0 / 0 | 4 | 0 / 0 |  |
| `wevtutil.exe` | 38 | 11 | 24 / 4 | 7 / 0 | 7 | 7 / 0 |  |
| `ntdsutil.exe` | 51 | 5 | 38 / 0 | 13 / 0 | 5 | 0 / 0 | chỉ dương trong Train |
| `vssadmin.exe` | 10 | 15 | 3 / 2 | 2 / 2 | 11 | 5 / 0 |  |
| `nltest.exe` | 23 | 19 | 9 / 6 | 5 / 0 | 13 | 9 / 0 |  |
| `net.exe` | 93 | 100 | 60 / 48 | 13 / 9 | 27 | 20 / 16 |  |
| `net1.exe` | 93 | 91 | 60 / 46 | 13 / 9 | 20 | 20 / 16 |  |
| `ipconfig.exe` | 40 | 187 | 23 / 103 | 7 / 31 | 23 | 10 / 30 |  |
| `arp.exe` | 65 | 196 | 35 / 105 | 12 / 33 | 28 | 18 / 30 |  |
| `route.exe` | 0 | 189 | 0 / 104 | 0 / 31 | 24 | 0 / 30 |  |
| `netstat.exe` | 0 | 193 | 0 / 106 | 0 / 33 | 24 | 0 / 30 |  |
| `nslookup.exe` | 48 | 2 | 29 / 1 | 6 / 0 | 1 | 13 / 0 |  |
| `nbtstat.exe` | 40 | 2 | 23 / 1 | 7 / 1 | 0 | 10 / 0 |  |
| `netsh.exe` | 42 | 2 | 24 / 1 | 8 / 1 | 0 | 10 / 0 |  |
| `whoami.exe` | 0 | 1 | 0 / 1 | 0 / 0 | 0 | 0 / 0 |  |
| `cmd.exe` | 231 | 12 | 141 / 3 | 39 / 1 | 8 | 51 / 0 |  |
| `powershell.exe` | 63 | 9 | 43 / 1 | 13 / 0 | 2 | 7 / 6 |  |
| `conhost.exe` | 262 | 55 | 162 / 25 | 47 / 7 | 8 | 53 / 15 |  |
| `rundll32.exe` | 36 | 8 | 25 / 6 | 10 / 2 | 0 | 1 / 0 |  |
| `vssvc.exe` | 39 | 6 | 27 / 3 | 7 / 0 | 3 | 5 / 0 |  |
| `wazuh-agent.exe` | 4 | 1 | 4 / 1 | 0 / 0 | 0 | 0 / 0 |  |

Công cụ chỉ xuất hiện ở phía dương: **toàn bộ dữ liệu: không có**; riêng Train: ntdsutil.exe.

## 6. Đặc trưng (mỗi event → 268 cột)
- 7 categorical → chỉ số embedding (`vocab.json`): `channel` (8), `event_id` (43), `image_name` (60), `parent_image_name` (17), `host_role` (5), `integrity_level` (8), `logon_type` (8). Id 0=`<pad>`, 1=`<unk>`, 2=`<none>`. Token vào vocab khi xuất hiện ở ≥2 phiên Train; `integrity_level` gộp SID về tên.
- `command_line` → 256 chiều: chuẩn hoá (chữ thường, bỏ nháy, GUID/hex/số → ký hiệu), char n-gram 3–5, signed hashing md5, log1p, chuẩn L2. **Không lưu text thô.**
- 5 số: `dt_log` = log(1+Δt giây), `has_network`, `has_dns`, `is_powershell_channel`, `is_security_channel`.
- Vocab fit **chỉ trên Train**; tỉ lệ `<unk>` của `image_name`: fit 0.1%, t_novel 1.9%, other 0.2% (fit = Train, other = T-clean + T-hard).

## 7. Biện pháp chống rò rỉ
- **Trường không bao giờ làm feature**: `wazuh_rule_*` (chỉ cho baseline B0), `label_*`, `run_id`, `event_uid`, `process_guid`, `parent_process_guid`, `script_block_text`, `ps_payload`, đường dẫn đầy đủ `image`/`parent_image`, `n_events`. `featurize.py` assert nguồn feature không khớp mẫu cấm; cửa sổ chỉ mang 11 trường nguồn được phép.
- **Labeler v6** loại event công cụ thay vì gán nhãn (tổng trên 9 đợt): orchestrator 345 312, harness ART 1 518, upload manifest scp/ssh 196, console PowerShell người vận hành 2 415, mảnh vỡ 4103 mất PID 683.
  - v5: chặn upload manifest (v4 gán nhầm 72 event thành malicious T1003.003 ở ntds), console người vận hành, mảnh vỡ 4103.
  - v6: event không có `process_guid` chỉ được ghép vào tiến trình khi `ts_system` nằm trong vòng đời tiến trình (EID1→EID5). v5 ghép theo PID ±300 s bằng giờ Wazuh: sau khi khôi phục snapshot, đồng hồ DC01 lệch ~55 phút nên 204 event PowerShell (pid 1112, nạp module CIM) bị gán nhầm malicious T1003.003 vào phiên ntds2 `20261015-084208-dc01-a`, và 27 event PowerShell khác bị ghép nhầm vào cây scp. Đối chiếu từng event v5↔v6: chỉ 231 event này đổi, các đợt khác giữ nguyên.
- Khử trùng lặp theo `(host, channel, record_id, event_id, ts_system)`: khôi phục snapshot DC01 làm `record_id` quay lui, khoá chỉ có `record_id` sẽ xoá nhầm 7 713 event thật.
- Chia theo phiên và nhóm phiên: không `run_id`/session nào ở 2 tập, không cặp phiên Train/kiểm thử nào chồng thời gian trên cùng host.
- Vocab fit chỉ trên Train; T-novel thật sự chứa token chưa thấy.

## 8. Kiểm thử chấp nhận (chạy lại trên file split)

| # | Kiểm tra | Kết quả |
|---|---|---|
| 1 | Không session/run_id ở >1 tập | ĐẠT (0 vi phạm) |
| 2 | Không feature từ trường cấm; giá trị feature chỉ là số | ĐẠT |
| 3 | T-hard chỉ hard_negative; T-novel chỉ batch05 + ntds2v (và các đợt này không ở tập khác) | ĐẠT |
| 4 | Thống kê mỗi tập (cửa sổ, tỉ lệ dương, TTP, host) | xem mục 5 |
| 5 | Số cửa sổ dương hợp lý | ĐẠT: 278 ≤ 148×8; trung bình 1.88/phiên |
| 6 | Quét rò rỉ 200 cửa sổ dương (atomic/invoke-/T10xx/VT-Guard) + token vocab | ĐẠT (0 hit) |
| 7 | Không cặp phiên Train/kiểm thử chồng thời gian | ĐẠT |
| 8 | Vocab chỉ fit trên Train | ĐẠT |

**Tổng: ĐẠT.** Kiểm tra bổ sung (mục 5b): công cụ chỉ ở phía dương trên toàn bộ dữ liệu — không có.

## 9. Hạn chế đã biết
- **Đường tắt theo tiến trình**: sau khi thêm batch06, không công cụ nào chỉ xuất hiện ở phía dương trên toàn bộ dữ liệu. Phía âm vẫn mỏng: `ping.exe` dương 16 / âm 5, `wevtutil.exe` 38 / 11, `ntdsutil.exe` 51 / 5 cửa sổ. **Riêng Train**, `ntdsutil.exe` chỉ có ở cửa sổ dương (các phiên hard-negative tương ứng rơi vào T-hard), nên mô hình vẫn có thể học đường tắt này; T-hard là nơi đo đúng lỗi đó. Gần như chỉ dương (≥90% số cửa sổ chứa là dương): `ntdsutil.exe` 51/5, `nslookup.exe` 48/2, `nbtstat.exe` 40/2, `netsh.exe` 42/2, `cmd.exe` 231/12. Đường tắt ngược (chỉ xuất hiện ở phía âm): `route.exe`, `netstat.exe`, `whoami.exe` — kịch bản benign dùng chúng còn biến thể tấn công thì không. Nên báo cáo ablation bỏ `image_name`.
- **T1003.003 ít dữ liệu đánh giá**: T-clean có 13 cửa sổ dương, T-novel (ntds2v) 5; báo cáo kèm khoảng tin cậy. Phiên ntds2/ntds2v rất ngắn (thường 1–2 cửa sổ, toàn cửa sổ dương), nên không có cửa sổ âm bên trong phiên NTDS mới.
- **Khôi phục snapshot ở ntds/ntds2/ntds2v**: phiên attack NTDS có bước khôi phục snapshot DC01, làm đồng hồ lệch tới ~55 phút cho tới khi đồng bộ lại. v6 không ghép nhầm event theo PID nữa, nhưng event nền phát ra lúc đồng hồ lệch có `ts_system` sai nên có thể rơi ra ngoài (hoặc vào nhầm) khung thời gian phiên. Hệ quả hệ thống của việc khôi phục (dịch vụ khởi động lại) có thể tương quan với lớp.
- **Độ dài cửa sổ khác nhau theo lớp**: tỉ lệ cửa sổ đủ 64 event — attack+ 74%, attack- 100%, benign- 54%, hard_negative- 40%. Không đưa `n_events` vào feature; khi huấn luyện nên cắt ngẫu nhiên độ dài.
- **Phiên chạy song song trên WIN10-01**: tác động phụ của phiên attack (logon mạng, DNS…) không thuộc cây tiến trình có thể nằm trong cửa sổ của phiên benign chạy cùng lúc dưới dạng event nền benign → nhiễu nhãn nhẹ.
- **Phiên không có event riêng**: 47 phiên benign chạy cmdlet ngay trong orchestrator nên event bị loại cùng orchestrator; cửa sổ của chúng chỉ gồm event nền.
- **DC01 ít trong T-clean** (33 cửa sổ so với 99 của WIN10-01) do phân tầng theo phiên.
- **Nhiễu nhãn nhỏ đã biết**: một lệnh `net user /domain` người vận hành gõ tay trên DC01 ở batch05 được giữ làm event nền benign.
- Chỉ 2 host, 2 tài khoản, 1 domain lab; phạm vi là 5 TTP Discovery/Credential Access, chưa có lateral movement hay persistence.

## 10. Tái lập
```
python src/label/label.py data/interim/<b>.norm.jsonl manifests/<b> data/processed/<b>.labeled.jsonl > reports/<b>.stats.json
python src/dataset/merge.py
python src/dataset/windows.py
python src/dataset/featurize.py
python src/dataset/split.py      # fit lại vocab trên Train và ghi data/processed/splits/
python src/dataset/card.py
```

Checksum sha256 (data/ không nằm trong git):

| File | sha256 |
|---|---|
| `all.events.jsonl` | `d01991d791818482dbc9539598178613060a29c7be1fe7f593250326a5adbb4f` |
| `windows.jsonl` | `6b4f2bfb0449996158fab0482aef876a6fef8006708b9cdc8b34fd5735c36e87` |
| `features.jsonl` | `9a6a04be5fd7f726ecbb07544da91359bfd252700eec3f1bc55c6f8641cc67a3` |
| `vocab.json` | `7ccfe1208100a4ac1350204102cd34fbd6e9ab2f1d1b5462d28e0c9d412c9882` |
| `splits/train.jsonl` | `43aae6e83b0dff8c43e9db655cd72e1ccaed6e9ec3b05c3da54d1790bde2adf8` |
| `splits/t_clean.jsonl` | `fc628170e0ba5cfced42b09c22d9137984e8ab7725e8228e3d1ba775a775c461` |
| `splits/t_hard.jsonl` | `8229393e67ca08a0b4c94ec5e0d2dabe3ce8dfdf64e17dec45048836d5feaf05` |
| `splits/t_novel.jsonl` | `f9cf96199c19e34154ad6ddabcff1d31dda61b40ec53b947f2b1c2b05bd29951` |

Bản sao vocab dùng khi inference: `reports/vocab.json`.
