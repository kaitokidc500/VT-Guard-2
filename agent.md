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
| 3 | Chuẩn hoá & gán nhãn (labeler v7) | `src/normalize/`, `src/label/` | Hoàn thành |
| 4 | Đóng băng dataset (tag `dataset-v1.0`): gộp, cửa sổ, đặc trưng, chia tập, dataset card | `src/dataset/`, `reports/` | Hoàn thành |
| 5–6 | Baseline B0–B3; VT-Seq + ablation | `src/models/`, `notebooks/` | Chưa bắt đầu |
| 7 | Luật | `src/rules/` | Chưa bắt đầu |
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
- **Dataset đóng băng `dataset-v1.0` (git tag):** Bước 5–8 dùng ĐÚNG `data/processed/splits/{train,t_clean,t_hard,t_novel}.jsonl`,
  `data/processed/vocab.json` (bản sao `reports/vocab.json`); trước khi chạy, so sha256 với `reports/dataset_card.md` mục 10.
  Không chạy lại split/featurize/label trên bản này; muốn đổi dữ liệu thì tạo phiên bản mới (dataset-v1.1…).

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

## 7. Việc tiếp theo / câu hỏi mở

- [ ] Bước 5: baseline B0 (luật Wazuh từ `wazuh_rule_*`), B1 (TF-IDF+LR), B2 (LightGBM), B3 (GRU thuần) trên các split.
- [ ] Bước 6: VT-Seq (GRU-Attention đa nhiệm) + ablation; nạp dữ liệu CHỈ từ `cat`/`cmd`/`num`; cắt ngẫu nhiên độ dài
      cửa sổ khi huấn luyện; ablation bỏ `image_name` (đường tắt ping/wevtutil/ntdsutil).
- [ ] #9: `cmd.exe` Train chỉ 14,5% cửa sổ âm — thêm phiên benign/hard-negative gọi tool qua `cmd.exe /c`
      (vd sửa network_check/user_inventory/log_review sang `cmd.exe /c`, cũng giúp 45 phiên benign có event riêng).
- [ ] route/netstat chỉ ở phía âm (đường tắt ngược); wevtutil Train âm 5 cửa sổ (17%) — sát ngưỡng.
- [ ] #10: ESENT 216/330 là tín hiệu nền của T1003.003 (ngoài cây tiến trình) — cân nhắc khi diễn giải ablation.
- [ ] T1003.003: T-clean 13 cửa sổ dương, T-novel (ntds2v) 5 — báo cáo kèm khoảng tin cậy.
- [ ] Chọn phiên bản Python, tạo `requirements.txt` (Bước 4 chỉ cần stdlib + numpy; Python 3.12).
