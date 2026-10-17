# VT-Guard — Bàn giao ngữ cảnh & đặc tả BƯỚC 6 (VT-Seq: GRU-Attention đa nhiệm)

Tài liệu tự chứa. Đọc cùng `reports/dataset_card.md`, `reports/step5_report.md`,
`src/eval/evaluate.py`, `src/baselines/b3_gru.py`. Không cần ngữ cảnh nào khác.

## 0. Bối cảnh (tóm tắt)
VT-Guard phát hiện hành vi APT kiểu Volt Typhoon trên log Windows (Wazuh, DC01 + WIN10-01),
đơn vị phát hiện = cửa sổ phiên (≤64 event), nhãn nhị phân + đa nhãn 5 TTP
(T1016, T1018, T1087.002, T1654, T1003.003). Ba yêu cầu môn học: (1) luật tự sinh có xuất xứ
+ kiểm định (Bước 7), (2) luật dùng chung với AI trong fusion (Bước 8), (3) **AI tùy biến biểu diễn
chuỗi event, có ablation so với baseline đơn giản — đây là Bước 6.** Hạn 01/11/2026.

## 1. Bài học từ Bước 5 (thiết kế Bước 6 dựa trên đây)
- Nhị phân và FPR T-hard **đã gần trần** ở baseline (B1: T-hard 0/88, T-novel F1 ~0,95). VT-Seq
  KHÔNG được kỳ vọng thắng rõ ở đây; chỉ cần **không kém** B1.
- Khoảng trống thật: **đa nhãn TTP trên T-novel** (tốt nhất B2 (a) 0,80; B3 0,74–0,76),
  đặc biệt **T1654** (0,46–0,61 ở mọi mô hình).
- **Bỏ `image_name` (ablation b) không làm B1/B3 kém đi, thậm chí tốt hơn**; B2 thì sụp. Tên công cụ
  là đường tắt gây kém tổng quát hoá.
- **Confounder độ dài**: B1 TF-IDF và B3 có Spearman(điểm, n_events) 0,5–0,8 trên cửa sổ âm.
- **Ngưỡng B3 không ổn định giữa seed** (0,51–0,95), làm phát hiện sớm T1003 dao động mạnh.
- B3: 3/120 fold CV chạm trần 60 epoch.

→ VT-Seq phải chứng minh giá trị ở: **(i) đa nhãn T-novel + T1654, (ii) bền khi không có tên công cụ,
(iii) trung lập với độ dài, (iv) ổn định giữa seed, (v) giải thích được (phục vụ Bước 7)**.

## 2. Đầu vào ĐÓNG BĂNG
- `dataset-v1.2` (tag). Kiểm checksum splits + vocab với `reports/dataset_stats.json` trước khi chạy;
  lệch → DỪNG.
- Khung đánh giá `src/eval/evaluate.py` (dùng y nguyên; được phép THÊM chỉ số, không sửa chỉ số cũ).
- Trường CẤM làm feature (giữ nguyên Bước 4–5): `wazuh_rule_*`, `label_*`, `run_id`, `window_id`,
  `event_uid`, `process_guid`, `parent_process_guid`, `script_block_text`, `ps_payload`, đường dẫn đầy đủ,
  `n_events`, `tempo`, `variant`, `user_role`, `batch`, `revert_control`. Acceptance #2 phải chạy cho VT-Seq.
- Nhãn từng event (`label_malicious`, `label_ttps`) CHỈ dùng để tính lại nhãn đoạn crop khi huấn luyện
  (như B3), không bao giờ là input.

## 3. Kiến trúc VT-Seq  → `src/models/vtseq.py` (MỘT nguồn code cho host và Colab)
**3.1 Bộ mã hoá event** (giống B3 để so sánh công bằng):
- Embedding cho 7 trường categorical (vocab.json): `channel, event_id, image_name, parent_image_name,
  host_role, integrity_level, logon_type` (dim 8–16 mỗi trường).
- Nhánh command-line: vector hash 256 chiều (f3) → Linear(256→64).
- 5 số (`dt_log`, cờ mạng/DNS/kênh) → nối thẳng.
- Nối tất cả → Linear → LayerNorm → vector event d=96.
- **Name dropout** (cấu hình): khi huấn luyện, thay `image_name` và `parent_image_name` bằng `<unk>`
  với xác suất p (theo cả cửa sổ). Lúc suy luận không drop. p ∈ {0, 0,5} trong ablation; (b) = drop luôn.

**3.2 Bộ mã hoá chuỗi**: GRU 1 lớp, hidden 96 (BẰNG B3, để ablation chỉ đổi một yếu tố).
Một chiều (causal) để hợp với phát hiện sớm/triển khai luồng. Mask padding bằng pack_padded_sequence.

**3.3 Attention pooling**: additive attention trên các output GRU có mask:
`e_t = v^T tanh(W h_t + b)`, `α = softmax(e)` (chỉ trên event thật), `c = Σ α_t h_t`.
Lưu α để giải thích (mục 6).

**3.4 Hai đầu (đa nhiệm)**: từ `c` (dropout 0,3):
- Đầu nhị phân: Linear→1 (sigmoid).
- Đầu TTP: Linear→5 (sigmoid độc lập).
- Loss = BCE_bin + λ·BCE_ttp (λ=1; pos_weight theo lớp tính trên Train).
- Ràng buộc nhất quán khi suy luận: báo cáo cả `p_bin` gốc và `p_bin' = max(p_bin, max_k p_ttp_k)`;
  chọn một trong hai bằng OOF (mục 4.3), không bằng test.

**3.5 Kiểm soát độ dài (bắt buộc)**: random contiguous crop như B3 (tính lại nhãn trên đoạn crop),
nhưng **độ dài crop lấy đều trong [4, L_window] cho MỌI lớp**, để phân bố độ dài giữa lớp dương/âm
gần như nhau trong dữ liệu huấn luyện. Báo Spearman(điểm, n_events) trên cửa sổ âm — mục tiêu |ρ| ≤ 0,2.

## 4. Huấn luyện & chọn cấu hình
**4.1 Siêu tham số mặc định**: AdamW lr 1e-3, weight_decay 1e-4, batch 32, dropout 0,3, grad clip 1,0,
max_epochs 100, early stopping patience 10 trên val loss của fold. Báo số fold chạm trần.

**4.2 CV**: 5-fold theo nhóm phiên trên Train (cùng cách nhóm của Bước 5). Mô hình cuối fit trên toàn
Train với số epoch = trung vị các fold.

**4.3 CHỌN cấu hình và ngưỡng CHỈ trên Train OOF — không nhìn test.** Tiêu chí OOF theo thứ tự:
(1) macro-F1 TTP OOF, (2) PR-AUC nhị phân OOF, (3) FPR OOF trên cửa sổ hard_negative.
Ngưỡng nhị phân chọn theo **FPR mục tiêu ≤ 1% trên cửa sổ âm OOF** (báo kèm ngưỡng max-F1 để tham chiếu).
Ngưỡng từng TTP: max-F1 OOF theo TTP. Test chạy MỘT lần với cấu hình đã khoá.

**4.4 Seed**: 5 seed (1337, 7, 42, 2024, 99). Báo trung bình ± độ lệch chuẩn. Thêm **VT-Seq-ens** =
trung bình xác suất 5 seed, ngưỡng chọn lại trên OOF trung bình — để giảm bất ổn ngưỡng.

## 5. Ablation (yêu cầu 3 của môn học)
**5.1 Chuỗi ablation kiến trúc** — mỗi bước chỉ đổi MỘT yếu tố, cùng hidden 96:

| Mã | Cấu hình | So với |
|---|---|---|
| M0 | B3 (GRU, last-state, đơn nhiệm) — dùng lại kết quả Bước 5 | — |
| M1 | + attention pooling (đơn nhiệm: bin và ttp huấn luyện riêng) | M0 |
| M2 | + đa nhiệm (một mạng, hai đầu) | M1 |
| M3 | + crop độ dài đều mọi lớp (3.5) | M2 |
| M4 | + name dropout p=0,5 | M3 |
| M4(b) | M3 nhưng bỏ hẳn `image_name`/`parent_image_name` | M3, M4 |

Cấu hình cuối = M3, M4 hoặc M4(b), **chọn theo OOF (4.3)**. Gọi là **VT-Seq**.

**5.2 Ablation đặc trưng cho VT-Seq cuối**: (a) đủ / (b) bỏ tên công cụ / (c) chỉ cây tiến trình (CHỈ báo
T-hard, so tương đối với (a)) / (c′) che event nền một-phía đã biết. Như Bước 5.

**5.3 So sánh có ý nghĩa thống kê**: với VT-Seq-ens so với B1 TF-IDF (b), B2 (a), B3 (b): **paired bootstrap**
(1000 lần, cùng chỉ số mẫu cho hai mô hình) cho hiệu số macro-F1 TTP T-novel, PR-AUC T-novel, FPR T-hard.
Báo CI của hiệu số; chỉ tuyên bố "hơn" khi CI không chứa 0.

## 6. Giải thích bằng attention (đầu vào cho Bước 7)  — SỬA 2026-10-17, chạy TRÊN HOST
- **Hạt giống luật cho Bước 7 = CHỈ TRAIN**: thống kê token lệnh / `image_name` / `event_id` theo TTP, tính bằng
  **attention OOF** (mỗi cửa sổ Train lấy α từ mô hình fold KHÔNG thấy nó khi huấn luyện)
  → `reports/step6/rule_seeds_train.json`. **KHÔNG dùng cửa sổ test làm hạt giống luật.**
- **Attention trên test chỉ để giải thích**: top-5 event cho cửa sổ dương được phát hiện ở T-clean/T-novel, kèm
  `image_name, parent_image_name, event_id, channel` và command line đã chuẩn hoá (canon); với ens dùng α trung bình
  5 seed → `reports/step6/attention_topk_test.jsonl`.
- **Faithfulness** (ens và từng seed): xoá top-k event theo α vs xoá k event ngẫu nhiên (lặp 10 lần), k=1/3/5,
  CÙNG số event bị xoá ở hai nhánh; đo mức giảm `p_bin` và `p_ttp` của đúng TTP của cửa sổ; báo CI bootstrap của
  hiệu số. Attention chỉ được gọi là "giải thích" nếu xoá top-k làm giảm điểm nhiều hơn xoá ngẫu nhiên có ý nghĩa.
- **ONNX** (mục 7): một seed đại diện VÀ ens (một đồ thị bọc 5 mô hình, đầu ra = trung bình xác suất + α trung bình),
  opset ≥ 17, dynamic batch + độ dài; parity với PyTorch < 1e-4 trên toàn T-novel; độ trễ CPU đo trên host
  (trung bình + p95 mỗi cửa sổ, batch 1 và batch 32).

## 7. Colab + xuất ONNX
- **Chỉ đưa lên Colab**: `data/processed/splits/*.jsonl`, `vocab.json`, và repo code (git clone theo commit).
  KHÔNG đưa log thô. Ghi commit hash + checksum vào kết quả.
- Notebook `notebooks/step6_vtseq_colab.ipynb` chỉ gọi hàm trong `src/models/vtseq.py` (không chép code).
  Đầu ra tải về: checkpoint `.pt` từng seed, `oof_*.jsonl`, `preds/<model>_<split>.jsonl`, log huấn luyện.
- **Chấm điểm luôn bằng `evaluate.py` trên host** (như Bước 5), không chấm trên Colab.
- **ONNX**: xuất VT-Seq cuối (một seed đại diện + ens nếu khả thi) sang `models/vtseq.onnx` (opset ≥ 17,
  dynamic axis cho batch và độ dài). Kiểm: sai khác tối đa giữa PyTorch và ONNX Runtime < 1e-4 trên toàn
  T-novel; đo độ trễ CPU trung bình mỗi cửa sổ trên host. ONNX phải xuất được cả trọng số attention.

## 8. Báo cáo  → `reports/step6_report.md` + `reports/step6_results.json`
Bảng giống Bước 5 (cột y hệt để đặt cạnh nhau), thêm:
1. Chuỗi ablation M0→M4(b): OOF và test, mỗi ô trung bình ± độ lệch chuẩn 5 seed.
2. VT-Seq cuối + VT-Seq-ens cạnh B0/B1/B2/B3: bảng chính, F1 theo TTP, phát hiện sớm k=4/8/16/32,
   T-hard (tổng/chữ ký/cmd/độ dài/Spearman), T1003 theo phiên (nhị phân / nhãn TTP).
3. Paired bootstrap so với baseline (5.3).
4. Ổn định: độ lệch chuẩn ngưỡng và chỉ số giữa seed (so với B3).
5. Faithfulness của attention + top token theo TTP.
6. ONNX: sai khác, độ trễ.
7. Thảo luận trung thực: VT-Seq hơn/không hơn ở đâu. Nếu không hơn B1 ở nhị phân, nói rõ và
   lập luận giá trị ở đa nhãn, ổn định, độ bền (b), độ dài, và giải thích.

## 9. Tiêu chí chấp nhận Bước 6
1. Checksum dataset-v1.2 khớp; acceptance #2 (trường cấm) đạt cho VT-Seq.
2. Cấu hình, ngưỡng, λ, lựa chọn `p_bin` vs `p_bin'` đều chọn trên Train OOF; test chạy một lần.
3. ≥ 5 seed; báo trung bình ± độ lệch chuẩn; có VT-Seq-ens.
4. Đủ chuỗi ablation M0→M4(b) và ablation đặc trưng (a)(b)(c)(c′).
5. Paired bootstrap cho mọi tuyên bố "hơn baseline".
6. Faithfulness attention có số liệu.
7. ONNX parity < 1e-4; có độ trễ CPU.
8. `reports/preds/vtseq*_<split>.jsonl` (cùng định dạng Bước 5) cho Bước 8.

## 10. Thứ tự thực hiện (DỪNG ở mỗi mốc để người dùng duyệt)
1. `src/models/vtseq.py` + unit test nhanh trên host (vài batch, 2 epoch): shape, mask, attention tổng = 1,
   nhãn crop tính lại đúng, không đọc trường cấm. Notebook Colab. **DỪNG.**
2. Chuỗi ablation M1→M4(b) trên Colab (5 seed, CV 5-fold). Bảng OOF. Chọn cấu hình cuối theo 4.3. **DỪNG.**
3. Chạy VT-Seq cuối trên test (một lần) + ablation đặc trưng + ens. Chấm bằng evaluate.py trên host.
   Paired bootstrap. **DỪNG.**
4. Attention top-k + faithfulness. ONNX export + parity + độ trễ. **DỪNG.**
5. `step6_report.md` + `step6_results.json`. Commit, push, tag `step6-done`.

Ước lượng thời gian: tối đa 3 ngày. Nếu chuỗi ablation trên Colab quá lâu, giảm còn 3 seed cho M1–M3
và giữ 5 seed cho cấu hình cuối; ghi rõ.

## 11. Quy ước
- Code ASCII; seed cố định; mỗi script chạy độc lập, in thống kê rõ.
- Không sửa dataset-v1.2, không dời tag. Không chọn gì trên test.
- Commit từng mốc. data/ và checkpoint lớn không vào git (ghi checksum + nơi lưu).

## 12. Sau Bước 6 (để biết hướng)
Bước 7: Auto Rule Engine — sinh luật (cây quyết định/RIPPER trên đặc trưng B2 + hạt giống attention mục 6)
→ Sigma, có xuất xứ (cửa sổ/phiên sinh ra luật) và quality gate (FPR trên T-hard, độ phủ trên T-novel).
Bước 8: Hybrid Fusion (điểm VT-Seq + luật), so với chỉ-AI và chỉ-luật bằng cùng evaluate.py và preds.
