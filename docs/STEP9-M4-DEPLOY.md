# VT-Guard — Bước 9 mốc 4 (phần 1): tích hợp vào hạ tầng Wazuh và vận hành ổn định

VT-Guard chạy **ngay trên VT-SIEM01 (10.20.30.10)**, cạnh `wazuh-docker`, dashboard ở **cổng 8501**
(`http://10.20.30.10:8501`). Wazuh giữ nguyên mọi cổng: 443 (Dashboard), 1514–1515 (agent), 514/udp, 55000 (API), 9200 (Indexer).
Kịch bản demo: `docs/STEP9-M4-DEMO.md`.

```
DC01, WIN10-01 ──1514──► VT-SIEM01 10.20.30.10
                          ├─ wazuh-docker (giữ nguyên): wazuh.manager · wazuh.indexer :9200 · wazuh.dashboard :443
                          │        ▲ mạng Docker single-node_default (https://wazuh.indexer:9200, đúng CN chứng chỉ)
                          ├─ vtguard-live       : đọc wazuh-archives-* mỗi 12 s → chấm → alerts.jsonl (+ ghi vtguard-alerts-*)
                          └─ vtguard-dashboard  : http://10.20.30.10:8501  (Phần A SIEM thời gian thực · Phần B kết quả)
                                   volume vtguard_live: checkpoint + trạng thái + cảnh báo (giữ qua khởi động lại)
```

Hai container tách biệt: luồng phát hiện chết thì Docker khởi động lại và **đọc tiếp từ checkpoint** (không mất, không đọc trùng
sự kiện); dashboard độc lập với luồng.

## 0. Kiểm tra trước trên VT-SIEM01 (5 phút)

```bash
free -h                                   # còn trống >= 2 GB RAM (vtguard-live ≤ 1 GB, dashboard ≤ 768 MB)
df -h /                                   # còn >= 3 GB đĩa (image ~225 MB + log + cảnh báo)
docker ps --format '{{.Names}}'           # thấy single-node-wazuh.indexer-1, .manager-1, .dashboard-1
docker network ls | grep single-node      # tên mạng của wazuh-docker, thường là single-node_default
ss -ltnp | grep -E ':8501\b' || echo "cong 8501 trong"
timedatectl | grep -i synchronized        # đồng hồ đã đồng bộ (cả DC01, WIN10-01: w32tm /query /status)
curl -sk -u admin "https://localhost:9200/_cat/indices/wazuh-archives-*?v" | tail -3   # archives còn nhận sự kiện hôm nay
```

Nếu `wazuh-archives-*` của hôm nay không tăng: kiểm tra `<logall_json>yes</logall_json>` trong `ossec.conf` của manager và
`archives.enabled: true` trong Filebeat (đã bật từ Bước 1, nhưng nên xác nhận lại sau mỗi lần khởi động lại stack).

## 1. Đưa image vào VT-SIEM01 (lab không có Internet)

Trên máy chủ vật lý (có repo, dữ liệu và mô hình):

```bash
sh docker/build.sh linux/amd64            # build + verify/selftest offline + docker/out/vtguard_amd64.tar + sha256 vào docker/image_info.json
scp docker/out/vtguard_amd64.tar deploy/ vt_admin@10.20.30.10:~/vtguard/ -r
```

Trên VT-SIEM01:

```bash
cd ~/vtguard
sha256sum vtguard_amd64.tar               # phải trùng docker/image_info.json
docker load -i vtguard_amd64.tar
docker run --rm --network none vtguard:step9 verify      # phải in "VERIFY: DAT (7/7 muc)"
```

## 2. Tài khoản Indexer riêng cho VT-Guard (một lần)

Quyền tối thiểu: **đọc** `wazuh-archives-*` (luồng phát hiện) và `wazuh-alerts-*` (báo cáo đối chiếu demo), **ghi** `vtguard-alerts-*`.
Chạy trên VT-SIEM01, mật khẩu admin nhập khi curl hỏi; thay `<MAT_KHAU_MANH>`:

```bash
curl -sk -u admin -X PUT "https://localhost:9200/_plugins/_security/api/roles/vtguard_role" -H 'Content-Type: application/json' -d '{
  "cluster_permissions": ["cluster:monitor/main", "indices:data/write/bulk"],
  "index_permissions": [
    {"index_patterns": ["wazuh-archives-*", "wazuh-alerts-*"], "allowed_actions": ["read"]},
    {"index_patterns": ["vtguard-alerts-*"], "allowed_actions": ["create_index", "write", "read"]}]}'
curl -sk -u admin -X PUT "https://localhost:9200/_plugins/_security/api/internalusers/vtguard" -H 'Content-Type: application/json' \
     -d '{"password": "<MAT_KHAU_MANH>"}'
curl -sk -u admin -X PUT "https://localhost:9200/_plugins/_security/api/rolesmapping/vtguard_role" -H 'Content-Type: application/json' \
     -d '{"users": ["vtguard"]}'
curl -sk -u vtguard "https://localhost:9200/_plugins/_security/authinfo?pretty" | grep -A3 '"roles"'   # thấy vtguard_role
```

## 3. Cấu hình triển khai

```bash
cd ~/vtguard/deploy
cp .env.example .env                      # sửa WAZUH_NET, WAZUH_CERTS (thư mục có root-ca.pem), VTG_BIND, VTG_PORT
mkdir -p secrets && cp vtguard.env.example secrets/vtguard.env
nano secrets/vtguard.env                  # điền VTG_INDEXER_PASSWORD
chown 1000:1000 secrets/vtguard.env && chmod 600 secrets/vtguard.env   # container chạy user vtguard (uid 1000), không phải root
ls "$(grep WAZUH_CERTS .env | cut -d= -f2)/root-ca.pem"   # CA của wazuh-docker phải tồn tại
docker compose config >/dev/null && echo "compose hop le"
```

**Quyền file:** container chạy bằng user `vtguard` (uid 1000) nên mọi file mount vào phải đọc được bởi uid 1000 — nếu không sẽ gặp
`PermissionError: [Errno 13] Permission denied: '/secrets/vtguard.env'`. Với `root-ca.pem`: nếu `ls -ln` cho thấy thuộc `0 0` và chỉ
root đọc được, **không đổi quyền chứng chỉ của Wazuh** mà chép một bản riêng (chứng chỉ CA là công khai):
`mkdir -p certs && cp <WAZUH_CERTS>/root-ca.pem certs/ && chown -R 1000:1000 certs`, rồi đặt `WAZUH_CERTS=<thư mục deploy>/certs` trong `.env`.

`secrets/vtguard.env` dùng `VTG_INDEXER_URL=https://wazuh.indexer:9200`: trong mạng Docker của Wazuh, tên này trùng CN chứng chỉ
nên **kiểm TLS đầy đủ** (không cần `VTG_INDEXER_CHECK_HOSTNAME=0` hay `INSECURE`). `.env` và `secrets/` nằm ngoài git.

## 4. Kiểm tra kết nối rồi khởi động

```bash
docker compose run --rm vtguard-live stream --env-file /secrets/vtguard.env --check
```

Kỳ vọng: `version` 2.x, `user` = `vtguard`, `roles` có `vtguard_role`, DC01 và WIN10-01 có `events_last_min` > 0, `latest` cách
hiện tại khoảng 1 phút. Sau đó:

```bash
docker compose up -d
docker compose ps                         # cả hai container "healthy" sau 1–2 phút
docker compose logs -f vtguard-live       # "[live] bat dau -> ..." và không có lỗi lặp
```

Mở `http://10.20.30.10:8501` từ máy trong lab: ô **Luồng** = TRỰC TIẾP, panel **Hạ tầng** hiện DC01, WIN10-01 với số event tăng,
biểu đồ **Lưu lượng event** chạy. Trang không còn nút “Phát lại log mẫu” (`VTG_DISABLE_REPLAY=1` — không cho ghi đè cảnh báo thật).

## 5. Hiển thị cảnh báo VT-Guard trong Wazuh Dashboard

`vtguard-live` mặc định ghi ngược `vtguard-alerts-YYYY.MM.DD` (`VTG_PUSH=--push-alerts` trong `.env`; tắt bằng `--no-push-alerts`).
Trong Wazuh Dashboard (`https://10.20.30.10`): **Dashboards Management → Index patterns → Create** `vtguard-alerts-*`, trường thời
gian `@timestamp` → **Discover**. Lọc gợi ý: `decision_source: both` (ưu tiên cao), `ttps: T1003.003`.

## 6. Vận hành ổn định

| Cơ chế | Cách làm | Kiểm tra |
|---|---|---|
| Tự khởi động lại | `restart: unless-stopped` cho cả hai container; khởi động lại máy → Docker bật lại | `docker compose ps` |
| Không mất / không trùng sự kiện | checkpoint (timestamp + `_id` tại mốc) ghi sau mỗi chu kỳ vào volume `vtguard_live` | khởi động lại `vtguard-live`, `status.json` tiếp tục từ mốc cũ |
| Indexer chập chờn | thử lại 5 → 10 → 20 → 60 s, giữ checkpoint; sai mật khẩu / thiếu quyền (401/403) thì dừng hẳn và báo rõ | log `[live] Indexer tam loi …`, trường `errors` trong `status.json` |
| Healthcheck | luồng: `status.json` cập nhật trong ≤ 3 chu kỳ + 60 s; dashboard: HTTP `/_stcore/health` | `docker inspect --format '{{.State.Health.Status}}' vtguard-live` |
| Bộ nhớ khi chạy nhiều ngày | dọn trạng thái tiến trình cũ hơn `VTG_STATE_TTL_H` = 12 h (đã kiểm: không đổi kết quả); khử trùng lặp ≤ 300 000 khoá; giới hạn RAM 1 GB / 768 MB | `docker stats vtguard-live` |
| Dashboard nhẹ | chỉ đọc 3 000 cảnh báo mới nhất (`VTGUARD_LIVE_MAX`) | trang Trực tiếp tải < 2 s |
| Log container | json-file, 5 × 20 MB mỗi container | `docker compose logs --tail 50` |
| Đồng hồ | NTP trên VT-SIEM01, `w32tm` trên DC01/WIN10-01 (độ trễ hiển thị dựa trên giờ máy phát sinh) | đồng hồ độ trễ trên dashboard < 2 phút |

Lệnh thường dùng:

```bash
docker compose exec vtguard-live /app/docker/entrypoint.sh health live      # KHOE: ... event, cua so, canh bao, loi Indexer
docker compose restart vtguard-live                                          # đọc tiếp từ checkpoint
# BẮT ĐẦU LẠI từ bây giờ (xoá checkpoint + cảnh báo cũ, vd trước buổi demo): dừng luồng, xoá trạng thái, chạy lại
docker compose stop vtguard-live
docker compose run --rm --entrypoint sh vtguard-live -c "rm -f /app/reports/step9/live/connector_state.json /app/reports/step9/live/alerts.jsonl /app/reports/step9/live/status.json"
docker compose up -d vtguard-live
docker run --rm -v vtguard_vtguard_live:/v -v "$PWD":/b alpine tar czf /b/vtguard_live_$(date +%F).tgz -C /v .   # sao lưu volume
```

Nâng cấp phiên bản: `docker load` image mới → `docker compose up -d` (volume giữ nguyên checkpoint và cảnh báo).
Gỡ bỏ: `docker compose down` (giữ dữ liệu) hoặc `docker compose down -v` (xoá cả volume); xoá user `vtguard` và role trong Indexer.

## 7. Xử lý sự cố

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `PermissionError: … /secrets/vtguard.env` (hoặc root-ca.pem) | file thuộc root, quyền 600; container chạy uid 1000 | `chown 1000:1000 secrets/vtguard.env`; chép `root-ca.pem` ra `certs/` (mục 3) |
| `--check` báo 401 / 403 | sai mật khẩu, chưa gán role | làm lại mục 2; `authinfo` phải có `vtguard_role` |
| `CERTIFICATE_VERIFY_FAILED` | sai đường dẫn `WAZUH_CERTS` hoặc URL không phải `wazuh.indexer` | kiểm `root-ca.pem`; container phải ở mạng `WAZUH_NET` |
| `Name or service not known: wazuh.indexer` | sai `WAZUH_NET` | `docker network ls`, sửa `.env` |
| `events_last_min` = 0 | agent mất kết nối / archives tắt | `agent_control -l` trong manager; mục 0 |
| Luồng chạy nhưng không có cảnh báo khi demo | sự kiện chưa tới Indexer (trễ 40–60 s) hoặc cửa sổ chưa đóng (chờ host im lặng 30 s) | chờ thêm 1–2 phút; xem `status.json` (events_read tăng?) |
| Độ trễ hiển thị hàng chục phút | đồng hồ DC01 lệch sau khôi phục snapshot | `w32tm /resync /force` trên DC01 trước mỗi màn demo |
| Cổng 8501 bận | dịch vụ khác | đổi `VTG_PORT` trong `.env` (vd 8601) rồi `docker compose up -d` |
