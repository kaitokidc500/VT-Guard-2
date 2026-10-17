# VT-Guard — Bàn giao & đặc tả BƯỚC 7 (Auto Rule Engine: luật tự sinh → Sigma)

Tự chứa. Đọc cùng `reports/dataset_card.md`, `reports/step5_report.md`, `reports/step6_report.md`,
`reports/step6/rule_seeds_train.json`, `reports/step6/m4_explain.md`, `src/eval/evaluate.py`,
`src/baselines/b2_lgbm.py` (đặc trưng tỉ lệ theo cửa sổ).

## 0. Bối cảnh
VT-Guard, phát hiện APT kiểu Volt Typhoon trên log Windows (Wazuh), đơn vị = cửa sổ phiên (≤64 event),
nhãn nhị phân + đa nhãn 5 TTP. Ba yêu cầu môn học: **(1) luật tự sinh có xuất xứ + kiểm định — ĐÂY LÀ
BƯỚC 7**, (2) luật dùng chung AI trong fusion (Bước 8), (3) AI tùy biến có ablation (xong, Bước 6).
Hạn 01/11/2026.

## 1. Mục tiêu Bước 7
Sinh **tự động** một tập luật phát hiện, mỗi luật:
- **induced từ dữ liệu** (không viết tay), chỉ từ **Train**;
- có **xuất xứ** (provenance): truy được về cửa sổ/phiên Train sinh ra nó, đặc trưng và ngưỡng, support/precision trên Train;
- qua **quality gate**: đạt ngưỡng chất lượng trên Train/OOF, rồi được **kiểm định** trên T-hard (FPR) và
  T-novel (độ phủ) — hai tập này CHỈ để đánh giá, không bao giờ dùng để sinh hay chỉnh luật;
- xuất ra **Sigma** (YAML) hợp lệ, chạy được trên telemetry thật, có thể kiểm toán;
- là một bộ phát hiện "chỉ-luật" (rule-only), chấm bằng `evaluate.py` như mọi mô hình, để Bước 8 so sánh
  chỉ-luật / chỉ-AI / fusion. Lưu `reports/preds/rules_<split>.jsonl` cùng định dạng Bước 5–6.

Đây KHÔNG phải thay thế AI. Đây là nhánh luật minh bạch, bổ sung cho AI ở Bước 8.

## 2. Đầu vào ĐÓNG BĂNG
- `dataset-v1.2` (tag). Kiểm checksum splits + vocab trước khi chạy; lệch → DỪNG.
- Đặc trưng: dùng lại bộ đặc trưng **tỉ lệ theo cửa sổ** của B2 (đã bỏ `n_events`, đã bỏ
  `tempo/variant/user_role`), CỘNG các vị từ nhị phân "có mặt token/công cụ" suy từ hạt giống attention.
- Hạt giống: `reports/step6/rule_seeds_train.json` (attention OOF trên Train, theo TTP).
- Trường CẤM làm vị từ luật (y như Bước 4–6): `wazuh_rule_*`, `label_*`, `run_id`, `window_id`,
  `process_guid`, `n_events`, `tempo`, `variant`, `user_role`, đường dẫn đầy đủ. Luật chỉ được key trên
  telemetry quan sát được: `image_name`, token dòng lệnh đã chuẩn hoá (canon f3), `event_id`, `channel`,
  `parent_image_name` (đã gộp `<launcher>`), các cờ mạng/DNS.

## 3. DANH SÁCH CẤM theo cảnh báo scaffold (bắt buộc — đây là điểm 9–10)
Luật KHÔNG được dựa chủ yếu vào bất kỳ vị từ nào sau đây (dấu vết bộ sinh, không phải hành vi):
1. `\windows\temp\ntds_t0*` và mọi chuỗi chứa mã kỹ thuật/đường dẫn mặc định của ART → loại khỏi vị từ.
2. Sự hiện diện trần của `cmd.exe` / `cmd /c` làm điều kiện chính → luật phải key trên **lệnh con** (ntdsutil,
   nltest, wevtutil, nslookup, net …) và tham số, không phải lớp vỏ cmd.
3. `<launcher>` / `powershell.exe` như điều kiện cho T1087.002 → thay bằng lệnh thật
   (`net user /domain`, `adsisearcher`, `objectcategory`).
4. Event nền một phía cho T1003.003 (ESENT/Directory Service, `vssvc.exe`) làm điều kiện → luật T1003 key
   trên hành vi trong cây tiến trình (`ntdsutil ... ifm ... create full`, `vssadmin ... create shadow`).
`featurize`/engine phải assert mỗi luật cuối không chứa vị từ cấm; luật vi phạm bị loại và ghi lý do.

## 4. Phương pháp sinh luật  → `src/rules/induce.py`
**4.1 Mô hình quy nạp luật** (một-đối-còn-lại cho từng TTP + một cho nhị phân):
- Dùng **cây quyết định nông** (sklearn `DecisionTreeClassifier`, max_depth 3–4, min_samples_leaf ≥ 10)
  HOẶC RIPPER (`wittgenstein`) nếu cài được; chọn bằng macro-F1 OOF trên Train, ghi rõ engine đã dùng.
- Huấn luyện CHỈ trên Train. Mỗi lá/quy tắc dương → một luật ứng viên.
- Vị từ rút từ: đặc trưng tỉ lệ B2 (ngưỡng hoá: "tỉ lệ event mang token X ≥ t") và vị từ có-mặt từ hạt giống.
  Ưu tiên token hành vi trong `rule_seeds_train.json` có lift cao và % rơi vào event nền thấp.

**4.2 Lượng hoá vị từ cho Sigma**: cây cho ngưỡng trên tỉ lệ; chuyển sang vị từ Sigma dạng "trong cửa sổ
có ≥1 event thoả (image=... AND command_line chứa ...)". Ghi lại ánh xạ ngưỡng→vị từ trong provenance.

**4.3 Provenance mỗi luật** (`reports/step7/rules_provenance.json`): id luật, TTP, vị từ, các cửa sổ/phiên
Train khớp (support), precision/recall trên Train và OOF, hạt giống attention liên quan, engine + tham số,
seed. Không có xuất xứ → không xuất luật.

## 5. Quality gate (hai tầng, thứ tự cố định)
**Tầng 1 — Train/OOF (để GIỮ hay LOẠI luật):**
- precision OOF ≥ 0,9 và support Train ≥ 10 cửa sổ; nếu không đạt → loại.
- không chứa vị từ cấm (mục 3) → nếu chứa, loại và ghi lý do.
- khử trùng: nếu hai luật cùng TTP phủ gần hết cùng tập cửa sổ (Jaccard ≥ 0,8), giữ luật precision cao hơn.

**Tầng 2 — kiểm định trên tập test (chỉ ĐO, không chỉnh luật):**
- T-hard: FPR của toàn bộ luật (mục tiêu ≤ mức B1, tức ~0/88); báo FPR theo chữ ký công cụ.
- T-novel: độ phủ (recall) theo TTP và theo phiên cho T1003.003.
- Nếu một luật làm FPR T-hard tăng, KHÔNG được chỉnh luật theo T-hard; chỉ ghi vào hạn chế, hoặc quay lại
  Tầng 1 siết precision OOF rồi sinh lại (vẫn chỉ dùng Train). Ghi rõ mọi vòng lặp.

## 6. Xuất Sigma  → `rules/sigma/*.yml`
- Mỗi luật một file Sigma hợp lệ: `title, id (uuid), status: experimental, description (gồm TTP + xuất xứ),
  logsource` (windows, sysmon hoặc security tuỳ event_id), `detection` (selection + condition), `level`,
  `tags` (attack.txxxx), `falsepositives`, `fields`.
- Kiểm cú pháp bằng `sigma` CLI hoặc `pySigma` nếu cài được; nếu không, validate bằng schema YAML tối thiểu
  và ghi rõ công cụ. Mỗi file ghi `vtguard_provenance` trong custom field (id luật → provenance ở mục 4.3).
- Một bộ chuyển Sigma→matcher nội bộ (`src/rules/apply.py`) để chấm trên windows.jsonl, đảm bảo luật Sigma
  và bộ chấm dùng chung một ngữ nghĩa. Kiểm: matcher nội bộ và điều kiện cây cho cùng kết quả trên Train.

## 7. Bộ phát hiện chỉ-luật và báo cáo
- `src/rules/apply.py` áp toàn bộ luật lên mỗi cửa sổ: nhị phân = có luật nào khớp; đa nhãn = hợp TTP các
  luật khớp. Xuất `reports/preds/rules_<split>.jsonl` (cùng định dạng Bước 5–6, có điểm = tỉ lệ luật khớp
  hoặc max confidence, để Bước 8 fusion dùng).
- `reports/step7_report.md` + `step7_results.json`:
  1. Danh sách luật (id, TTP, vị từ, support/precision Train/OOF, xuất xứ tóm tắt).
  2. Bảng chỉ-luật cạnh B0, B1, B2, VT-Seq-ens: T-clean F1, T-hard FPR (tổng + chữ ký), T-novel F1 + theo TTP,
     T1003 theo phiên. (Luật đơn giản sẽ kém AI về recall — điều đó bình thường; giá trị là minh bạch + FPR thấp.)
  3. So với B0 (luật Wazuh có sẵn): luật tự sinh có phủ được các TTP mà B0 mù không (T1016/T1654/T1003)?
  4. Số luật bị loại ở mỗi cổng và lý do (đặc biệt số luật loại vì chứa vị từ cấm scaffold).
  5. Hạn chế: luật induced từ 2 host/1 domain; coverage gap đã biết; T1003 test nhỏ.

## 8. Tiêu chí chấp nhận
1. Checksum dataset-v1.2 khớp; luật chỉ induced từ Train; test chỉ để đo.
2. Mỗi luật xuất ra có provenance đầy đủ và KHÔNG chứa vị từ cấm (assert tự động, in 0 vi phạm).
3. Sigma hợp lệ cú pháp; matcher nội bộ ≡ điều kiện cây trên Train.
4. Có bảng chỉ-luật trên cả 3 tập test + so với B0 + so với AI.
5. `reports/preds/rules_<split>.jsonl` sẵn cho Bước 8.
6. Báo số luật loại theo từng cổng, gồm cổng vị từ cấm.

## 9. Thứ tự thực hiện (DỪNG mỗi mốc để người dùng duyệt)
1. `src/rules/induce.py` + danh sách vị từ cấm + unit test (chỉ đọc Train; vị từ cấm bị chặn; matcher ≡ cây).
   Sinh luật ứng viên + provenance, in bảng precision/support OOF và danh sách loại. **DỪNG — gửi tôi danh sách luật.**
2. Sau khi tôi duyệt tập luật: xuất Sigma + validate, áp lên 3 tập, chấm bằng evaluate.py, bảng so sánh,
   `rules_<split>.jsonl`. **DỪNG — gửi tôi bảng + vài file Sigma mẫu.**
3. `step7_report.md` + `step7_results.json`, commit, push, tag `step7-done`.

Seed 1337. ASCII. Không sửa dataset. Không chỉnh luật theo test.

## 10. Sau Bước 7
Bước 8 (Hybrid Fusion): hợp nhất điểm VT-Seq-ens + điểm chỉ-luật (vd luật tăng độ tin/đổi ngưỡng, hoặc
fusion học nhẹ trên OOF), so chỉ-AI / chỉ-luật / fusion bằng cùng `evaluate.py` và `reports/preds/`.
Mục tiêu fusion: giữ recall của AI, giảm FP nhờ luật precision cao, và có nhánh giải thích được bằng luật khớp.
