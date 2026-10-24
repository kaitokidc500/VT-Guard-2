# VT-Guard — Lộ trình hoàn thành đề tài

Đề tài: **VT-Guard — phát hiện APT kiểu Volt Typhoon kết hợp mô hình chuỗi GRU-Attention và luật tự sinh trên nền Wazuh**
(môn Giám sát an ninh mạng). Hạn nộp: **01/11/2026**. Cập nhật: 24/10/2026.

Trạng thái: ✅ hoàn thành · 🟡 đang làm · ⬜ chưa bắt đầu.

## 1. Tổng quan 11 bước

| Bước | Nội dung | Trạng thái | Mốc / tag | Sản phẩm chính |
|---|---|---|---|---|
| 1 | Hạ tầng Wazuh: DC01, WIN10-01 → VT-SIEM01 (wazuh-docker 4.14.8), Sysmon, audit 4688, PowerShell logging | ✅ | 12/10 | `evidence/`, lab VMnet2 cô lập |
| 2 | Bộ điều phối phiên + Atomic Red Team, manifest, kịch bản lành tính / hard-negative | ✅ | 13/10 | `orchestrator/`, `manifests/` |
| 3 | Thu thập 479 phiên (10 đợt), chuẩn hoá (normalize v1), gán nhãn theo cây tiến trình (labeler v8) | ✅ | 14–16/10 | `src/normalize/`, `src/label/` |
| 4 | Đóng băng dataset: cửa sổ 64/32, đặc trưng 268 chiều, chia Train / T-clean / T-hard / T-novel, 12 kiểm tra chấp nhận | ✅ | `dataset-v1.2` (16/10) | `src/dataset/`, `reports/dataset_card.md` |
| 5 | Khung đánh giá (bootstrap, Holm) + baseline B0 (luật Wazuh), B1 (TF-IDF), B2 (LightGBM), B3 (GRU) + ablation | ✅ | `step5-done`, `-r1` (17/10) | `src/eval/`, `src/baselines/`, `reports/step5_report.md` |
| 6 | **YC3** — VT-Seq (GRU + attention, đa nhiệm), chuỗi ablation M0→M4b, ensemble 5 seed, ONNX | ✅ | `step6-done` (17/10) | `src/models/`, `reports/step6_report.md` |
| 7 | **YC1** — Auto Rule Engine: 11 luật RIPPER chỉ từ Train → Sigma có xuất xứ | ✅ | `step7-done`, `-r1` (17/10) | `src/rules/`, `rules/sigma/`, `reports/step7_report.md` |
| 8 | **YC2** — Hợp nhất F3-B (AI + luật xác nhận) + pipeline suy luận đầu–cuối | ✅ | `step8-done` (17/10) | `src/fusion/`, `src/pipeline/`, `reports/step8_report.md` |
| 9 | Dashboard SOC + luồng trực tiếp + Docker + **triển khai cạnh Wazuh** + kịch bản demo | 🟡 | chờ `step9-done` | `dashboard/`, `src/live/`, `docker/`, `deploy/`, `docs/STEP9-M4-*.md` |
| 10 | Báo cáo Word (3 chương, ~59 trang, TNR 14) + slide bảo vệ | 🟡 | — | `report/` (mã dựng; **file .docx chỉ giữ cục bộ, không đưa lên git**) |
| 11 | Cải tiến đề tài và mô hình (nếu còn thời gian) | ⬜ | — | `docs/STEP11-BRIEF.md` |

## 2. Kết quả chính đã đạt (số liệu chính thức trên tập kiểm thử đóng băng)

| Hạng mục | Kết quả |
|---|---|
| Dữ liệu | 479 phiên, 62 917 sự kiện, 809 cửa sổ (272 dương); nhãn theo cây tiến trình; dấu vết bộ sinh trung hoà (mức tách 0,942 → 0,735) |
| Luật Wazuh có sẵn (B0) | macro-F1 kỹ thuật T-novel 0,12; F1 = 0 ở T1016, T1018, T1654, T1003.003; 17/88 báo nhầm trên quản trị hợp lệ |
| VT-Seq-ens (YC3) | F1 T-novel 0,964; macro-F1 kỹ thuật 0,82; 1/88 báo nhầm; hơn GRU thuần sau Holm (+0,092, p = 0,009) |
| Luật tự sinh (YC1) | 11 luật Sigma hợp lệ (pySigma 0 lỗi), 0/88 báo nhầm, phủ T1018 / T1654 / T1003.003 |
| Hợp nhất F3-B (YC2) | hơn chỉ-luật sau Holm (macro-F1 +0,40); không kém chỉ-AI; nhóm “AI + luật” đúng 76/76 |
| Sản phẩm | suy luận 2–3 ms/cửa sổ CPU; image Docker offline, `verify` 7/7; chạy thật cạnh Wazuh tại 10.20.30.10:8501 |

## 3. Việc còn lại đến hạn 01/11/2026

| Ngày | Việc | Bước | Đầu ra |
|---|---|---|---|
| 24–25/10 | Chạy đủ kịch bản KB1–KB6 trên hạ tầng thật (`docs/STEP9-M4-DEMO.md`), chụp ảnh từng bước, chạy `demo_report.py` | 9 | ảnh + `demo_report.md` |
| 25/10 | Đưa số liệu thực nghiệm vào `reports/step9_report.md`; gắn tag `step9-done` | 9 | tag |
| 25–27/10 | Dán ảnh vào 25 khung Hình 3.18–3.42, điền ô tô vàng, điền bìa, cập nhật mục lục trong Word | 10 | báo cáo hoàn chỉnh |
| 27–28/10 | (tuỳ thời gian) Bước 11 nhóm A: thử nghiệm báo nhầm 24 giờ, kiểm thử biến thể chưa thấy | 11 | phụ lục báo cáo |
| 29/10 | Slide bảo vệ + tổng duyệt demo (có phương án phát lại dự phòng) | 10 | slide |
| 30–31/10 | Rà soát, nộp | — | — |

## 4. Nguyên tắc xuyên suốt (giữ nguyên khi làm tiếp)

- **Không sửa `dataset-v1.2`** và không dời tag đã đẩy; dữ liệu mới → phiên bản mới hoặc tập kiểm thử riêng.
- Mọi lựa chọn chỉ dựa trên Train (OOF); cấu hình khoá bằng commit **trước** khi chấm tập kiểm thử; chấm một lần.
- Tuyên bố “tốt hơn” chỉ khi kiểm định paired bootstrap + Holm có ý nghĩa.
- Không commit dữ liệu thô, checkpoint, mật khẩu (`data/`, `*.pt`, `deploy/.env`, `deploy/secrets/`) và **file Word** (`*.docx`).

Tài liệu từng bước: `docs/STEP4-BRIEF.md` … `docs/STEP9-BRIEF.md`, `docs/STEP9-M4-DEPLOY.md`, `docs/STEP9-M4-DEMO.md`, `docs/STEP11-BRIEF.md`.
Đánh giá tổng thể: `docs/ASSESSMENT.md`. Nhật ký chi tiết: `agent.md`.
