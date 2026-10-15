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
| 2 | Bộ điều phối sinh phiên, thu thập 401 phiên | `orchestrator/`, `manifests/` | Hoàn thành |
| 3 | Chuẩn hoá & gán nhãn (labeler v5) | `src/normalize/`, `src/label/` | Hoàn thành |
| 4 | Đóng băng dataset: gộp, cửa sổ, đặc trưng, chia tập, dataset card | `src/dataset/`, `reports/` | Hoàn thành |
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

## 7. Việc tiếp theo / câu hỏi mở

- [ ] Bước 5: baseline B0 (luật Wazuh từ `wazuh_rule_*`), B1 (TF-IDF+LR), B2 (LightGBM), B3 (GRU thuần) trên các split.
- [ ] Bước 6: VT-Seq (GRU-Attention đa nhiệm) + ablation; nạp dữ liệu CHỈ từ `cat`/`cmd`/`num`; cắt ngẫu nhiên độ dài
      cửa sổ khi huấn luyện; ablation bỏ `image_name` (đường tắt ping/wevtutil/ntdsutil).
- [ ] Cân nhắc thu thêm phiên hard-negative dùng ping/wevtutil hợp lệ (T-hard hiện chưa thử thách T1018/T1654).
- [ ] T1003.003 chỉ có 5 cửa sổ ở T-clean — báo cáo kèm khoảng tin cậy.
- [ ] Chọn phiên bản Python, tạo `requirements.txt` (Bước 4 chỉ cần stdlib + numpy; Python 3.12).
