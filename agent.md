# agent.md — Bộ nhớ ngữ cảnh cho AI agent

> File này là "trí nhớ" của dự án giữa các phiên làm việc.
> - **Đầu phiên:** đọc toàn bộ file này (đặc biệt mục 3, 6, 7) trước khi làm bất cứ việc gì.
> - **Cuối phiên:** cập nhật mục 3 (Trạng thái), mục 6 (Nhật ký), mục 7 (Việc tiếp theo), rồi commit và push (xem mục 5).

---

## 1. Tổng quan dự án

- **Tên:** VT-Guard (research)
- **Repo:** https://github.com/kaitokidc500/VT-Guard-2 — nhánh `main`
- **Thư mục cục bộ:** `G:\VT-Guard` (chính là thư mục gốc `vt-guard-research/` trong sơ đồ thiết kế)
- **Pipeline (suy ra từ cấu trúc thư mục):**
  kéo JSON từ Indexer → chuẩn hoá → gán nhãn → cắt cửa sổ, chia tập → mô hình (Bước 5–6) → luật (Bước 7) → kết hợp/fusion (Bước 8); kiểm thử ngoài trên dataset công khai.
- **Huấn luyện:** Google Colab (`notebooks/`).
- **Đề tài:** báo cáo môn Giám sát an ninh mạng — phát hiện APT (Volt Typhoon) kết hợp AI (GRU-Attention)
  và luật tự sinh. Hạ tầng Wazuh: DC01 + WIN10-01 → Indexer. 5 TTP: T1016, T1018, T1087.002, T1654, T1003.003.
  Hạn 01/11/2026. Đặc tả Bước 4 và ngữ cảnh chi tiết: `docs/STEP4-BRIEF.md`; dataset: `reports/dataset_card.md`.

## 2. Cấu trúc thư mục

```
VT-Guard/  (= vt-guard-research/)
├─ data/                # KHÔNG đưa lên git (xem .gitignore), chỉ giữ .gitkeep
│  ├─ raw/              # JSON kéo từ Indexer (bất biến, không sửa tay)
│  ├─ interim/          # đã chuẩn hoá
│  ├─ processed/        # cửa sổ đã cắt, đã chia tập
│  └─ external/         # dataset công khai làm test ngoài
├─ manifests/           # bản kê mỗi phiên chạy
├─ orchestrator/        # bộ điều phối sinh phiên (Bước 2)
├─ src/                 # Python package (có __init__.py)
│  ├─ normalize/        # Bước 4
│  ├─ label/            # Bước 4
│  ├─ dataset/          # cắt cửa sổ, chia tập
│  ├─ models/           # Bước 5–6
│  ├─ rules/            # Bước 7
│  └─ fusion/           # Bước 8
├─ notebooks/           # huấn luyện Colab
├─ evidence/            # bằng chứng hạ tầng
├─ reports/             # viết báo cáo song song
├─ agent.md             # file này
├─ CLAUDE.md            # tự động nạp agent.md cho Claude Code
└─ README.md
```

## 3. Trạng thái pipeline

| Bước | Nội dung | Thư mục | Trạng thái |
|------|----------|---------|------------|
| 1 | Hạ tầng Wazuh (DC01, WIN10-01 → Indexer) | `evidence/` | Hoàn thành |
| 2 | Bộ điều phối sinh phiên, thu thập 479 phiên (10 đợt) | `orchestrator/`, `manifests/` | Hoàn thành |
| 3 | Chuẩn hoá & gán nhãn (normalize v1, labeler v8) | `src/normalize/`, `src/label/` | Hoàn thành |
| 4 | Đóng băng dataset (tag `dataset-v1.2`, thay v1.1/v1.0 — bản sửa dataset CUỐI): gộp, cửa sổ, đặc trưng, chia tập, dataset card | `src/dataset/`, `reports/` | Hoàn thành |
| 5 | Khung đánh giá (`src/eval/`), baseline B0–B3 (`src/baselines/`) + ablation; tổng hợp `reports/step5_report.md` (tag `step5-done`) | `src/eval/`, `src/baselines/`, `reports/` | Hoàn thành |
| 6 | VT-Seq (GRU-Attention đa nhiệm) + ablation; `reports/step6_report.md` (tag `step6-done`); triển khai = VT-Seq-ens (M3, 5 seed) | `src/models/`, `notebooks/`, `reports/step6/` | Hoàn thành |
| 7 | Auto Rule Engine: 11 luật tự sinh (RIPPER, chỉ Train) → Sigma `rules/sigma/`; `reports/step7_report.md` (tag `step7-done`) | `src/rules/`, `rules/sigma/` | Hoàn thành |
| 8 | Fusion | `src/fusion/` | Chưa bắt đầu |
| — | Bằng chứng hạ tầng | `evidence/` | Chưa bắt đầu |
| — | Báo cáo (song song) | `reports/` | Chưa bắt đầu |

Giá trị trạng thái: `Chưa bắt đầu` · `Đang làm` · `Hoàn thành` · `Tạm dừng`.

## 4. Quy ước

- `data/` không commit lên git (dữ liệu lớn/nhạy cảm). Lưu cục bộ hoặc Google Drive; ghi nguồn gốc trong `manifests/`.
- Dữ liệu đi một chiều: `raw → interim → processed`. Không chỉnh sửa tay `data/raw/`.
- Mỗi phiên chạy của orchestrator ghi một bản kê vào `manifests/` (schema sẽ chốt ở Bước 2).
- Notebook Colab import code từ `src/` thay vì chép code vào notebook.
- Không commit secrets: `.env`, thông tin đăng nhập Indexer, token.
- **Dataset đóng băng `dataset-v1.2` (git tag, thay v1.1/v1.0; bản sửa dataset CUỐI — bất đối xứng mới chỉ ghi hạn chế + ablation):** Bước 5–8 dùng ĐÚNG `data/processed/splits/{train,t_clean,t_hard,t_novel}.jsonl`,
  `data/processed/vocab.json` (bản sao `reports/vocab.json`); trước khi chạy, so sha256 với `reports/dataset_card.md` mục 10
  (`src/eval/evaluate.py: check_dataset` tự so). Không chạy lại split/featurize/label trên bản này; muốn đổi dữ liệu thì tạo
  phiên bản mới. Bản cũ lưu cục bộ ở `data/processed/v1.0/`, `data/processed/v1.1/` (nhãn v7: `data/processed/v7/`, normalize v0: `data/interim/v0/`).
- KHÔNG dời/force-push tag dataset đã đẩy; cần sửa thì tạo tag mới.

## 5. Quy trình mỗi phiên làm việc

**Bắt đầu phiên**
1. Đọc `agent.md`.
2. `git pull origin main` để đồng bộ.

**Kết thúc phiên** (khi người dùng báo kết thúc, hoặc sau một phần việc đáng kể)
1. Cập nhật bảng ở mục 3.
2. Thêm một mục mới vào mục 6: ngày, việc đã làm, quyết định quan trọng, vấn đề tồn đọng.
3. Cập nhật mục 7.
4. `git add -A` → `git commit -m "<mô tả ngắn>"` → `git push origin main`.

## 6. Nhật ký tiến trình

### Phiên 1 — 2026-10-12
- Tạo khung thư mục theo thiết kế; `src/*` là Python package, thư mục rỗng khác giữ bằng `.gitkeep`.
- Thêm `agent.md`, `CLAUDE.md` (dòng `@agent.md` để Claude Code tự nạp ngữ cảnh), `README.md`, `.gitignore`, `.gitattributes`.
- Khởi tạo git, nối remote `origin` tới VT-Guard-2, push lần đầu lên `main`.
- Quyết định: gốc repo = `G:\VT-Guard`; nội dung `data/` bị loại khỏi git.

### Phiên Bước 4 — 2026-10-15
- Làm Bước 4 theo `docs/STEP4-BRIEF.md`, từng bước con có xác nhận của người dùng:
  `src/dataset/merge.py` (4.1) → `windows.py` (4.2) → `featurize.py` (4.3) → `split.py` (4.4) → `card.py` (4.5).
- Phát hiện và chặn rò rỉ ở **labeler v5** (`src/label/label.py`), gán nhãn lại 6 đợt:
  scp/ssh upload manifest bị v4 gán nhầm malicious T1003.003 (72 event = 35% event NTDS);
  console PowerShell người vận hành gọi ART/VT (2 415 event); mảnh vỡ 4103 mất PID chứa text ART (680 event).
  Đối chiếu từng event v4↔v5: không event nào khác đổi nhãn. Nhãn v4 giữ ở `data/processed/v4/`.
- Quyết định khác brief: bỏ `smoke6`; khoá khử trùng lặp thêm `channel` + `ts_system` (snapshot DC01 làm record_id
  quay lui); thời gian theo `ts_system` (ts Wazuh trễ tới ~85 s); stream phiên không lấy event của phiên song song;
  lấy mẫu K=8 phân tầng dương/âm; vocab chỉ token xuất hiện ở ≥2 phiên Train; T-hard chọn theo nhóm thuần
  hard_negative; gom phiên chồng thời gian thành nhóm để Train và tập kiểm thử không chung event nền.
- Kết quả: 41 901 event → 713 cửa sổ (243 dương). Train 396 · T-clean 108 · T-hard 63 · T-novel 146.
  Kiểm thử chấp nhận cuối: ĐẠT (xem `reports/dataset_card.md` mục 8).
- Tồn đọng: xem mục 7 và mục "Hạn chế" của dataset card.

### Phiên Bước 4 (chạy lại) — 2026-10-15
- Thêm 3 đợt: `batch06` (27 hard-negative: ping/wevtutil/ntdsutil hợp lệ), `ntds2` (15 phiên T1003.003 test 3),
  `ntds2v` (6 phiên T1003.003 test 1, vssadmin shadow copy).
- **Labeler v6**: event không có `process_guid` chỉ ghép vào tiến trình khi `ts_system` nằm trong vòng đời [EID1, EID5].
  Lý do: khôi phục snapshot làm đồng hồ DC01 lệch ~55 phút; v5 (PID ±300 s theo giờ Wazuh) gán nhầm 204 event PowerShell
  (pid 1112, nạp module CIM) thành malicious T1003.003 ở phiên `20261015-084208-dc01-a`. Đối chiếu v5↔v6: chỉ 231 event ở ntds2 đổi.
  Nhãn v5 giữ ở `data/processed/v5/`.
- Loại 3 phiên attack labeled=0 (atomic không sinh tiến trình con): `20261014-164113`, `20261015-075708`, `20261015-084801` (dc01-a), không coi là benign.
- T-novel = batch05 + ntds2v (`NOVEL_BATCHES` trong `src/dataset/windows.py`); ntds2 chia Train/T-clean; batch06 theo quy tắc T-hard.
- Kết quả: 52 165 event → 778 cửa sổ (278 dương). Train 413 · T-clean 132 · T-hard 82 · T-novel 151. 8 kiểm tra chấp nhận: ĐẠT.
- Card bổ sung bảng T1003.003 theo tập và coverage theo công cụ: không công cụ nào chỉ ở phía dương trên toàn bộ dữ liệu,
  nhưng trong Train `ntdsutil.exe` vẫn chỉ ở phía dương; `route.exe`/`netstat.exe` chỉ ở phía âm (đường tắt ngược).

### Phiên batch07 — 2026-10-15
- Orchestrator: `orchestrator/benign/` (admin_net_diag mới; dc_db_maint, admin_net_sweep dựng lại từ log 4104, gọi tool qua
  `cmd.exe /c`), `Invoke-Batch07.ps1` (Loop + DbMaintSnapshot). Sửa `Invoke-VTSession.ps1`: `<test#>` đóng sớm khối `<# #>`
  -> đổi sang chú thích `#`, ASCII, CRLF; `.gitattributes` thêm `*.ps1 eol=crlf`. Cả 10 file .ps1 parse không lỗi.
  Lưu ý: repo có `orchestrator/begin/` (cũ) và `orchestrator/benign/` (mới); bản trên lab có thể khác repo.
- **Labeler v7**: (1) phiên = đúng [t_start, t_end] manifest ±5 s theo `ts_system`; con orchestrator ngoài khung ->
  `orch_child_outside`. v4–v6 gán theo giờ Wazuh (trễ 40–60 s) + kéo khung tới phiên kế: 102 event attack bị gán nhãn
  benign/HN của phiên kế tiếp; lệnh người vận hành (w32tm, VMwareToolboxCmd) bị gán vào phiên (122828-dc01-h: 61 -> 45).
  (2) nạp manifest đợt bên cạnh khi khung phiên giao ±10 phút: phiên ntds2v 084801 có 8 event nằm trong file ntds2
  (export cắt theo giờ Wazuh) -> không còn bị loại. Đối chiếu v6↔v7: 400 event đổi. Nhãn v6 ở `data/processed/v6/`.
  Lệnh gán nhãn: `label.py <norm> manifests/<b>,manifests/<đợt khác>... <out>`.
- Quy tắc chung: hard_negative labeled=0 bị loại như attack (7 phiên: 2 batch07 dc_db_maint + 5 log_review cũ).
- `revert_control` (HN có snapshot_before) chỉ là metadata cửa sổ, nằm trong mẫu cấm của featurize.
- split: T-hard theo chữ ký công cụ (21 chữ ký, mỗi chữ ký ≥1 T-hard, ≥50% Train) — đều đạt.
- Kết quả: 61 490 event -> 809 cửa sổ (278 dương). Train 479 · T-clean 91 · T-hard 87 · T-novel 152.
  Kiểm tra 1–8: ĐẠT. #9 KHÔNG ĐẠT ở `cmd.exe` (Train 14,5% âm < 15%), không ép số liệu. #10: TVD 0,495; ESENT 216/330
  chỉ ở phía dương (tác động phụ thật của ntdsutil ifm, ngoài cây tiến trình).

### Đóng băng dataset-v1.0 — 2026-10-15
- Sửa cách tính giờ log trong card: tổng thời lượng phiên theo manifest = 13,88 giờ (hợp khung theo host: WIN10-01 7,97 h,
  DC01 3,79 h; khoảng export theo giờ Wazuh 26,26 h để đối chiếu). Bản trước dùng min/max ts_system ra 46,6 h (batch07|DC01
  21,1 h do đồng hồ snapshot). Không chạy lại split: checksum split/vocab không đổi.
- Xác nhận `orchestrator/Invoke-VTSession.ps1` ở HEAD parse 0 lỗi.
- Gắn tag `dataset-v1.0`. sha256: train 22008227…, t_clean 7795fe31…, t_hard 185ae4d0…, t_novel e53b4ff7…, vocab f92a0915…

### Bước 5 (phần 1) + dataset-v1.1 — 2026-10-16
- Khung đánh giá `src/eval/{bootstrap,evaluate}.py` (chỉ numpy): checksum dataset, fold theo nhóm chồng thời gian,
  ngưỡng chọn trên Train OOF (khoá) + 0.5, CI bootstrap 1000 lần seed 1337 (paired) + Wilson, báo riêng T-clean / T-hard
  (FPR theo chữ ký công cụ, có/không cmd.exe) / T-novel (recall T1003.003 mức phiên). Selftest random/oracle đạt.
- B0 (`src/baselines/b0_wazuh.py`, trên v1.0): L=4; mạnh nhờ luật powershell→cmd.exe; mù T1016/T1654/T1003.003. Sẽ chạy lại trên v1.1.
- B1 (`b1_tfidf_lr.py`) trên v1.0 lộ **dấu vết bộ sinh (scaffold)**: đường dẫn cmd (ART `"cmd.exe"` vs HN `C:\Windows\System32\cmd.exe`),
  `>nul 2>&1`, `conhost.exe` (ART console riêng), launcher cha (powershell vs cmd), đuôi `.exe`. Mốc A: B1-canon ≈ B1 (chênh trong CI).
- `src/dataset/scaffold_scan.py`: quét đặc trưng đơn lẻ tách attack/hard_negative (kiểm tra #11 thường trực, ngưỡng 0.98).
- **dataset-v1.1** (featurizer f3), áp đồng nhất mọi lớp: bỏ event conhost.exe khi dựng stream; `canon_cmd` (basename file thực thi,
  bỏ chuyển hướng & toán tử, bỏ đuôi `.exe`); parent powershell/cmd → `<launcher>`. run_id mỗi tập + assignment.json trùng v1.0;
  809 → 793 cửa sổ (265 dương; 16 phiên mất 1 cửa sổ vì stream ngắn đi). #11: mức tách cao nhất 0.942 → 0.778; một phía 68 → 52
  (còn lại: coverage benign route/netstat/admins, hành vi attack, ESENT, `<launcher>→powershell.exe`, svchost→rundll32 COM nền).
  #9 giờ ĐẠT (cmd.exe 15.1%). Giữ nguyên có chủ ý các khác biệt hành vi/coverage; đo bằng ablation.
- Đã cài scikit-learn 1.9.1 (+scipy) trên host.
- Sửa trình bày card (7a đánh số 1–4 theo thứ tự thao tác, #11 nối vào bảng mục 8, bỏ gạch đầu #9 ở mục 9 vì đã đạt);
  `scaffold_scan` sắp xếp tất định (tie-break theo tên). Dữ liệu/checksum KHÔNG đổi; tag `dataset-v1.1` dời sang commit này.

### dataset-v1.2 — 2026-10-16
- B1 trên v1.1 lộ bất đối xứng 4688/EID1 (trọng số `eid=5 eid=4688`): normalize v0 lấy process_id của 4688 = creator
  trong khi image = tiến trình được tạo; labeler loại event có process_id thuộc orchestrator ⇒ mất 4688 của con trực tiếp
  orchestrator (script benign/HN gọi tool trực tiếp; ART/batch07 qua cmd) ⇒ tỉ lệ 4688/EID1 lệch theo lớp (0.11–0.82).
- **normalize v1**: 4688 process_id = newProcessId, parent = processId. **labeler v8**: 4688 không khớp EID1 kế thừa theo
  tiến trình tạo (cha orchestrator → phiên tại thời điểm tạo / harness / upload / orch_child_outside; cha khác → cùng cây).
  Đối chiếu v7↔v8 10 đợt: chỉ 2 394 event 4688 đổi, 0 event khác (`reports/label_v7_v8_diff.json`).
- #12 mới (4688/EID1 theo host × lớp, [0.9, 1.1]): mọi ô ≈ 1.00 — ĐẠT. #11 mở rộng (bigram event_id): max 0.735, ĐẠT.
- Phiên `20261014-164113-dc01-a` (ntds) bị loại sai ở v1.1 (thiếu EID1, có 4688) → khôi phục. `split.py --pin-assignment`
  giữ nguyên thành viên v1.1, phiên mới → Train (nhóm đơn, phân tầng). 793 → 809 cửa sổ (272 dương).
- Rà 20 phiên bị loại (`src/dataset/audit.py`): không phiên nào có event tạo tiến trình con của orchestrator; lý do trong card
  theo bằng chứng (mất telemetry / cmdlet trong orchestrator / không xác định sau snapshot).
- Lỗi trùng PID của quy tắc loại orchestrator (không giới hạn thời gian): 7 tiến trình / 23 event (gồm ntdsutil malicious) — ghi hạn chế.

### Bước 5 hoàn tất (B0–B3) — 2026-10-17
- Vá rò rỉ: `tempo`/`variant`/`user_role` (cấu hình orchestrator; `variant != mixed` chỉ ở attack → rò nhãn) thêm vào trường cấm:
  `featurize.FORBIDDEN`, `evaluate.check_model_sources` (quét tĩnh `src/baselines` + `src/models`, `evaluate()` dừng nếu vi phạm),
  `common.window_events` assert, card #2 + mục 7. B0/B1 không dùng → không chạy lại; dữ liệu/checksum dataset-v1.2 không đổi.
- B2 (`b2_lgbm.py`, LightGBM 4.7.0): đặc trưng tỉ lệ theo số event (không `n_events`), CV nhóm chọn siêu tham số, ngưỡng khoá Train OOF,
  top-15 gain. (a) macro-F1 TTP 0.88/0.80, T-hard FPR 1/88; (b) sụp (T-novel F1 0.48, FPR 14/88) → phụ thuộc tên tiến trình.
- B3 (`b3_gru.py`, torch 2.14.1 CPU): GRU 1 lớp hidden 96, không attention, đơn nhiệm; B3-bin + B3-ttp huấn luyện RIÊNG;
  padding mask (pack_padded_sequence) + random length crop (nhãn tính lại trên đoạn cắt từ `label_malicious`/`label_ttps` từng event,
  chỉ trên Train); early stopping theo CV nhóm, 3 seed (1337/7/42) báo trung bình ± độ lệch chuẩn. Mã hoá đối chiếu khớp file split.
  Trần 60 epoch: 3/120 fold CV chạm trần, nhưng model cuối mỗi lượt dừng ở epoch 18–49 (dưới trần) → ảnh hưởng nhỏ.
- Kết quả chính: học máy giảm FPR T-hard từ 17/88 (B0) xuống 0–5/88; **B1 và B3 KHÔNG sụp ở ablation (b)**, B2 thì sụp → ở B1/B3
  bỏ `image_name` tổng quát hoá tốt hơn (ứng cử cấu hình chính Bước 6); (c') ≈ (a) ở mọi mô hình; T1654 là TTP khó nhất; T1003.003
  test nhỏ (6 phiên T-novel) báo theo phiên. Confounder độ dài: Spearman điểm~độ dài dương ở B1 TF-IDF (~0.73) và B3 (~0.61).
- `src/baselines/summary.py` gộp nhiều seed (trung bình ± độ lệch chuẩn); `src/baselines/step5_report.py` sinh report + results.json.

### Bước 5 đóng + Bước 6 (VT-Seq) — 2026-10-17
- Bước 5 đóng: sửa câu coverage gap (route/netstat/Domain Admins chỉ ở phía ÂM); Spearman B0 T-hard 0.46 (v1.1) → 0.05 (v1.2)
  là thật (luật Wazuh 67027 level 3 trên 4688 khôi phục ở v1.2). Tag `step5-done` đã đẩy nên KHÔNG dời: tạo `step5-done-r1`.
- `src/models/vtseq.py` (một nguồn cho host + Colab): encoder event giống B3 → GRU 1 chiều hidden 96 → additive attention →
  đầu bin + 5 đầu TTP; name dropout; crop U[4,n] mọi lớp (nhãn đoạn từ nhãn event Train); ngưỡng FPR<=1% OOF; p_bin/p_bin'.
  Đọc CHỈ cat/cmd/num + nhãn cửa sổ từ split + `data/processed/step6/aux.jsonl` (`vtseq_aux.py`: mặt nạ origin/one_sided,
  nhãn event CHỈ Train; sha ở `reports/step6/aux_manifest.json`). `test_vtseq.py` 38/38.
- Huấn luyện: laptop quá tải khi chạy 5 tiến trình song song → mốc 2–3 chạy Colab (`notebooks/step6_vtseq_colab.ipynb`,
  clone theo commit, chỉ giải nén splits + vocab + aux), chấm trên host bằng evaluate.py. Mốc 4 (attention, ONNX) trên host.
- Mốc 2 (OOF, 5 seed): attention là bước nhảy chính (macro-F1 OOF 0.774 → 0.822); M3/M4/M4b ngang nhau theo 4.3, phá hoà bằng
  độ ổn định ngưỡng OOF → khoá M3 ở `reports/step6/final_config.json` (commit 3ebc94b) TRƯỚC test.
- Mốc 3 (test 1 lần): sau Holm (9 so sánh) chỉ còn VT-Seq-ens > B3 (b) ở macro-F1 TTP T-novel (+0.092, p Holm 0.009); vs
  B1/B2 không khác. T1654 ~0.68 (B2 0.59, B3 0.46–0.50); M4b-ens bền khi bỏ tên công cụ (0.83 vs B2 (b) 0.45). Crop chưa vững
  (theo trung vị); seed lẻ không ổn định với T1003 → triển khai ens. Ổn định ngưỡng đến từ quy tắc FPR<=1%, không từ kiến trúc.
- Mốc 4: hạt giống luật CHỈ Train (attention OOF, fold huấn luyện lại trên host, r 0.991–0.999 với Colab) → 4 cảnh báo
  (ntds_T1003 trong đường dẫn ART, cmd /c, attention dùng chung + ESENT ở T1003, powershell/4104 ở T1087.002). Faithfulness ens
  đạt mọi k. ONNX opset 17 (seed 1337 + ens), parity ≤ 6.6e-7, ens ~1.4 ms/cửa sổ CPU 1 thread. `.onnx`/`.pt` không vào git (sha256).
- Tiêu chí chấp nhận mục 9: 8/8 đạt. Brief mục 6 đã sửa (hạt giống chỉ Train; attention test chỉ để giải thích).

### Bước 7 (Auto Rule Engine) — 2026-10-17
- `src/rules/predicates.py`: atom "có mặt" (image / parent / event_id / token lệnh norm_cmd / image+token cùng event), danh sách cấm
  S1 (đường dẫn/mã ART), S2 (vỏ cmd), S3 (PowerShell), S4 (ESENT/VSS/COM nền), S5 (tên miền lab), matcher nội bộ.
- `src/rules/induce.py` (CHỈ Train: split test chỉ băm sha; windows.jsonl chỉ parse dòng Train): 2 lượt (không ràng buộc / ràng
  buộc + S4-auto: atom < 50% khớp trong cây tiến trình), engine chọn bằng macro-F1 TTP OOF: RIPPER 0.756 > cây 0.675/0.658;
  luật = literal có mặt; OOF = quy nạp lại trên fold; cổng G0–G4 + ≥10 cửa sổ OOF (đặt trước test). 11 luật được duyệt
  (commit 6b56a7a); G1 loại 18, G3 24, G4 1. Sai khác brief ghi trong provenance + report.
- Sigma (`sigma_export.py`): 10 luật đơn + 1 correlation temporal (`generate: false`), token → `CommandLine|re` có biên token
  (+ `\"` do log Wazuh); pySigma 2.0.1 + 31 validator: 0 lỗi. `apply.py`: matcher đọc YAML ≡ vị từ luật trên Train (0 lệch).
- Chỉ-luật: T-hard 0/88 FP (B0 17/88), T-novel F1 0.878; phủ T1018/T1654/T1003 (B0 mù). Hạn chế: 6/6 ntds2v chỉ nhờ token chung
  `create` (trùng khớp); token chung create/system; VTR-T1654-01 gắn nhầm 2 cửa sổ T-novel; không luật TTP cho T1016/T1087.002.
- OOF cho Bước 8 (`oof.py`): chạy lại quy trình trên 4/5 Train mỗi fold → `reports/preds/rules_oof_train.jsonl` (G3 xấp xỉ).
- Tiêu chí chấp nhận mục 8: 6/6 đạt; `test_induce.py` 15/15.

## 7. Việc tiếp theo / câu hỏi mở

- [x] Bước 5 mốc C: FPR phân tầng theo độ dài + Spearman điểm–độ dài trong evaluate.py.
- [x] Bước 5 mốc D: B0, B1 (TF-IDF/raw), B2 (LightGBM), B3 (GRU, 3 seed) trên dataset-v1.2 + ablation (a)(b)(c chỉ T-hard)(c');
      tổng hợp `reports/step5_report.md` + `reports/step5_results.json`; preds ở `reports/preds/` (giữ cho Bước 8). Tag `step5-done`.
- [x] Bước 6: VT-Seq + ablation, `reports/step6_report.md`, tag `step6-done`.
- [x] Bước 7: Auto Rule Engine, `reports/step7_report.md`, tag `step7-done`.
- [ ] Bước 8: fusion VT-Seq-ens (`reports/preds/vtseq_M3_ens_*`) + chỉ-luật, cùng evaluate.py. Học fusion CHỈ bằng OOF:
      `reports/preds/vtseq_M3_ens_train.jsonl` (OOF) + `reports/preds/rules_oof_train.jsonl` (OOF theo fold). KHÔNG dùng
      `rules_train.jsonl` (in-sample). T1016/T1087.002 không có luật theo TTP → dựa vào AI.
- [ ] Kiểm soát độ dài chưa vững ở từng seed (crop) — cân nhắc ở bước sau nếu cần.
- [ ] `.onnx`/`.pt` không vào git: bản gốc ở Drive `step6_m3_44f8948d.zip`; tái tạo ONNX: `python src/models/step6_explain.py onnx`.
- [ ] #9 đạt sát ngưỡng (cmd.exe 15.1%) — nếu thu thêm dữ liệu: phiên benign gọi tool qua `cmd.exe /c`
      (vd sửa network_check/user_inventory/log_review), cũng giúp 45 phiên benign có event riêng.
- [ ] route/netstat chỉ ở phía âm (đường tắt ngược); wevtutil Train âm 5 cửa sổ (17%) — sát ngưỡng.
- [ ] #10: ESENT 216/330 là tín hiệu nền của T1003.003 (ngoài cây tiến trình) — cân nhắc khi diễn giải ablation.
- [ ] T1003.003: T-clean 13 cửa sổ dương, T-novel (ntds2v) 5 — báo cáo kèm khoảng tin cậy.
- [ ] Chọn phiên bản Python, tạo `requirements.txt` (Bước 4 chỉ cần stdlib + numpy; Python 3.12).
