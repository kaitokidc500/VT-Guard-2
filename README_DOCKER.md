# VT-Guard — chạy lại bằng Docker (offline)

Image `vtguard:step9` chứa mô hình đã đóng băng (VT-Seq-ens ONNX), 11 luật Sigma tự sinh, cấu hình fusion F3-B đã khoá,
3 tập kiểm thử của `dataset-v1.2` và toàn bộ kết quả Bước 5–8. **Không cần lab, không cần Internet, không cần GPU.**
Image không chứa log thô (trừ một file log mẫu để phát lại), checkpoint `.pt` hay thông tin đăng nhập.

## Yêu cầu máy

- Docker Desktop (Windows / macOS) hoặc Docker Engine (Linux), image `linux/amd64`. Máy Apple Silicon chạy được qua giả lập
  (chậm hơn); có thể dựng bản `linux/arm64` bằng `sh docker/build.sh linux/arm64`.
- RAM trống ~1 GB, đĩa ~0,5 GB (file `vtguard_amd64.tar` 223 MB; image sau khi nạp ~223 MB).

## Nạp image

```bash
docker load -i vtguard_amd64.tar
```

Kiểm tra file trước khi nạp: sha256 của `vtguard_amd64.tar` phải trùng `docker/image_info.json`.

## 3 lệnh chính

**1. Kiểm chứng số liệu báo cáo (offline hoàn toàn):**

```bash
docker run --rm --network none vtguard:step9 verify
```

Chạy lại pipeline suy luận + `evaluate.py` trên 3 tập test (326 cửa sổ), mất ~10–20 giây. Mỗi dòng là một mục kiểm tra:

| Mục | Kiểm tra |
|---|---|
| V1 | sha256 dataset-v1.2 (splits + vocab) trùng dataset card |
| V2 | sha256 mô hình ONNX trùng Bước 6; 27 artefact báo cáo trùng bản đã chấm |
| V3 | đặc trưng tính lại trùng vector trong file split |
| V4 | quyết định nhị phân + 5 TTP trùng dự đoán đã chấm (0 lệch; điểm lệch ≤ 1e-5) |
| V5 | 101 cảnh báo trùng `reports/step8/alerts_<tập>.jsonl` |
| V6 | chỉ số (F1, PR-AUC, macro-F1 TTP, FPR T-hard… kèm CI bootstrap seed 1337) trùng báo cáo Bước 8 |
| V7 | TP/FP/FN của B0 (luật Wazuh), VT-Seq-ens, chỉ-luật trùng Bước 5/6/7 (T-hard FP: 17 / 1 / 0 trên 88) |

Dòng cuối `VERIFY: DAT (7/7 muc)` nghĩa là toàn bộ số liệu chính thức chạy lại được và trùng khớp. Mã thoát 0 = ĐẠT, 1 = có mục KHÔNG ĐẠT.

**2. Mở dashboard SOC (tiếng Việt):**

```bash
docker run --rm -p 8501:8501 vtguard:step9
```

Mở trình duyệt `http://localhost:8501`. Dashboard có hai phần:

- **Phần A · SIEM thời gian thực** (Trực tiếp · Hàng đợi, Chi tiết cảnh báo, Dòng thời gian sự cố): giống màn hình SOC gắn vào Wazuh,
  không hiện nhãn đúng/sai. Chưa có luồng thì bấm **Phát lại log mẫu** ngay trên trang.
- **Phần B · Kết quả nghiên cứu** (Kết quả & đánh giá, Luật Sigma tự sinh): số liệu chính thức trên tập kiểm thử đóng băng,
  làm nổi 3 yêu cầu đề tài (luật tự sinh có xuất xứ, hợp nhất AI + luật, mô hình chuỗi tuỳ biến) và so sánh với luật Wazuh có sẵn.

**3. Xem luồng trực tiếp (phát lại log mẫu, không cần lab):**

```bash
docker run --rm -p 8501:8501 vtguard:step9 demo
```

Phát lại `samples/replay_demo.jsonl.gz` (31 054 event Wazuh: quản trị lành tính + discovery + dump NTDS) qua đúng pipeline
trực tiếp, nhanh gấp 10 lần thời gian thật; khoảng im lặng dài giữa hai đoạn log được tua nhanh (~3–4 phút cho cả luồng,
17 cảnh báo). Trang **Trực tiếp · Hàng đợi** tự làm mới: cảnh báo mới trôi lên đầu hàng đợi.

## Lệnh khác

| Lệnh | Việc |
|---|---|
| `selftest` | kiểm thử không cần mạng: dashboard (31), luồng trực tiếp (9), quét file nhạy cảm |
| `scan` | quét image: 0 checkpoint / log thô / thông tin đăng nhập |
| `replay [--speed k]` | phát lại log ra `reports/step9/live/alerts.jsonl` (in tóm tắt) |
| `infer --input /data/windows.jsonl --out /out/alerts.jsonl` | chạy pipeline trên file cửa sổ của bạn (`-v` mount thư mục) |
| `live --env-file /secrets/vtguard.env [--push-alerts]` | chỉ dùng trong lab: nối Indexer Wazuh thật (xem dưới) |

## Triển khai cạnh Wazuh trên máy chủ SIEM

Để chạy VT-Guard **cố định trên VT-SIEM01 (10.20.30.10) cạnh wazuh-docker**, dashboard ở cổng 8501, với tự khởi động lại,
healthcheck và ghi ngược `vtguard-alerts-*`, dùng `deploy/docker-compose.yml`. Hướng dẫn đầy đủ: **`docs/STEP9-M4-DEPLOY.md`**;
bộ kịch bản demo trước hội đồng: **`docs/STEP9-M4-DEMO.md`**.

```bash
cd deploy && cp .env.example .env && mkdir -p secrets && cp vtguard.env.example secrets/vtguard.env
# sửa .env (mạng Wazuh, cổng) và secrets/vtguard.env (mật khẩu Indexer)
docker compose run --rm vtguard-live stream --env-file /secrets/vtguard.env --check   # kiểm kết nối
docker compose up -d
```

## Chế độ `live` (một container, trong lab)

Thông tin đăng nhập KHÔNG nằm trong image: mount file từ ngoài lúc chạy.

```bash
docker run --rm --network <mang_lab> -p 8501:8501 -v /duong/dan/secrets:/secrets:ro vtguard:step9 live --env-file /secrets/vtguard.env
```

File env gồm các khoá `VTG_INDEXER_URL`, `VTG_INDEXER_USER`, `VTG_INDEXER_PASSWORD`, `VTG_INDEXER_CA` (đường dẫn file CA đã mount)
và tuỳ chọn `VTG_AGENTS` (mặc định `DC01,WIN10-01`). Nên dùng tài khoản Indexer riêng: chỉ đọc `wazuh-archives-*`, chỉ ghi
`vtguard-alerts-*` (khi bật `--push-alerts`).

## Tự build lại (người phát triển)

Trên host có `data/processed/` và `models/vtseq_M3_ens.onnx`:

```bash
sh docker/build.sh linux/amd64
```

Script dựng context theo danh sách cho phép (`docker/stage.py`, ghi `docker/MANIFEST.json`), quét file nhạy cảm, build,
chạy `verify` + `selftest` với `--network none`, rồi `docker save` ra `docker/out/vtguard_amd64.tar` và ghi sha256 vào
`docker/image_info.json`.
