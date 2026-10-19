# VT-Guard — Bước 9 mốc 4: gắn VT-Guard vào hạ tầng Wazuh và chạy thử trong lab

Mục tiêu (brief Bước 9 mục 2, 4, 5, 8.4): VT-Guard đọc log THẬT từ `wazuh-archives-*` trên VT-SIEM01, chấm bằng pipeline đã khoá,
cảnh báo hiện ở dashboard Phần A (Trực tiếp · Hàng đợi), tuỳ chọn ghi ngược `vtguard-alerts-*` để thấy ngay trong Wazuh Dashboard.
Không huấn luyện lại, không đổi ngưỡng/cấu hình.

```
DC01, WIN10-01 (agent) ──► VT-SIEM01 10.20.30.10: Wazuh Manager + Indexer :9200 (wazuh-docker 4.14.8, giữ nguyên)
                                        │  REST, tài khoản riêng: chỉ đọc wazuh-archives-*, chỉ ghi vtguard-alerts-*
                                        ▼
                     Máy trình chiếu (host): VT-Guard live (Python hoặc Docker) ──► dashboard :8501
```

## 0. Kiểm tra trước (5 phút)

1. Máy host ping được `10.20.30.10` và mở được `https://10.20.30.10:9200` (trình duyệt báo lỗi chứng chỉ là bình thường).
2. Trên VT-SIEM01, `wazuh-archives-*` vẫn đang nhận event (archives đã bật ở Bước 1, đã dùng để export dataset):
   ```bash
   curl -k -u admin "https://localhost:9200/_cat/indices/wazuh-archives-*?v"
   ```
3. Đồng hồ DC01 / WIN10-01 / VT-SIEM01 đúng giờ (sau khi khôi phục snapshot DC01 từng lệch ~55 phút — chạy `w32tm /resync` trên DC01).

## 1. Tạo tài khoản Indexer riêng cho VT-Guard (trên VT-SIEM01, một lần)

Dùng tài khoản admin hiện có; mật khẩu nhập tay khi curl hỏi (`-u admin`), không ghi vào file nào trong repo.

```bash
# vai trò: chỉ đọc wazuh-archives-*, chỉ ghi vtguard-alerts-*
curl -k -u admin -X PUT "https://localhost:9200/_plugins/_security/api/roles/vtguard_role" -H 'Content-Type: application/json' -d '{
  "cluster_permissions": ["cluster:monitor/main", "indices:data/write/bulk"],
  "index_permissions": [
    {"index_patterns": ["wazuh-archives-*"], "allowed_actions": ["read"]},
    {"index_patterns": ["vtguard-alerts-*"], "allowed_actions": ["create_index", "write", "read"]}]}'

# người dùng (đặt mật khẩu mạnh của bạn thay cho <MAT_KHAU>)
curl -k -u admin -X PUT "https://localhost:9200/_plugins/_security/api/internalusers/vtguard" -H 'Content-Type: application/json' \
     -d '{"password": "<MAT_KHAU>"}'

# gán vai trò
curl -k -u admin -X PUT "https://localhost:9200/_plugins/_security/api/rolesmapping/vtguard_role" -H 'Content-Type: application/json' \
     -d '{"users": ["vtguard"]}'
```

Lấy chứng chỉ CA của Indexer về host (wazuh-docker single-node):
`single-node/config/wazuh_indexer_ssl_certs/root-ca.pem` → chép vào `G:\VT-Guard\secrets\root-ca.pem`
(thư mục `secrets/` đã nằm trong `.gitignore`).

## 2. File env trên host

```bash
mkdir -p secrets && cp docker/vtguard.env.example secrets/vtguard.env
```

Sửa `secrets/vtguard.env`: điền `VTG_INDEXER_PASSWORD`; nếu chạy Python trực tiếp trên host thì đổi
`VTG_INDEXER_CA=G:/VT-Guard/secrets/root-ca.pem` (Docker giữ `/secrets/root-ca.pem`). `VTG_INDEXER_CHECK_HOSTNAME=0` vì chứng chỉ
cấp cho tên `wazuh.indexer` còn ta nối bằng IP (vẫn kiểm CA). Không có CA thì tạm dùng `VTG_INDEXER_INSECURE=1` (chỉ lab).

## 3. Kiểm tra kết nối (không đọc luồng, không ghi gì)

```bash
python src/live/run.py live --env-file secrets/vtguard.env --check
```

Kỳ vọng: `version` 2.x, `user` = `vtguard`, `roles` có `vtguard_role`, mỗi agent có `events_last_min` > 0 và `latest` gần giờ hiện tại
(trễ 40–60 s là bình thường). Lỗi thường gặp: 401 → sai mật khẩu / chưa gán role; `CERTIFICATE_VERIFY_FAILED` → sai file CA hoặc thiếu
`VTG_INDEXER_CHECK_HOSTNAME=0`; `events_last_min` = 0 → agent ngắt hoặc archives không ghi.

## 4. Chạy live + dashboard

**Cách A — Python trên host (dễ gỡ lỗi):** hai cửa sổ terminal

```bash
python src/live/run.py live --env-file secrets/vtguard.env --reset --push-alerts
```
```bash
python -m streamlit run dashboard/app.py --server.port 8501
```

**Cách B — Docker (giống sản phẩm đóng gói):**

```bash
docker run --rm -p 8501:8501 -v "G:/VT-Guard/secrets:/secrets:ro" vtguard:step9 live --env-file /secrets/vtguard.env --reset --push-alerts
```

- `--reset`: bỏ checkpoint cũ, đọc từ thời điểm bắt đầu; lần chạy lại sau sự cố thì BỎ `--reset` để đọc tiếp từ checkpoint.
- Cảnh báo phát lại (replay) cũ tự bị xoá khi chuyển sang live, không trộn với cảnh báo thật.
- `--push-alerts` (tuỳ chọn): ghi `vtguard-alerts-YYYY.MM.DD`. Trong Wazuh Dashboard: Dashboards Management → Index patterns →
  tạo `vtguard-alerts-*`, trường thời gian `@timestamp` → Discover để thấy cảnh báo VT-Guard cạnh cảnh báo gốc.

Mở `http://localhost:8501`: ô **Luồng** phải ghi TRỰC TIẾP, panel **Hạ tầng** hiện DC01, WIN10-01 với số event tăng dần, biểu đồ
**Lưu lượng event** chạy.

## 5. Chạy thử kịch bản demo (brief mục 4)

Mọi bước tấn công qua **Atomic Red Team theo test ID**, trên lab cô lập, bằng chính orchestrator của dataset
(`orchestrator/Invoke-VTSession.ps1`) — để cách VT-Guard loại tiến trình khung ART giống hệt lúc tạo dataset
(`--tool-mode orchestrator`, mặc định; độ lệch đã đo ở `reports/step9/live/drift_report.json`).

| Màn | Việc trong lab | Kỳ vọng trên VT-Guard | Ghi lại |
|---|---|---|---|
| 0 | Revert snapshot sạch; bật live + dashboard; mở Wazuh Dashboard bên trái, VT-Guard bên phải | Luồng TRỰC TIẾP, 0 cảnh báo | ảnh 2 màn hình |
| 1 | `Invoke-VTSession.ps1 -Class hard_negative ...` với `admin_net_sweep`, `dc_db_maint` | KHÔNG cảnh báo (đối chiếu T-hard 1/88) | ảnh hàng đợi trống |
| 2 | `-Class attack` với T1016 / T1018 / T1087.002 / T1654 (test trong `orchestrator/scenarios.json`) | cảnh báo sau ~1 phút; Chi tiết: luật Sigma + xuất xứ, top-5 attention; Wazuh không có cảnh báo hành vi tương ứng | ảnh Chi tiết + ảnh Wazuh |
| 3 | `-Class attack` T1003.003 test 3 trên DC01 (sau khi revert snapshot) | cảnh báo nguồn `both` (AI + VTR-T1003003-01) | ảnh Chi tiết |
| 4 | — | Dòng thời gian: một sự cố LINC chuỗi discovery → NTDS; (nếu `--push-alerts`) cùng cảnh báo trong Wazuh Discover | ảnh 2 màn hình |

Sau buổi chạy thử:
- Ghi log của lần chạy thành công làm log mẫu replay mới (giữ ngoài git):
  `python scripts/export_batch.py <GTE> <LTE> demo_m4` trên VT-SIEM01 → chép `data/raw/demo_m4/` về host →
  sửa `SLICES` trong `src/live/make_sample.py` (hoặc phát lại thẳng thư mục: `run.py replay --input data/raw/demo_m4`).
- Lưu `reports/step9/live/status.json` + ảnh vào `reports/step9/m4/`, ghi số liệu (số cảnh báo theo màn, độ trễ trung vị) vào
  `reports/step9_report.md` mục 2.

## 6. Trung thực khi trình bày

Demo trực tiếp là minh hoạ VẬN HÀNH (cửa sổ theo thời gian, khác cửa sổ theo phiên của tập test). Số liệu chính thức ở Phần B
(tập kiểm thử đóng băng). Tương phản với Wazuh nói theo B0: "theo baseline B0 của chúng tôi, luật Wazuh có sẵn không gán được 4/5 kỹ thuật".
Chạy tấn công từ console tay (không qua orchestrator) có thể lệch tiền xử lý — xem `drift_report.json` chế độ `console`.

## Giới hạn đã biết của connector

- Phân trang theo `timestamp` (ms) + loại trùng theo `_id` tại mốc; nếu > 2 000 event có CÙNG một mili-giây thì vòng đọc dừng ở mốc đó
  (chưa gặp trong lab). Kiểm thử: `src/live/test_live.py` L8 (Indexer giả lập, 40 event cùng mốc, trang 50).
