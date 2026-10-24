# VT-Guard Research

**VT-Guard** — phát hiện tấn công APT kiểu Volt Typhoon (living off the land) bằng mô hình chuỗi GRU-Attention kết hợp luật
Sigma tự sinh, chạy như một lớp phân tích gắn thêm vào SIEM Wazuh. Đề tài môn Giám sát an ninh mạng.

- **Lộ trình và trạng thái:** [`docs/ROADMAP.md`](docs/ROADMAP.md)
- **Đánh giá tổng thể (thang 10):** [`docs/ASSESSMENT.md`](docs/ASSESSMENT.md)
- **Hướng cải tiến (Bước 11):** [`docs/STEP11-BRIEF.md`](docs/STEP11-BRIEF.md)
- **Nhật ký chi tiết cho người / AI tiếp tục:** [`agent.md`](agent.md)

## Kết quả chính (tập kiểm thử đóng băng `dataset-v1.2`)

| | Luật Wazuh có sẵn (B0) | VT-Guard (F3-B) |
|---|---|---|
| macro-F1 theo kỹ thuật, T-novel | 0,12 (F1 = 0 ở 4/5 kỹ thuật) | 0,82 |
| Báo nhầm trên 88 cửa sổ quản trị hợp lệ | 17 | 1 |
| Giải thích cảnh báo | — | luật Sigma có xuất xứ + top-5 sự kiện attention |

## Chạy nhanh

```bash
# tái lập số liệu báo cáo (offline, không cần lab)
docker run --rm --network none vtguard:step9 verify
# dashboard + phát lại log mẫu
docker run --rm -p 8501:8501 vtguard:step9 demo
# triển khai cạnh Wazuh: docs/STEP9-M4-DEPLOY.md (deploy/docker-compose.yml)
```

## Cấu trúc

```
├─ orchestrator/        # bộ điều phối phiên + Atomic Red Team (Bước 2)
├─ manifests/           # bản kê mỗi phiên chạy
├─ src/
│  ├─ normalize/, label/ # chuẩn hoá, gán nhãn theo cây tiến trình (Bước 3)
│  ├─ dataset/          # cửa sổ, đặc trưng, chia tập, dataset card (Bước 4)
│  ├─ eval/, baselines/ # khung đánh giá, B0–B3 (Bước 5)
│  ├─ models/           # VT-Seq GRU-Attention, ONNX (Bước 6)
│  ├─ rules/            # Auto Rule Engine → Sigma (Bước 7)
│  ├─ fusion/, pipeline/ # hợp nhất F3-B, suy luận, verify (Bước 8)
│  └─ live/             # luồng trực tiếp từ Wazuh Indexer (Bước 9)
├─ rules/sigma/         # 11 luật Sigma tự sinh
├─ dashboard/           # dashboard SOC tiếng Việt (Bước 9)
├─ docker/, deploy/     # đóng gói offline, triển khai cạnh Wazuh (Bước 9)
├─ report/              # mã dựng báo cáo Word (Bước 10; file .docx không lưu trên git)
├─ reports/             # báo cáo từng bước, kết quả JSON, dự đoán
├─ docs/                # đặc tả từng bước, lộ trình, đánh giá, hướng dẫn
└─ data/                # KHÔNG đưa lên git (log thô, dữ liệu đã xử lý)
```

## Ghi chú

- Nội dung `data/`, checkpoint mô hình, thông tin đăng nhập và file Word không được đưa lên git.
- Mọi kỹ thuật tấn công được thực thi qua Atomic Red Team theo mã test, trong lab cô lập; repo không chứa lệnh tấn công.
