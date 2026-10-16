# VT-Guard — Bàn giao ngữ cảnh & đặc tả BƯỚC 5 (baselines + giao thức đánh giá)

Tài liệu này tự chứa. Đọc cùng `reports/dataset_card.md`, `reports/dataset_stats.json` và
`data/processed/splits/*.jsonl` là đủ để làm Bước 5, không cần ngữ cảnh ở nơi khác.

## 0. Đề tài (tóm tắt)
VT-Guard: phát hiện APT thích nghi, kết hợp AI (GRU-Attention) + luật tự sinh (Sigma) trong một
bộ hợp nhất (fusion), thực nghiệm trên TTP của **Volt Typhoon**. Hạ tầng Wazuh (DC01 + WIN10-01).
5 TTP: T1016, T1018, T1087.002, T1654 (Discovery), T1003.003 (NTDS Credential Access).
Đơn vị phát hiện = **cửa sổ phiên**, nhãn **đa nhãn** ở mức cửa sổ. Ba yêu cầu môn học:
(1) luật tự sinh có xuất xứ + kiểm định, (2) luật dùng chung với AI trong fusion, so với
chỉ-luật và chỉ-AI, (3) AI tùy biến biểu diễn chuỗi event, có ablation so baseline đơn giản.
Mục tiêu 9–10, hạn 01/11/2026, một người làm.

## 1. MỤC TIÊU BƯỚC 5
Xây dựng **các baseline** và **khung đánh giá dùng chung** cho toàn bộ Bước 5–8. Bước 5 trả lời
hai câu hỏi học thuật:
- Một mô hình học máy đơn giản có hơn luật SIEM có sẵn không, và hơn bao nhiêu?
- Mỗi baseline dựa vào tín hiệu gì — hành vi thật hay đường tắt (tên tiến trình, độ dài cửa sổ)?

Bước 5 KHÔNG xây mô hình chính (VT-Seq GRU-Attention — để Bước 6). Nhưng **khung đánh giá
`src/eval/evaluate.py` viết ở Bước 5 sẽ được mọi bước sau dùng lại**, nên phải làm cẩn thận.

Bốn baseline:
- **B0 — Luật Wazuh**: dùng `wazuh_rule_*` có sẵn trong event. Đại diện "SIEM mua về, chưa tinh chỉnh".
- **B1 — TF-IDF + Logistic Regression**: đặc trưng văn bản từ chuỗi event, mô hình tuyến tính.
- **B2 — LightGBM** trên đặc trưng tổng hợp mức cửa sổ (aggregate features).
- **B3 — GRU thuần** (một lớp, không attention, không đa nhiệm): sàn tham chiếu cho Bước 6 để
  đo phần đóng góp của attention + đa nhiệm.

## 2. DỮ LIỆU ĐẦU VÀO (ĐÃ ĐÓNG BĂNG — KHÔNG ĐƯỢC TẠO LẠI)
Dùng ĐÚNG các file đã gắn tag `dataset-v1.0`. Không chạy lại normalize/label/split. Không fit
lại vocab. Nếu checksum khác `reports/dataset_stats.json` → DỪNG và báo.

- `data/processed/splits/train.jsonl`  — 479 cửa sổ (178 dương). CHỈ tập này được dùng để học + chọn ngưỡng/siêu tham số.
- `data/processed/splits/t_clean.jsonl` — 91 cửa sổ: test cùng phân phối.
- `data/processed/splits/t_hard.jsonl` — 87 cửa sổ, 0 dương: đo **false positive** trên hoạt động admin hợp lệ.
- `data/processed/splits/t_novel.jsonl` — 152 cửa sổ: holdout thời gian (batch05) + biến thể NTDS held-out (ntds2v).
- `data/processed/vocab.json` — vocab categorical, fit trên Train. Dùng y nguyên.
- Mỗi cửa sổ có: `window_id, run_id, batch, host, user_role, tempo, variant, t0, t1, n_events,
  window_malicious, window_ttps (list), window_class, events:[...]`. Mỗi event có 11 trường nguồn
  được phép (xem dataset_card mục 6–7).

### Nhãn cho hai bài toán
- **Phát hiện nhị phân**: `y = window_malicious` (0/1). Đây là bài chính để so B0–B3.
- **Đa nhãn TTP**: `y_ttp = window_ttps` trên 5 nhãn [T1016, T1018, T1087.002, T1654, T1003.003].
  B1/B2/B3 làm đa nhãn (one-vs-rest). B0 ánh xạ từ `wazuh_rule_mitre` (xem 4.1).

## 3. QUY TẮC CHỐNG RÒ RỈ (GIỮ NGUYÊN TỪ BƯỚC 4 — đây là điểm 9–10)
Tuyệt đối KHÔNG dùng làm feature cho B1/B2/B3: `wazuh_rule_*` (chỉ B0 dùng), `label_*`, `run_id`,
`window_id`, `event_uid`, `process_guid`, `parent_process_guid`, `script_block_text`, `ps_payload`,
đường dẫn tuyệt đối `image`/`parent_image`, và `n_events` (độ dài cửa sổ — xem 4.5 vì sao).
- Vocab cho B1/B3 chỉ fit trên Train. Không đọc t_clean/t_hard/t_novel khi học bất cứ thứ gì.
- IDF của B1 chỉ tính trên Train. Chuẩn hoá (scaler) của B2 chỉ fit trên Train.
- Chọn ngưỡng, chọn siêu tham số: CHỈ trên Train (dùng cross-validation theo nhóm run_id). Không
  bao giờ nhìn tập test để chỉnh.

## 4. ĐẶC TẢ TỪNG BASELINE

### 4.1 B0 — Luật Wazuh  → `src/baselines/b0_wazuh.py`
- Với mỗi cửa sổ: dự đoán dương nếu có ÍT NHẤT một event trong cửa sổ có `wazuh_rule_level >= L`.
- B0 không "học". Nhưng để công bằng, quét L trên Train (vd L in 3..12), chọn L tối đa hoá F1 trên
  Train, rồi KHOÁ L đó và báo cáo trên test. Ghi L đã chọn vào kết quả.
- Đa nhãn TTP: ánh xạ `wazuh_rule_mitre` (danh sách kỹ thuật Wazuh gắn) sang 5 TTP của ta. Cửa sổ
  được gán TTP t nếu có event mang rule mitre chứa t. TTP nào Wazuh không có luật → B0 mù (recall 0);
  nêu rõ trong phân tích, đây chính là lý do cần luật tự sinh ở Bước 7.
- Lưu ý: B0 là baseline "miễn phí" — đừng tinh chỉnh quá; mục đích là cho thấy sàn của SIEM thô.

### 4.2 B1 — TF-IDF + Logistic Regression  → `src/baselines/b1_tfidf_lr.py`
- Biểu diễn mỗi cửa sổ thành một "tài liệu": nối chuỗi token mỗi event theo thứ tự thời gian.
  Token mỗi event = `image_name` + `event_id` + các token của `command_line` đã chuẩn hoá
  (CHUẨN HOÁ GIỐNG featurize.py Bước 4: chữ thường, bỏ nháy, GUID/hex/số → ký hiệu). KHÔNG dùng
  text thô chưa chuẩn hoá (chứa dấu vết ART).
- TF-IDF char/word n-gram (word 1–2 gram là đủ), fit trên Train.
- **BẮT BUỘC chuẩn hoá theo độ dài**: TF-IDF đã chuẩn hoá L2 nên tương đối ổn, nhưng thêm biến thể
  B1-raw (đếm thô, không chuẩn hoá) để chứng minh bằng số rằng không chuẩn hoá thì mô hình học độ dài.
- LogisticRegression (class_weight="balanced"). Đa nhãn: one-vs-rest.

### 4.3 B2 — LightGBM trên đặc trưng tổng hợp  → `src/baselines/b2_lgbm.py`
- Mỗi cửa sổ → một vector tổng hợp (KHÔNG dùng thứ tự chuỗi):
  - Đếm theo `event_id` (chuẩn hoá theo số event trong cửa sổ → tỉ lệ, không phải số đếm thô).
  - Đếm theo `image_name` top-K (tỉ lệ). Số tiến trình phân biệt.
  - Tỉ lệ event có mạng, có DNS, kênh PowerShell, kênh Security.
  - Thống kê `dt` giữa các event: trung bình, độ lệch chuẩn.
  - host_role, user_role, tempo, variant (one-hot).
- **BẮT BUỘC**: mọi đặc trưng đếm phải chia cho số event trong cửa sổ (thành tỉ lệ). KHÔNG đưa số
  đếm tuyệt đối và KHÔNG đưa `n_events`. Nếu đưa, LightGBM sẽ học độ dài cửa sổ (xem 4.5).
- Nếu LightGBM không cài được trên host, fallback sang HistGradientBoosting của scikit-learn và ghi rõ.

### 4.4 B3 — GRU thuần  → `src/baselines/b3_gru.py`
- Chuỗi event (tối đa 64) → embedding categorical (dùng vocab.json) + nhánh command_line 256 chiều
  (giống featurize.py) → GRU một lớp (hidden 64–128) → lớp tuyến tính → sigmoid.
- Chỉ phát hiện nhị phân ở B3 (đa nhãn để Bước 6). KHÔNG attention, KHÔNG đa nhiệm — đó là điểm
  khác biệt mà Bước 6 sẽ thêm vào.
- **Padding mask** cho cửa sổ ngắn (<64). **Random length crop** khi huấn luyện (cắt ngẫu nhiên
  một đoạn liên tiếp) để mô hình không dựa vào độ dài — đây là biện pháp bắt buộc, xem 4.5.
- Huấn luyện nhẹ, chạy được trên CPU host (vài epoch). Nếu cần GPU, cho phép chạy Colab và tải
  trọng số về; nhưng B3 nên đủ nhỏ để chạy host. Seed 1337.

### 4.5 Vì sao cấm `n_events` và bắt chuẩn hoá theo độ dài
dataset_stats: tỉ lệ cửa sổ đủ 64 event lệch theo lớp — attack+ 74%, attack- 100%, benign- 53%,
hard_negative- 41%. Nếu để lọt độ dài vào feature, mọi baseline sẽ học "cửa sổ ngắn = hard-negative"
thay vì học hành vi, và sẽ sập trên T-hard thực tế. Mọi baseline phải trung lập với độ dài.

## 5. KHUNG ĐÁNH GIÁ DÙNG CHUNG  → `src/eval/evaluate.py` (QUAN TRỌNG NHẤT BƯỚC 5)
Mọi bước sau (B6 VT-Seq, B7 luật, B8 fusion) gọi lại module này. Thiết kế cho ổn định.

### 5.1 Báo cáo RIÊNG cho từng tập test
Với mỗi mô hình, in bảng cho **T-clean**, **T-hard**, **T-novel** riêng biệt (không gộp):
- **T-clean**: Precision, Recall, F1, PR-AUC, ROC-AUC cho nhị phân; macro-F1 và per-TTP F1 cho đa nhãn.
- **T-hard**: chỉ số chính là **FPR = số cửa sổ bị gắn dương / tổng** (tập này 0 dương, nên precision/recall
  không định nghĩa). Báo thêm **FPR theo từng chữ ký công cụ** (nhóm hard_negative theo `hn_signature`,
  đặc biệt các chữ ký chứa `cmd.exe`, `ntdsutil.exe`). Đây là nơi lộ đường tắt tên tiến trình.
- **T-novel**: như T-clean, nhưng **báo T1003.003 riêng theo từng phiên** (recall mức phiên: x/6 phiên
  ntds2v được phát hiện), KHÔNG chỉ báo F1 mức cửa sổ — vì chỉ 6 cửa sổ dương, F1 không có ý nghĩa
  thống kê. Nêu rõ điều này.

### 5.2 Ngưỡng
Chọn ngưỡng nhị phân trên Train (tối đa F1 bằng cross-validation theo nhóm run_id). KHOÁ ngưỡng,
áp y nguyên cho cả 3 tập test. Báo cáo cả ở ngưỡng cố định 0.5 để tham chiếu. Tuyệt đối không
chọn ngưỡng trên tập test.

### 5.3 Khoảng tin cậy (BẮT BUỘC — vì test nhỏ)
Mọi chỉ số kèm **khoảng tin cậy bootstrap 95%** (1000 lần lấy mẫu lại theo CỬA SỔ, seed 1337).
Riêng recall T1003.003 trên T-novel: bootstrap theo PHIÊN, không theo cửa sổ. Báo khoảng, không
chỉ điểm ước lượng. Test nhỏ nên hai mô hình chênh nhau vài phần trăm thường không có ý nghĩa — nói rõ.

### 5.4 Ablation (áp cho B2 và B3; là tiền đề cho yêu cầu (3) của môn học)
Chạy và lập bảng cho các cấu hình:
- (a) đầy đủ đặc trưng;
- (b) bỏ `image_name` + `parent_image_name` (chứng minh mô hình không chỉ đọc tên tiến trình);
- (c) chỉ dùng event trong cây tiến trình, che toàn bộ event nền (chứng minh không sống nhờ nhiễu
  nền như dịch vụ khởi động lại sau khôi phục snapshot — liên quan kiểm tra #10 ở dataset_card);
- So sánh (a) với (b),(c) trên cả T-clean và T-hard. Kỳ vọng: nếu (b) tụt nhiều trên T-hard tức
  mô hình đang dựa vào tên tiến trình — ghi nhận và bàn luận, không giấu.

### 5.5 Đầu ra
- `reports/step5_results.json`: mọi chỉ số, mọi tập, mọi ablation, kèm CI, ngưỡng đã chọn, seed.
- `reports/step5_report.md`: bảng người đọc được: (1) bảng chính B0–B3 × {T-clean, T-hard FPR,
  T-novel} cho nhị phân; (2) bảng per-TTP F1; (3) bảng ablation; (4) bảng recall T1003.003 mức phiên;
  (5) 3–5 câu nhận xét: baseline nào thắng ở đâu, dấu hiệu đường tắt, hệ quả cho Bước 6–7.
- Lưu dự đoán thô (xác suất mỗi cửa sổ) `reports/preds/<model>_<split>.jsonl` để Bước 8 fusion dùng lại.

## 6. QUY ƯỚC KHI CODE (giống Bước 1–4)
- Python chạy trên host (Windows, Python 3.12). scikit-learn, numpy được; LightGBM nếu cài được,
  không thì HistGradientBoosting. PyTorch cho B3 (CPU); nếu nặng, Colab rồi tải trọng số về.
- Mỗi script chạy độc lập, in thống kê rõ, seed cố định 1337.
- File chỉ ASCII. Đọc manifest (nếu cần) bằng utf-8-sig.
- Commit từng baseline. data/ bị gitignore; commit code + reports/.
- Làm từng baseline, chạy, in kết quả, cho người dùng xác nhận rồi mới sang baseline kế.
- KHÔNG sửa dataset. Nếu thấy nghi ngờ về dữ liệu, báo rồi dừng, đừng tự vá.

## 7. THỨ TỰ THỰC HIỆN ĐỀ NGHỊ
1. Viết `src/eval/evaluate.py` + `src/eval/bootstrap.py` TRƯỚC (khung đánh giá, test bằng mô hình
   giả ngẫu nhiên để chắc bảng và CI chạy đúng).
2. B0 (nhanh, cho thấy sàn SIEM).
3. B1, rồi B2 (kèm ablation).
4. B3 (kèm ablation nhị phân).
5. Viết `reports/step5_report.md`. Gửi người dùng `step5_report.md` + `step5_results.json` để soát
   trước khi sang Bước 6.

## 8. TIÊU CHÍ CHẤP NHẬN BƯỚC 5 (in ra, phải đạt)
- Không mô hình nào (trừ B0) chạm `wazuh_rule_*`, `label_*`, `run_id`, `n_events`, hay text thô.
- Vocab/IDF/scaler chỉ fit trên Train (assert bằng checksum vocab = dataset-v1.0).
- Ngưỡng và siêu tham số chọn trên Train; test chỉ chạy một lần với cấu hình đã khoá.
- Mọi chỉ số có CI bootstrap.
- Có đủ bảng: chính (3 tập), per-TTP, ablation (a/b/c), recall T1003.003 mức phiên.
- Mỗi cửa sổ test có đúng một dự đoán; không cửa sổ Train nào lọt vào test (đối chiếu run_id).

## 9. SAU BƯỚC 5 (để biết hướng, CHƯA làm)
Bước 6: VT-Seq (GRU-Attention đa nhiệm: nhị phân + đa nhãn TTP cùng lúc), ablation so B3 (thêm
attention, thêm đa nhiệm), huấn luyện Colab, xuất ONNX cho inference CPU. Bước 7: Auto Rule Engine
(cây quyết định/RIPPER trên đặc trưng B2 → luật Sigma có xuất xứ + quality gate kiểm trên T-hard).
Bước 8: Hybrid Fusion (hợp nhất điểm AI + luật), so với chỉ-AI và chỉ-luật dùng chính khung
`evaluate.py` này. Giữ nguyên định dạng `reports/preds/*.jsonl` để fusion dùng lại.
