# Bước 11 — Cải tiến đề tài và mô hình (hướng dẫn từng bước)

Cập nhật: 24/10/2026. Hạn nộp: 01/11/2026. Đọc kèm `docs/ASSESSMENT.md` (các mã W1–W10 dưới đây là điểm yếu nêu ở đó).

**Thứ tự bắt buộc:** chỉ bắt đầu Bước 11 khi đã xong (1) KB1–KB6 trên hạ tầng thật + tag `step9-done` và (2) báo cáo Word đã dán ảnh,
điền số liệu. Hai việc đó nâng điểm nhiều hơn mọi cải tiến dưới đây (xem ASSESSMENT mục 1).

Ký hiệu: ⏱ thời lượng ước tính · 🎯 điểm yếu được giải quyết · ✅ tiêu chí chấp nhận · ⚠ rủi ro.

---

## 0. Luật chơi (giữ nguyên tính trung thực của Bước 4–8)

1. **Không sửa `dataset-v1.2`**, không chạy lại split/featurize/label trên nó, không dời tag đã đẩy. Dữ liệu mới vào **tập kiểm thử riêng**
   (`data/processed/step11/<tên>/`) hoặc phiên bản mới `dataset-v1.3`.
2. **Mô hình và luật đã triển khai giữ nguyên** khi chấm tập kiểm thử mới (VT-Seq-ens M3, 11 luật, F3-B β = 0,1, τ khoá).
   Nếu cải tiến làm thay đổi mô hình/luật → cấu hình mới phải khoá bằng commit **trước** khi chấm, và báo song song bản cũ.
3. Mỗi tập kiểm thử mới chấm **một lần**; nếu phải chấm lại vì lỗi pipeline, ghi rõ trong báo cáo.
4. Không đưa lên git: log thô, `*.pt`/`*.onnx`, `deploy/.env`, `deploy/secrets/`, `*.docx`.
5. Mọi phiên tấn công vẫn chỉ gọi **Atomic Red Team theo mã test** qua `orchestrator/Invoke-VTSession.ps1`, trong lab cô lập, có snapshot.
6. Kết quả của Bước 11 viết thành **mục bổ sung / phụ lục** của báo cáo (đề xuất: 3.15 “Đánh giá mở rộng”), không sửa số liệu chính đã báo ở 3.1–3.14.

---

## Nhóm A — làm được trước 01/11 (chọn theo thứ tự, mỗi mục độc lập)

### A1. Đo báo nhầm khi chạy trực tiếp 24 giờ (soak test)

🎯 W1 (tỉ lệ báo nhầm thực tế chưa biết) · ⏱ 1 giờ chuẩn bị + 24 giờ chạy + 2 giờ phân tích

**Mục tiêu.** Trả lời câu “nếu cắm vào lab và để yên một ngày thì VT-Guard báo bao nhiêu cảnh báo sai?” — bằng số đo trên hạ tầng thật,
không phải trên tập kiểm thử.

**Các bước.**
1. Trên VT-SIEM01, đảm bảo `vtguard-live` đang chạy, sạch cảnh báo cũ:
   ```bash
   cd ~/vtguard/deploy
   docker compose exec vtguard-live python src/live/run.py live --env-file /secrets/vtguard.env --check
   # lưu cảnh báo KB1–KB6 sang chỗ khác rồi làm sạch (checkpoint xoá -> đọc tiếp từ thời điểm khởi động lại)
   docker compose cp vtguard-live:/app/reports/step9/live/alerts.jsonl ./kb_alerts_backup.jsonl
   docker compose exec vtguard-live sh -c 'rm -f /app/reports/step9/live/connector_state.json; : > /app/reports/step9/live/alerts.jsonl'
   docker compose restart vtguard-live
   ```
   (`--reset` chỉ có tác dụng khi chạy luồng, bị bỏ qua khi đi cùng `--check`.)
   Ghi lại giờ bắt đầu (`date -Is`) vào sổ thực nghiệm.
2. Trong 24 giờ **không chạy bất kỳ phiên tấn công nào**. Hoạt động trên DC01/WIN10-01 gồm:
   - người vận hành đăng nhập, mở Explorer, trình duyệt, Event Viewer, Server Manager như bình thường (ít nhất 2 khung 30 phút);
   - chạy kịch bản lành tính và hard-negative có sẵn (`orchestrator/benign/`) theo vòng lặp thưa, ví dụ `Invoke-Batch07.ps1 -Loop` với khoảng nghỉ dài;
   - để máy rảnh qua đêm (đo nền Windows: Windows Update, tác vụ lịch, Defender).
3. Sau 24 giờ, lấy file cảnh báo và trạng thái ra:
   ```bash
   docker compose cp vtguard-live:/app/reports/step9/live/alerts.jsonl ./soak_alerts.jsonl
   docker compose cp vtguard-live:/app/reports/step9/live/status.json ./soak_status.json
   ```
4. Viết `src/live/soak_report.py` (mới, ~80 dòng, chỉ stdlib):
   - đầu vào `--alerts`, `--status`, `--t0`, `--t1`;
   - đếm số cửa sổ đã chấm (từ `status.json`), số cảnh báo, **cảnh báo / host / giờ**, chia theo `decision_source` (`both` / `ai`) và mức độ;
   - xuất `reports/step11/soak/soak_report.md` + bảng liệt kê từng cảnh báo (host, t0, top-5 sự kiện attention, luật khớp) để phân loại tay.
5. Phân loại tay **từng** cảnh báo vào 3 nhóm: (a) báo nhầm do hoạt động quản trị, (b) báo nhầm do nền Windows, (c) không xác định.
   Ghi lý do một dòng cho mỗi cảnh báo trong `reports/step11/soak/triage.md`.

✅ Có bảng: số giờ, số cửa sổ, số cảnh báo, cảnh báo/host/giờ, % ở nhóm `both` vs `ai`; mọi cảnh báo đã phân loại.
Viết kèm câu so sánh với Wazuh trong cùng khung giờ (đếm `wazuh-alerts-*` mức ≥ 4 trên 2 agent — Discover, lọc `agent.name`).

⚠ Nếu cảnh báo nhiều (> 1 / host / giờ) **không được chỉnh ngưỡng rồi báo lại** — báo trung thực, phân tích nguyên nhân, đưa vào hướng phát triển
(A1 chính là bằng chứng cho mục B2 hiệu chỉnh xác suất).

---

### A2. Tập kiểm thử biến thể chưa thấy (T-novel-2)

🎯 W2, W10 (tổng quát hoá sang cách thực hiện khác của cùng kỹ thuật) · ⏱ 0,5 ngày lab + 0,5 ngày phân tích

**Mục tiêu.** Kiểm tra mô hình đã triển khai trên **các Atomic test chưa từng dùng** của cùng 5 kỹ thuật (dataset chỉ dùng
T1016 #1–2, T1018 #1–2, T1087.002 #1–2, T1654 #1–2, T1003.003 #3 — xem `orchestrator/scenarios.json`).

**Các bước.**
1. Trên máy tấn công trong lab, liệt kê test có sẵn của từng kỹ thuật (chỉ xem, không chạy):
   `Invoke-AtomicTest T1018 -ShowDetailsBrief` (lặp cho 5 kỹ thuật). Chọn test **chạy được trên Windows, không cần tải công cụ ngoài**,
   chưa có trong `scenarios.json`. Ghi danh sách chọn vào `docs/STEP11-A2-tests.md` **trước khi chạy** (khoá lựa chọn).
2. Tạo `orchestrator/scenarios_novel2.json` (sao từ `scenarios.json`, chỉ đổi `tests`); không sửa file gốc.
3. Chạy một đợt nhỏ `batch11n` bằng `Invoke-VTBatch.ps1` với file kịch bản mới: ~20 phiên attack (mỗi test chọn ≥ 3 phiên),
   + ~10 phiên benign/hard-negative xen kẽ để đo báo nhầm trong cùng khung. T1003.003 chỉ trên DC01, có snapshot như cũ.
4. Export JSON từ Indexer như các đợt trước (`data/raw/batch11n/`), manifest vào `manifests/batch11n/`.
5. Xử lý bằng **đúng mã** của dataset-v1.2 (normalize v1 → labeler v8 → windows → featurize với `reports/vocab.json`), đầu ra
   `data/processed/step11/novel2/windows.jsonl` — **không** gọi `split.py`, không ghi vào `data/processed/splits/`.
6. Chấm: `python src/pipeline/infer.py --windows data/processed/step11/novel2/windows.jsonl --out reports/step11/novel2/alerts.jsonl`,
   sau đó tính F1 nhị phân, recall theo kỹ thuật **mức phiên**, báo nhầm trên phiên lành tính; so với B0 (luật Wazuh,
   `src/baselines/b0_wazuh.py` trên cùng cửa sổ). CI bootstrap như Bước 5 (`src/eval/bootstrap.py`).

✅ Bảng recall mức phiên theo từng test ART mới, VT-Guard vs Wazuh; nêu rõ test nào bị bỏ sót và vì sao (đọc attention + luật khớp).

⚠ Một số test mới có thể không sinh tiến trình con (labeled = 0) → loại như quy tắc Bước 4, ghi số phiên bị loại.
Mô hình có thể bỏ sót nhiều — **đó là kết quả có giá trị**, không phải thất bại; không huấn luyện lại trên tập này.

---

### A3. Kiểm thử ngoài trên dataset công khai (bản nhỏ)

🎯 W2 (khác lab, khác người sinh dữ liệu) · ⏱ 1–1,5 ngày

**Mục tiêu.** Một phép thử “ngoài phân phối” thật: log Sysmon/Security do nhóm khác thu, máy khác, tên miền khác.

**Nguồn đề xuất** (tải thủ công về `data/external/`, không vào git; ghi URL + sha256 trong `data/external/SOURCES.md` và `reports/step11/external/sources.json`):
- **OTRF Security-Datasets** (Mordor): các bộ atomic Windows cho discovery (net group/net user, nltest, ipconfig, …) và
  credential access NTDS — định dạng JSON từng sự kiện, có Sysmon + Security.
- **EVTX-ATTACK-SAMPLES** (sbousseaden): file `.evtx` theo tactic — cần chuyển EVTX → JSON (thư viện `python-evtx`).
- Tập **lành tính** đối chứng: chọn các bộ “benign/baseline” của Security-Datasets nếu có; nếu không, chỉ báo recall, không báo FPR.

**Các bước.**
1. Viết `src/external/convert.py` (mới): đọc JSON/EVTX → bản ghi theo schema của normalize v1 (`docs/schema.md`): `ts_system`, `host`,
   `channel`, `event_id`, `image`, `parent_image`, `command_line`, `process_guid`, `process_id`, `parent_process_id`…
   Map trường Sysmon (`Image`, `ParentImage`, `CommandLine`, `ProcessGuid`) và Security 4688 (`NewProcessName`, `NewProcessId`, `ProcessId`).
   Thêm kiểm thử `src/external/test_convert.py` với 3–5 sự kiện mẫu viết tay.
2. Nhãn: dataset công khai không có manifest → dùng **nhãn mức file**: file thuộc kỹ thuật X ⇒ mọi cửa sổ có tiến trình khớp mô tả
   của file là dương X. Ghi rõ đây là nhãn thô; chỉ báo **recall mức file** (file có ≥ 1 cảnh báo đúng kỹ thuật hay không).
3. Cắt cửa sổ bằng `src/dataset/windows.py` (hàm dựng stream theo host + thời gian, W = 64) → featurize với `reports/vocab.json` (token lạ → OOV,
   đúng như khi triển khai).
4. Chấm bằng `infer.py` như A2, và B0 nếu file có trường `rule` của Wazuh (thường không có → chỉ VT-Guard).
5. Báo cáo: số file, số cửa sổ, tỉ lệ token OOV, recall mức file theo kỹ thuật, ví dụ cảnh báo có attention.

✅ Có ít nhất 1 file/kỹ thuật cho ≥ 3 trong 5 kỹ thuật; bảng recall mức file; tỉ lệ OOV.

⚠ Rủi ro lớn nhất là **lệch schema** (thiếu `process_guid`, khác tên host) chứ không phải mô hình — dành nửa thời gian cho bộ chuyển đổi
và kiểm tra thủ công 20 sự kiện đầu. Nếu tỉ lệ OOV > 50%, kết luận trung thực: mô hình phụ thuộc từ vựng lab.

---

### A4. Chuẩn bị bảo vệ: phân tích lỗi có hệ thống (không cần lab)

🎯 W3, W4 · ⏱ 3–4 giờ

1. Viết `src/eval/error_analysis.py`: đọc `reports/step8/alerts_t_novel.jsonl`, `alerts_t_hard.jsonl` và nhãn split → liệt kê mọi FN, FP của F3-B
   với top-5 sự kiện attention, luật khớp, độ dài cửa sổ, chữ ký công cụ.
2. Gom nhóm nguyên nhân (cửa sổ ngắn, kỹ thuật T1654, trùng công cụ hard-negative, …) thành bảng `reports/step11/error_analysis.md`.
3. Đưa 1 bảng + 2 ví dụ vào slide “Hạn chế và phân tích lỗi”.

✅ Mọi FN/FP trên T-novel và T-hard có một dòng giải thích; có câu trả lời sẵn cho 4 câu hỏi ở ASSESSMENT mục 4.

---

## Nhóm B — cải tiến mô hình / luật (sau khi nộp, hoặc nếu dư ≥ 3 ngày)

### B1. Cổng độ đặc hiệu token cho luật tự sinh (rules v2)

🎯 W5 · ⏱ 1 ngày

**Vấn đề.** Luật hiện tại dùng token phổ biến (`create`, `system`) — chúng khớp cả ngoài hành vi tấn công.
**Cách làm.**
1. Trong `src/rules/induce.py` thêm cổng **G1b** trước G2: với mỗi atom token, tính tần suất xuất hiện trong **cửa sổ âm của Train**
   (`df_neg`) và trong **toàn bộ token lệnh Train** (`df_all`). Loại atom nếu `df_all` > 20% số cửa sổ Train **hoặc** token nằm trong danh sách
   từ chức năng (`create`, `system`, `delete`, `list`, `query`, `get`, `set`, `/c`, …) ghi trong `predicates.py` như S6.
2. Thêm hằng số `MAX_TOKEN_DF = 0.2` cạnh `PREC_OOF`… và ghi vào provenance (mục `gates`).
3. Chạy lại `induce.py` + `oof.py` → `rules/sigma_v2/`, `reports/step11/rules_v2/`. **Không ghi đè** `rules/sigma/`.
4. Khoá bộ luật v2 bằng commit, rồi chấm T-hard/T-novel một lần; báo song song v1/v2 và F3-B với luật v2 (`final_fusion.json` bản v2 riêng).

✅ Không luật nào chứa token trong S6; báo nhầm T-hard không tăng; báo rõ mất bao nhiêu recall T1003.003 trên ntds2v (dự kiến giảm — đó là
cái giá trung thực của việc bỏ trùng khớp `create`).
⚠ Có thể chỉ còn < 11 luật; chấp nhận, ghi vào báo cáo như một phát hiện.

### B2. Hiệu chỉnh xác suất và ngưỡng theo vận hành

🎯 W1, kết quả A1 · ⏱ 0,5 ngày

1. `src/fusion/calibrate.py`: temperature scaling (1 tham số) học **trên OOF Train** của `vtseq_M3_ens_train.jsonl`; đo ECE + reliability diagram
   trước/sau trên OOF và trên T-clean.
2. Thêm 2 mức ngưỡng cho vận hành: “cao” (FPR OOF ≤ 0,5%) và “cần xem lại” (FPR OOF ≤ 2%); dashboard đã có cột mức độ — chỉ cần đọc ngưỡng mới
   từ `reports/step11/calibration.json`.
3. Nếu A1 cho thấy báo nhầm cao: tính lại cảnh báo/host/giờ với ngưỡng “cao” **trên chính log 24 giờ đã thu** (ghi rõ là phân tích sau).

✅ ECE giảm; bảng đánh đổi recall T-novel ↔ cảnh báo/host/giờ.

### B3. Luật tương quan cho T1016 và T1087.002

🎯 W5 (2/5 kỹ thuật chưa có luật riêng) · ⏱ 1 ngày

1. Mở rộng không gian atom trong `predicates.py` thêm atom **cặp có thứ tự trong 5 phút** cùng host (image A rồi image B), chỉ từ Train.
2. Cho RIPPER học thêm với atom cặp; giữ nguyên cổng G0–G4 (+ G1b).
3. Xuất luật cặp thành Sigma correlation `temporal_ordered` (pySigma đã dùng ở Bước 7 cho correlation `temporal`).

✅ Có ≥ 1 luật qua cổng cho mỗi kỹ thuật T1016 / T1087.002, hoặc báo rõ không có luật nào qua G3 (cũng là kết quả).

### B4. Kiểm soát độ dài cửa sổ (crop đều)

🎯 W7 · ⏱ 1 ngày Colab

1. Trong `src/models/vtseq.py`, thêm chế độ `crop="matched"`: ở mỗi batch, lấy mẫu độ dài đích từ **cùng một** phân phối cho cả dương và âm
   (histogram độ dài cửa sổ âm Train), thay cho U[4, n] riêng từng mẫu.
2. Huấn luyện 5 seed trên Colab (`notebooks/step6_vtseq_colab.ipynb`, tham số mới), chấm OOF; đo Spearman điểm–độ dài như Bước 5.
3. Chỉ thay mô hình triển khai nếu OOF không kém và Spearman giảm rõ — quyết định khoá bằng commit trước khi chấm test.

✅ Spearman điểm–độ dài trên T-hard giảm (mục tiêu < 0,3) mà macro-F1 OOF không giảm quá 0,02.

### B5. dataset-v1.3 — lấp khoảng trống phủ

🎯 W1, các mục mở #9/#10 của dataset card · ⏱ 2–3 ngày (thu + xử lý)

1. Thu thêm: phiên benign gọi công cụ qua `cmd.exe /c` (sửa `network_check`, `user_inventory`, `log_review` trong `orchestrator/benign/`);
   hard-negative có `route`/`netstat` ở cả hai phía; thêm 1 máy (WIN10-02) nếu đủ tài nguyên; ít nhất 15 phiên T1003.003 mới.
2. Chạy lại toàn bộ Bước 4 thành **phiên bản mới** `dataset-v1.3` (tag mới), card mới; kiểm tra #1–#12 phải đạt.
3. Huấn luyện lại VT-Seq + luật + fusion trên v1.3; báo song song v1.2 / v1.3.

⚠ Tốn thời gian nhất, không làm trước hạn nộp.

---

## Nhóm C — kỹ thuật, đóng gói (làm xen kẽ khi chờ lab)

| Mục | Việc | ⏱ | ✅ |
|---|---|---|---|
| C1 | `requirements.txt` (Python 3.12) chốt phiên bản: numpy, scikit-learn 1.9.1, lightgbm 4.7.0, onnxruntime, pySigma 2.0.1, streamlit, wittgenstein (nếu dùng) — lấy từ `docker/requirements.lock` | 0,5 h | `pip install -r requirements.txt` trên venv sạch + chạy `test_*.py` đạt |
| C2 | GitHub Actions `.github/workflows/tests.yml`: chạy `src/models/test_vtseq.py`, `src/rules/test_induce.py`, `src/fusion/test_fuse.py`, `src/live/test_live.py`, `dashboard/test_data.py` (các test không cần `data/`) | 1 h | badge xanh trên README |
| C3 | Dựng image arm64 (`docker buildx build --platform linux/arm64`) nếu máy giảng viên là Apple Silicon; chạy `verify` trong QEMU | 1–2 h | `verify` 7/7 trên arm64 |
| C4 | Xuất luật Sigma sang **luật Wazuh XML** (`src/rules/wazuh_export.py`: field `CommandLine|re` → `<field name="win.eventdata.commandLine" type="pcre2">`), nạp vào `local_rules.xml`, id 100100+ | 0,5 ngày | Wazuh tự bắn luật VT-Guard trên KB2 — demo “đưa tri thức sinh ra trở lại SIEM” |
| C5 | Gom cảnh báo theo sự cố (cùng host, cách nhau ≤ 15 phút) ngay trong `run.py` khi ghi `vtguard-alerts-*` | 0,5 ngày | Wazuh Dashboard hiện 1 sự cố thay vì n cảnh báo |

---

## Lịch đề xuất nếu làm trước hạn

| Ngày | Việc |
|---|---|
| 25/10 | (sau khi xong KB1–KB6) bắt đầu A1 (để chạy qua đêm) + A4 song song |
| 26/10 | Kết thúc A1, phân loại cảnh báo; A2 chạy lab buổi chiều |
| 27/10 | Phân tích A2; C1 + C2 |
| 28/10 | (tuỳ) A3 bản nhỏ 1–2 kỹ thuật; viết mục 3.15 + phụ lục |
| 29/10 | Dừng Bước 11. Slide + tổng duyệt demo |

Nhóm B và B5 ghi vào mục **Hướng phát triển** của báo cáo với đúng mô tả ở trên (vấn đề → cách làm → tiêu chí), không cần thực hiện.

## Ghi lại sau mỗi mục

- Kết quả vào `reports/step11/<mục>/` (md + json), commit cùng mã.
- Thêm một dòng nhật ký vào `agent.md` mục 6, cập nhật mục 3 (dòng Bước 11) và mục 7.
- Nếu số liệu đưa vào báo cáo Word: sửa `report/ch3*.js` rồi dựng lại bằng `node report/build.js` (file `.docx` không commit).
