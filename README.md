# VT-Guard Research

Kho mã nghiên cứu VT-Guard: thu thập sự kiện từ Indexer, chuẩn hoá và gán nhãn, xây dựng tập dữ liệu theo cửa sổ, huấn luyện mô hình, xây dựng bộ luật và kết hợp (fusion) kết quả.

## Cấu trúc

```
├─ data/
│  ├─ raw/              # JSON kéo từ Indexer
│  ├─ interim/          # đã chuẩn hoá
│  ├─ processed/        # cửa sổ đã cắt, đã chia tập
│  └─ external/         # dataset công khai làm test ngoài
├─ manifests/           # bản kê mỗi phiên chạy
├─ orchestrator/        # bộ điều phối sinh phiên (Bước 2)
├─ src/
│  ├─ normalize/        # Bước 4
│  ├─ label/            # Bước 4
│  ├─ dataset/          # cắt cửa sổ, chia tập
│  ├─ models/           # Bước 5–6
│  ├─ rules/            # Bước 7
│  └─ fusion/           # Bước 8
├─ notebooks/           # huấn luyện Colab
├─ evidence/            # bằng chứng hạ tầng
├─ reports/             # viết báo cáo song song
└─ README.md
```

## Ghi chú

- Nội dung `data/` không được đưa lên git; chỉ giữ cấu trúc thư mục.
- Trạng thái dự án và nhật ký tiến trình: xem [`agent.md`](agent.md).
