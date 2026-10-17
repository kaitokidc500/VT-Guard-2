# VT-Guard — Bàn giao & đặc tả BƯỚC 8 (Hybrid Fusion: AI + luật tự sinh)

Tự chứa. Đọc cùng `reports/step6_report.md`, `reports/step7_report.md`, `src/eval/evaluate.py`,
`reports/preds/` (định dạng dự đoán chung), `rules/sigma/`, `src/rules/apply.py`, `models/` (ONNX).

## 0. Bối cảnh
Ba yêu cầu môn học: (1) luật tự sinh có xuất xứ + kiểm định — xong (Bước 7);
**(2) luật dùng chung với AI trong một bộ hợp nhất, so được với chỉ-luật và chỉ-AI — ĐÂY LÀ BƯỚC 8**;
(3) AI tùy biến có ablation — xong (Bước 6). Hạn 01/11/2026.

## 1. Kỳ vọng đúng
- Chỉ-AI (VT-Seq-ens): recall và đa nhãn tốt, T-hard 1/88. Chỉ-luật (11 luật): precision gần 1, T-hard 0/88,
  recall thấp hơn, đa nhãn yếu, nhưng minh bạch và có xuất xứ.
- Nhị phân đã gần trần. **Không kỳ vọng fusion tăng mạnh F1.** Giá trị cần chứng minh:
  (i) không kém chỉ-AI về recall và FPR; (ii) mỗi cảnh báo có giải thích (luật khớp và/hoặc event attention cao);
  (iii) nếu có, cải thiện đa nhãn ở TTP mà luật có tín hiệu rõ.

## 2. Đầu vào ĐÓNG BĂNG
- `dataset-v1.2` (kiểm checksum). Khung `evaluate.py` dùng nguyên, chỉ được THÊM chỉ số.
- **Học/chọn fusion CHỈ trên OOF của Train:**
  - AI: OOF của 5 seed M3 (mốc 2 Bước 6), ens = trung bình xác suất. Ghi rõ file nguồn.
  - Luật: `reports/preds/rules_oof_train.jsonl`. **Không dùng `rules_train.jsonl` (in-sample).**
- Test: `reports/preds/vtseq_ens_<split>.jsonl`, `reports/preds/rules_<split>.jsonl`.
- **Hạn chế đã biết phải xử lý:** bộ luật ở từng fold dễ dãi hơn bộ luật cuối (không có OOF lồng). Fusion học
  trên OOF có thể tin luật hơi khác lúc chạy test. Vì vậy ưu tiên fusion ít tham số (mục 3) và báo độ nhạy.

## 3. Các chiến lược fusion (đặt trước, số tham số ít)  → `src/fusion/fuse.py`
Ký hiệu: `p` = xác suất nhị phân của AI; `r` = 1 nếu có ít nhất một luật nhị phân khớp; `p_k`, `r_k` cho TTP k.
- **F0 chỉ-AI** và **F1 chỉ-luật**: tham chiếu, giữ nguyên ngưỡng đã khoá ở Bước 6 / Bước 7.
- **F2 OR**: cảnh báo nếu `p ≥ τ` hoặc `r = 1`. Đa nhãn: TTP k nếu `p_k ≥ τ_k` hoặc `r_k = 1`.
  Tham số: τ, τ_k (giữ ngưỡng chỉ-AI) — không học thêm.
- **F3 boost**: `s = max(p, r·c)` với c ∈ {1}; hoặc `s = p + β·r`, β chọn trên OOF trong lưới nhỏ {0,1; 0,2; 0,3}.
  Ngưỡng của `s` chọn theo FPR ≤ 1% trên cửa sổ âm OOF (cùng quy tắc Bước 6). Đa nhãn tương tự theo từng k.
- **F4 stacking nhẹ**: hồi quy logistic trên [logit(p), r, các r_k] (≤ 7 đặc trưng), huấn luyện trên OOF.
  Điểm OOF của chính F4 phải lấy bằng **CV theo nhóm phiên lồng trên OOF** (không chấm F4 trên dữ liệu nó vừa học).
  Ngưỡng theo FPR ≤ 1% trên OOF lồng.

## 4. Chọn cấu hình fusion — CHỈ trên OOF, khoá trước khi chạy test
- Tiêu chí theo thứ tự (giống Bước 6): (1) macro-F1 TTP OOF, (2) PR-AUC nhị phân OOF, (3) FPR OOF trên cửa sổ
  hard_negative. Hoà (chênh ≤ độ lệch chuẩn bootstrap) → chọn cấu hình **ít tham số hơn** (F2 < F3 < F4).
- Ghi `reports/step8/final_fusion.json` (chiến lược, tham số, ngưỡng, nguồn OOF), commit + push **trước** khi
  chạy test. Commit hash là bằng chứng chọn trước.
- Độ nhạy với hạn chế mục 2: báo kết quả OOF của cấu hình chọn khi thay luật fold bằng luật cuối (chỉ để mô tả,
  không dùng để chọn).

## 5. Đánh giá trên test (một lần)
- Chạy F0–F4 trên t_clean / t_hard / t_novel (F0–F3 không có tham số học trên test; F4 dùng mô hình đã khoá).
- Bảng giống Bước 5–7: T-clean F1; T-hard FPR (tổng, theo chữ ký, phân tầng độ dài, Spearman);
  T-novel F1 + PR-AUC; macro-F1 TTP + F1 theo TTP; phát hiện sớm k=4/8/16/32; T1003.003 theo phiên.
- **Paired bootstrap** (1000 lần) cho cấu hình fusion đã chọn so với F0 (chỉ-AI) và F1 (chỉ-luật), trên
  3 chỉ số: macro-F1 TTP T-novel, PR-AUC T-novel, FPR T-hard. Họ so sánh = 6 → **hiệu chỉnh Holm**.
  Chỉ tuyên bố "hơn" khi còn ý nghĩa sau Holm. "Không kém" (non-inferiority) báo bằng CI của hiệu số.
- Không chỉnh fusion theo test. Mọi kết quả xấu chỉ ghi vào hạn chế.

## 6. Giải thích cảnh báo (phục vụ yêu cầu (2) và dashboard)
Mỗi cửa sổ bị cảnh báo xuất một bản ghi → `reports/step8/alerts_<split>.jsonl`:
`window_id, host, t0, t1, score, decision_source ∈ {rule, ai, both}, ttps, rule_ids (kèm đường dẫn file Sigma
và provenance), attention_top5 (chỉ số event + trường quan sát được), threshold, fusion_config`.
Báo: tỉ lệ cảnh báo có ít nhất một luật giải thích; phân bố decision_source theo tập; ví dụ 3 cảnh báo
(một do luật, một do AI, một do cả hai).

## 7. Pipeline suy luận đầu-cuối  → `src/pipeline/infer.py`
- Đầu vào: một file cửa sổ cùng định dạng `windows.jsonl` (hoặc split). Các bước: featurize (vocab đã đóng băng)
  → ONNX VT-Seq-ens (`models/vtseq_ens.onnx`) → matcher Sigma (`src/rules/apply.py`) → fusion đã khoá →
  `alerts.jsonl` theo schema mục 6.
- Kiểm: kết quả `infer.py` trên 3 tập test **trùng** với kết quả chấm ở mục 5 (0 lệch).
- Đo độ trễ đầu-cuối trên host CPU (trung bình, p95, mỗi cửa sổ; batch 1 và 32).
- Đây là đầu vào cho dashboard ở bước sau.

## 8. Báo cáo  → `reports/step8_report.md` + `step8_results.json`
1. Bảng OOF F2–F4 và lý do chọn (mục 4).
2. Bảng test F0–F4 cạnh B0/B1/B2 (các cột như Bước 5–7).
3. Paired bootstrap + Holm (6 so sánh).
4. Giải thích cảnh báo (mục 6) và độ trễ pipeline (mục 7).
5. Thảo luận trung thực: fusion giúp ở đâu, không giúp ở đâu. Nếu fusion chỉ "không kém" chỉ-AI về điểm số,
   giá trị nằm ở giải thích được và xuất xứ của luật — nói rõ, không phóng đại.
6. Hạn chế: luật fold dễ dãi hơn luật cuối; T1003 test nhỏ; 2 host/1 domain; các hạn chế kế thừa Bước 4–7.

## 9. Tiêu chí chấp nhận
1. Checksum dataset khớp; fusion học/chọn chỉ trên OOF; không dùng `rules_train.jsonl`.
2. `final_fusion.json` commit trước khi chạy test.
3. Bảng test đủ F0–F4; paired bootstrap + Holm.
4. `alerts_<split>.jsonl` đủ schema; có tỉ lệ cảnh báo được luật giải thích.
5. `infer.py` trùng kết quả chấm (0 lệch) và có độ trễ.
6. `reports/preds/fusion_<split>.jsonl` cùng định dạng chung.

## 10. Thứ tự thực hiện (DỪNG mỗi mốc để người dùng duyệt)
1. `fuse.py` F0–F4 + unit test (chỉ đọc OOF cho học/chọn; F4 có CV lồng; ngưỡng FPR ≤ 1%). Bảng OOF + đề xuất
   cấu hình. **DỪNG.**
2. Ghi + commit `final_fusion.json`. Chạy test một lần, chấm, paired bootstrap + Holm. **DỪNG — gửi bảng.**
3. `alerts_<split>.jsonl` + `infer.py` + kiểm trùng + độ trễ. **DỪNG.**
4. `step8_report.md` + `step8_results.json`, cập nhật agent.md, commit, push, tag `step8-done`.

Seed 1337. ASCII trong code. Không sửa dataset, không dời tag, không chỉnh gì theo test.

## 11. Sau Bước 8
Dashboard (đọc `alerts.jsonl`: danh sách cảnh báo, nguồn quyết định, luật khớp, event attention) và báo cáo cuối.
