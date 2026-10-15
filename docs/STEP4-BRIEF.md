# VT-Guard — Bàn giao ngữ cảnh & đặc tả BƯỚC 4 (đóng băng dataset)

Tài liệu này tự chứa. Đọc cùng `src/normalize/normalize.py` và `src/label/label.py`
là đủ để thực hiện Bước 4, không cần ngữ cảnh ở nơi khác.

## 0. Đề tài (tóm tắt)
VT-Guard: phát hiện APT thích nghi, kết hợp AI (GRU-Attention) + luật tự sinh, thực nghiệm
trên TTP của **Volt Typhoon**. Hạ tầng Wazuh (DC01 + WIN10-01 → Indexer). 5 TTP:
T1016, T1018, T1087.002, T1654 (Discovery), T1003.003 (NTDS Credential Access).
Đơn vị phát hiện = **cửa sổ phiên** (sequence of events), nhãn **đa nhãn** (multi-label) ở
mức cửa sổ. Ba yêu cầu môn học: (1) luật tự sinh có xuất xứ, (2) luật dùng chung với AI trong
fusion, (3) AI tùy biến có ablation. Mục tiêu điểm 9-10, hạn 01/11/2026, một người làm.

## 1. Trạng thái hiện tại (ĐÃ XONG Bước 1-3)
- Dataset đã thu đủ: ~129 phiên attack, 107 hard-negative, 164 benign (~400 phiên),
  đủ 5 TTP, 2 host (DC01/WIN10-01), 2 account (user01/admin01).
- Pipeline đã kiểm chứng: Atomic Red Team → Wazuh → Indexer → `normalize.py` → `label.py`.
- Dữ liệu đã gán nhãn nằm ở: `data/processed/{batch01,batch02,batch03,batch04,batch05,ntds}.labeled.jsonl`
- Manifest (nguồn gốc) ở `manifests/<đợt>/`. Thống kê ở `reports/<đợt>.stats.json`.

## 2. Schema event (đầu ra normalize.py, đã có nhãn từ label.py)
Mỗi dòng JSONL là một event phẳng. Trường quan trọng:
- Định danh/thời gian: `event_uid, ts (ISO +0000), host, host_role, agent_id, channel, event_id, record_id`
- Tiến trình: `process_guid, parent_process_guid, process_id, parent_process_id, image, image_name,
  parent_image, parent_image_name, command_line, parent_command_line, integrity_level`
- Danh tính: `user, subject_user, subject_domain, target_user, logon_type, logon_id, auth_package`
- Mạng/DNS: `dst_ip, dst_port, dst_host, protocol, dns_query`
- Script: `script_block_text, ps_payload`  (NHẠY CẢM — xem mục rò rỉ)
- Nhãn (do label.py điền): `label_malicious (bool), label_ttps (list), label_source, run_id,
  dropped (bool), drop_reason`
- Ngữ cảnh Wazuh (CHỈ cho baseline B0, KHÔNG làm feature): `wazuh_rule_id, wazuh_rule_level, wazuh_rule_mitre`

Lưu ý: event có `dropped=True` là event orchestrator/harness ĐÃ BỊ LOẠI (chống rò rỉ) — KHÔNG
đưa vào dataset. Chỉ dùng event `dropped=False`.

## 3. QUY TẮC CHỐNG RÒ RỈ (bắt buộc giữ — đây là điểm 9-10)
Tuyệt đối KHÔNG dùng làm feature: `wazuh_rule_*`, `label_*`, `run_id`, `event_uid`, `process_guid`,
đường dẫn tuyệt đối chứa tên công cụ mô phỏng (C:\AtomicRedTeam, VT-Guard, Invoke-...), và
`script_block_text`/`ps_payload` dạng thô (chúng có thể chứa dấu vết khung ART). v1 BỎ HẲN
script_block_text khỏi feature; chỉ dùng `command_line` (là hành vi thật, không chứa tên TTP).
Event `dropped=True` đã loại đúng phần rò rỉ ở label.py — giữ nguyên.

## 4. ĐẶC TẢ BƯỚC 4 — các bước con

### 4.1 Gộp dataset  → `src/dataset/merge.py`
- Đọc tất cả `data/processed/*.labeled.jsonl`, gắn thêm trường `batch` (tên file nguồn).
- Chỉ giữ event `dropped != True`.
- Khử trùng lặp theo `(host, record_id, event_id)` (phòng khi khoảng export chồng nhau).
- Ghi `data/processed/all.events.jsonl`. In thống kê: tổng event, theo host, theo batch,
  số event malicious/benign, số run_id duy nhất theo class.

### 4.2 Cắt cửa sổ phiên  → `src/dataset/windows.py`
- Nhóm event theo (host, run_id) cho event có run_id; event nền (run_id=None) gom theo
  (host, phiên gần nhất về thời gian) — hoặc đơn giản: dựng "session stream" = mọi event
  (dropped=False) trên cùng host nằm trong [t_start, t_end] của manifest phiên đó
  (đọc manifest ở manifests/*/*.manifest.json để lấy t_start/t_end/class/ttps/host).
- Mỗi session stream: sort theo ts, cắt cửa sổ trượt **W=64 event, stride=32**.
- Nhãn cửa sổ: `window_malicious = any(label_malicious trong cửa sổ)`;
  `window_ttps = union(label_ttps các event malicious trong cửa sổ)`;
  `window_class` = class của phiên (attack/benign/hard_negative).
- **GIỚI HẠN chống áp đảo**: tối đa **K=8 cửa sổ mỗi phiên** (lấy mẫu ngẫu nhiên có seed nếu
  phiên sinh nhiều hơn). Lý do: 2 phiên ping-sweep ở batch01 sinh ~800 event, không được áp đảo.
- Ghi `data/processed/windows.jsonl`: mỗi dòng = {window_id, run_id, batch, host, user_role,
  tempo, variant (từ manifest), t0, t1, n_events, window_malicious, window_ttps, window_class,
  events: [danh sách event rút gọn chỉ gồm các trường feature ở 4.3]}.

### 4.3 Trích đặc trưng  → `src/dataset/featurize.py` + `data/processed/vocab.json`
Mỗi event trong cửa sổ → vector:
- Categorical (xây vocab → chỉ số embedding): `channel, event_id, image_name, parent_image_name,
  host_role, integrity_level, logon_type`. Token lạ → <unk>.
- `command_line`: hashing trick char n-gram (n=3..5) vào vector cố định (vd 256 chiều) — KHÔNG
  lưu text thô vào feature. Viết hàm hash ổn định (md5 mod dim).
- `dt_log`: log(1 + Δt giây so với event trước trong cửa sổ).
- Cờ nhị phân: has_network (event 3/có dst_port), has_dns (event 22/có dns_query),
  is_powershell_channel, is_security_channel.
- Ghi `vocab.json` (map token→id cho từng trường categorical) để tái lập khi inference.

### 4.4 Chia tập chống rò rỉ (CHIA THEO PHIÊN, không theo cửa sổ)  → `src/dataset/split.py`
Chia theo `run_id` để không có cửa sổ cùng phiên lọt sang hai tập. Bốn tập:
- **T-novel** = toàn bộ phiên thuộc `batch05` (giữ lại thời gian/biến thể chưa huấn luyện — holdout thời gian).
- Từ phần còn lại (batch01-04 + ntds):
  - **T-hard** = 40% phiên `hard_negative` (ngẫu nhiên, seed) — đo false-positive trên hoạt động admin hợp lệ.
  - Phần còn lại chia **Train 80% / T-clean 20%**, phân tầng theo (class, host, chữ ký TTP của phiên).
- Bất biến: mỗi run_id chỉ ở đúng MỘT tập. In kiểm tra: không run_id nào ở 2 tập.
- Ghi `data/processed/splits/{train,t_clean,t_hard,t_novel}.jsonl` (các cửa sổ).

### 4.5 Dataset card  → `reports/dataset_card.md` + `reports/dataset_stats.json`
Gồm: nguồn gốc (5 batch + ntds, số manifest), phân phối lớp & TTP theo tập, số cửa sổ dương/âm
mỗi tập, tỉ lệ dương, số giờ log benign ước lượng, danh sách feature, các biện pháp chống rò rỉ
(liệt kê trường bị loại), seed, checksum (sha256) của mỗi file split, phiên bản normalize/label.

## 5. Kiểm thử chấp nhận (acceptance) — in ra, phải đạt
- Không run_id nào xuất hiện ở >1 tập.
- Không feature nào lấy từ: wazuh_rule_*, label_*, run_id, event_uid, process_guid, script_block_text.
- T-hard chỉ gồm hard_negative; T-novel chỉ gồm phiên batch05.
- Mỗi tập in: số cửa sổ, tỉ lệ dương, phân phối TTP (đa nhãn), phân phối host.
- Tổng số cửa sổ dương (attack) hợp lý so với ~129 phiên attack × tối đa 8 cửa sổ.
- Quét rò rỉ cuối: với mẫu 200 cửa sổ dương, xác nhận không feature text nào chứa
  "atomic/invoke-/T10xx/VT-Guard".

## 6. Quy ước khi code (giống Bước 1-3)
- Python thuần chạy trên host (Windows, Python 3.12), chỉ thư viện chuẩn + numpy nếu cần
  (tránh phụ thuộc nặng ở bước dataset; model để Colab ở Bước 6).
- File .ps1/.py chỉ ASCII (PowerShell 5.1 ghi BOM — nếu đọc manifest, dùng encoding utf-8-sig).
- Mỗi script: chạy được độc lập, in thống kê rõ ràng, có seed cố định (vd 1337).
- Commit từng bước con. Dữ liệu trong data/ bị .gitignore; chỉ commit code + reports/ + dataset_card.
- Làm từng bước con, chạy, in thống kê, cho người dùng xác nhận rồi mới sang bước con kế.

## 7. Sau Bước 4 (để biết hướng, chưa làm)
Bước 5: baseline B0 (luật Wazuh từ wazuh_rule_*), B1 (TF-IDF+LR), B2 (LightGBM theo cửa sổ),
B3 (GRU thuần). Bước 6: VT-Seq (GRU-Attention đa nhiệm) + ablation, huấn luyện Colab, xuất ONNX
cho inference CPU. Bước 7-8: Auto Rule Engine (RIPPER/cây QĐ → Sigma) + quality gate; Hybrid Fusion.
Giữ `vocab.json` và quy ước feature để tái dùng ở các bước này.
