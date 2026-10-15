# VT-Guard — Dataset card (Bước 4, bản đóng băng)

Sinh tự động bởi `src/dataset/card.py` lúc 2026-10-15T10:27:53+07:00. Số liệu chi tiết: `reports/dataset_stats.json`.

## 1. Mục đích
Phát hiện hành vi APT kiểu **Volt Typhoon** (living-off-the-land) trên log Windows thu bằng Wazuh. Đơn vị phát hiện là **cửa sổ phiên** (chuỗi tối đa 64 event), nhãn **đa nhãn** ở mức cửa sổ: `window_malicious` (nhị phân) và `window_ttps` (tập TTP).

## 2. Nguồn gốc
- Hạ tầng: Wazuh agent trên **DC01** (domain controller) và **WIN10-01** (workstation) → Wazuh Indexer.
- Mô phỏng: Atomic Red Team qua orchestrator sinh phiên; mỗi phiên có một manifest (`manifests/<đợt>/`).
- Đợt dùng: batch01, batch02, batch03, batch04, batch05, ntds. Bỏ: smoke6 (chạy thử, gán nhãn bằng labeler cũ).
- Manifest: 401 phiên — batch01 60, batch02 80, batch03 80, batch04 80, batch05 80, ntds 21; theo lớp: attack 130, benign 164, hard_negative 107.
- Pipeline: `normalize.py` (v0) → `label.py` (labeler v5) → `merge.py` → `windows.py` → `featurize.py` (f1) → `split.py`. Seed cố định 1337.
- Event: đọc 364 711, giữ 41 901 (malicious 4 920, benign 36 981; trong đó nền 34 779). DC01 26 380 · WIN10-01 15 521.
- Log ước lượng: **21.9 giờ** (cộng khoảng thời gian log theo đợt × host); thời lượng phiên theo manifest: attack 5.77 h, benign 4.8 h, hard_negative 2.92 h.

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
- Cửa sổ trượt W=64, stride=32; tối đa K=8 cửa sổ/phiên (lấy mẫu phân tầng dương/âm, seed). 14 phiên bị chặn, 784 → 713 cửa sổ.
- Loại 15 phiên: `20261014-164113-dc01-a` (attack_khong_co_event_malicious) và 14 phiên benign/hard-negative có stream rỗng.
- `window_malicious` = có ít nhất 1 event malicious; `window_ttps` = hợp TTP của event malicious; `window_class` = lớp phiên.

## 5. Các tập (chia theo PHIÊN và NHÓM PHIÊN)

| Tập | Vai trò | Phiên | Cửa sổ | Dương | Tỉ lệ dương | DC01 / WIN10-01 | T1016 | T1018 | T1087.002 | T1654 | T1003.003 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Train | huấn luyện | 219 | 396 | 156 | 39.4% | 141 / 255 | 87 | 80 | 97 | 82 | 19 |
| T-clean | kiểm thử cùng phân phối | 54 | 108 | 38 | 35.2% | 18 / 90 | 24 | 25 | 28 | 22 | 5 |
| T-hard | đo false-positive trên quản trị hợp lệ | 36 | 63 | 0 | 0.0% | 36 / 27 | 0 | 0 | 0 | 0 | 0 |
| T-novel | holdout thời gian/biến thể (batch05) | 77 | 146 | 49 | 33.6% | 54 / 92 | 37 | 37 | 34 | 16 | 0 |

- **T-novel** = toàn bộ phiên batch05. **T-hard** = 40% phiên hard_negative còn lại, chọn ngẫu nhiên theo nhóm chỉ gồm hard_negative. Phần còn lại chia **Train 80% / T-clean 20%** theo nhóm, phân tầng theo (lớp, host, chữ ký TTP).
- **Nhóm phiên**: các phiên cùng host chồng thời gian (kể cả bắc cầu) dùng chung event nền, nên cả nhóm vào cùng một tập.

## 6. Đặc trưng (mỗi event → 268 cột)
- 7 categorical → chỉ số embedding (`vocab.json`): `channel` (8), `event_id` (43), `image_name` (60), `parent_image_name` (17), `host_role` (5), `integrity_level` (8), `logon_type` (8). Id 0=`<pad>`, 1=`<unk>`, 2=`<none>`. Token vào vocab khi xuất hiện ở ≥2 phiên Train; `integrity_level` gộp SID về tên.
- `command_line` → 256 chiều: chuẩn hoá (chữ thường, bỏ nháy, GUID/hex/số → ký hiệu), char n-gram 3–5, signed hashing md5, log1p, chuẩn L2. **Không lưu text thô.**
- 5 số: `dt_log` = log(1+Δt giây), `has_network`, `has_dns`, `is_powershell_channel`, `is_security_channel`.
- Vocab fit **chỉ trên Train**; tỉ lệ `<unk>` của `image_name`: fit 0.1%, batch05 2.0%, other 0.2% (fit = Train, other = T-clean + T-hard).

## 7. Biện pháp chống rò rỉ
- **Trường không bao giờ làm feature**: `wazuh_rule_*` (chỉ cho baseline B0), `label_*`, `run_id`, `event_uid`, `process_guid`, `parent_process_guid`, `script_block_text`, `ps_payload`, đường dẫn đầy đủ `image`/`parent_image`, `n_events`. `featurize.py` assert nguồn feature không khớp mẫu cấm; cửa sổ chỉ mang 11 trường nguồn được phép.
- **Labeler v5** loại event của công cụ, không gán nhãn: orchestrator (theo `exclude_pids`), harness ART (conhost/hostname/whoami), **upload manifest scp/ssh** (v4 đã gán nhầm 72 event thành malicious T1003.003 = 35% số event NTDS), **console PowerShell của người vận hành** có script gọi ART/VT (2 415 event, có `runas`/`w32tm` trước mỗi phiên NTDS), và **mảnh vỡ 4103** mất PID chứa text Invoke-AtomicTest (680 event).
- Khử trùng lặp theo `(host, channel, record_id, event_id, ts_system)`: khôi phục snapshot DC01 làm `record_id` quay lui, khoá chỉ có `record_id` sẽ xoá nhầm 3 558 event thật.
- Chia theo phiên và nhóm phiên: không `run_id` nào ở 2 tập, không cặp phiên Train/kiểm thử nào chồng thời gian trên cùng host.
- Vocab fit chỉ trên Train; T-novel thật sự chứa token chưa thấy.

## 8. Kiểm thử chấp nhận (chạy lại trên file split)

| # | Kiểm tra | Kết quả |
|---|---|---|
| 1 | Không run_id ở >1 tập | ĐẠT (0 vi phạm) |
| 2 | Không feature từ trường cấm; giá trị feature chỉ là số | ĐẠT |
| 3 | T-hard chỉ hard_negative; T-novel chỉ batch05 (và batch05 không ở tập khác) | ĐẠT |
| 4 | Thống kê mỗi tập (cửa sổ, tỉ lệ dương, TTP, host) | xem mục 5 |
| 5 | Số cửa sổ dương hợp lý | ĐẠT: 243 ≤ 129×8; trung bình 1.88/phiên |
| 6 | Quét rò rỉ 200 cửa sổ dương (atomic/invoke-/T10xx/VT-Guard) + token vocab | ĐẠT (0 hit) |
| 7 | Không cặp phiên Train/kiểm thử chồng thời gian | ĐẠT |
| 8 | Vocab chỉ fit trên Train | ĐẠT |

**Tổng: ĐẠT.**

## 9. Hạn chế đã biết
- **Đường tắt theo tiến trình**: `ping.exe` (T1018), `wevtutil.exe` (T1654) và `ntdsutil.exe` (T1003.003) chỉ xuất hiện trong cửa sổ dương. Không phiên benign/hard-negative nào dùng ping hay wevtutil, nên T-hard chưa thử thách các TTP này; mô hình có thể đạt điểm cao chỉ nhờ tên tiến trình. Cần thu thêm hard-negative dùng ping/wevtutil hợp lệ, và báo cáo ablation bỏ `image_name`.
- **T1003.003 chỉ có trong Train/T-clean** (đợt ntds riêng, batch05 không có NTDS): T-clean chỉ có 5 cửa sổ T1003.003 → độ tin cậy thấp; T-novel không đo được TTP này.
- **Khôi phục snapshot ở ntds**: phiên attack NTDS có bước khôi phục snapshot DC01 trước mỗi lần chạy, hard-negative thì không. Hệ quả phụ (dịch vụ khởi động lại, nhảy đồng hồ) có thể tương quan với lớp; event công cụ đã loại, nhưng hệ quả hệ thống thì không lọc được.
- **Độ dài cửa sổ khác nhau theo lớp**: cửa sổ đủ 64 event chiếm 72% ở attack dương, 54% ở benign, 44% ở hard-negative. Không đưa `n_events` vào feature; khi huấn luyện nên cắt ngẫu nhiên độ dài và đánh giá thêm trên tập cân bằng độ dài.
- **Phiên chạy song song trên WIN10-01**: tác động phụ của phiên attack (logon mạng, DNS…) không thuộc cây tiến trình có thể nằm trong cửa sổ của phiên benign chạy cùng lúc dưới dạng event nền benign → nhiễu nhãn nhẹ.
- **Phiên benign không có event riêng**: 47 phiên benign chạy cmdlet ngay trong orchestrator nên event bị loại cùng orchestrator; cửa sổ của chúng chỉ gồm event nền.
- **DC01 ít trong T-clean** (18 cửa sổ so với 90 của WIN10-01) do phân tầng theo phiên, phiên DC01 nhiều cửa sổ rơi vào Train.
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
| `all.events.jsonl` | `1f93737ea39952e53206656c535f70c49d0da875390c687a762c0c2cf1d34c9c` |
| `windows.jsonl` | `3a44fd9d0c8150cca447889fa6c6b721eddc29f4d56bcb96150ecf6d816579f3` |
| `features.jsonl` | `454604bb9f6cb7356337ce6c648163903091f687c6fdc40543c60135941ba95d` |
| `vocab.json` | `10ec93d4b7121999ceb34c9759212885bb31180512657b540e5b462d3cdb38ad` |
| `splits/train.jsonl` | `604e987fe10b566b36ced28eb883d941fa290e00d257b93a10ba416dddbd960c` |
| `splits/t_clean.jsonl` | `59e490aa54825fd47a0adc2c43c2eebc1984fa3337f2899b6f2bf884abebf5c0` |
| `splits/t_hard.jsonl` | `c59a35bb7c54ea7b77c11041b9c4c04e870cf87bc384b75fcef24860a911e6f0` |
| `splits/t_novel.jsonl` | `cf5d0a09c032659055f57307ccbfa0045987e4d037cd0e978225b2d6010ad9f0` |

Bản sao vocab dùng khi inference: `reports/vocab.json`.
