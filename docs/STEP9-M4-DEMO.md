# VT-Guard — Bước 9 mốc 4 (phần 2): kịch bản demo trước hội đồng

Mục tiêu: trong ~12–15 phút, chứng minh **Wazuh không bắt được hành vi (không gán đúng kỹ thuật), còn VT-Guard bắt được**, và
làm nổi cả ba yêu cầu đề tài. Mọi bước tấn công chạy **qua Atomic Red Team bằng bộ điều phối** `orchestrator/Invoke-VTSession.ps1`
(uỷ quyền cho ART, ghi manifest — không có lệnh tấn công trong repo), trong lab cô lập.

## 0. Vì sao tương phản là thật, không dàn dựng

Phân tích trên **chính dữ liệu đã thu** cho thấy luật Wazuh có sẵn **gán sai kỹ thuật** cho các hành vi LOTL này (baseline B0 trong
báo cáo: macro-F1 theo kỹ thuật chỉ 0,12; F1 = 0 ở T1016, T1018, T1654, T1003.003). Khi có bắn, Wazuh chủ yếu bắn các luật chung
cấp thấp theo tên tiến trình, **gắn nhầm sang kỹ thuật khác** (Bảng dưới) — không cho biết kẻ tấn công đang làm gì:

| Hành vi (TTP thật) | Luật Wazuh hay bắn | Mức | ATT&CK Wazuh gán | Đúng kỹ thuật? |
|---|---|---|---|---|
| Dò cấu hình mạng (T1016) | 92052 *Windows command prompt started by an abnormal process* | 4 | T1059.003 (Command Shell) | **Sai** |
| Dò máy trong mạng (T1018) | 92052; 91816 *PowerShell querying system env vars* | 4 | T1059.003 / T1082 | **Sai** |
| Liệt kê tài khoản miền (T1087.002) | 92103 *LDAP activity from PowerShell* (thỉnh thoảng) | 6 | T1018 | gần đúng nhầm sang T1018 |
| Liệt kê nhật ký (T1654) | 92052; 91816 | 4 | T1059.003 / T1082 | **Sai** |
| Trích xuất NTDS (T1003.003) | 92052 | 4 | T1059.003 | **Sai** (không nhận ra credential dumping) |

Nghĩa là Wazuh chỉ thấy “một shell bất thường chạy” (mức 4), **không nhận ra chuỗi trinh sát hay việc trích xuất CSDL tài khoản
miền**. VT-Guard gán đúng kỹ thuật và dựng được chuỗi tấn công. **Chốt trung thực để nói trước hội đồng:** “theo baseline B0 của
chúng tôi, luật Wazuh có sẵn không gán được 4/5 kỹ thuật này; có bắn thì chỉ là luật chung cấp thấp và gắn nhầm sang kỹ thuật khác.”

## 1. Chuẩn bị (màn 0, ~1 phút)

- Khôi phục snapshot sạch cho các máy sẽ demo; `w32tm /resync /force` trên DC01.
- Trên VT-SIEM01: `docker compose ps` — `vtguard-live` và `vtguard-dashboard` đều *healthy* (mục triển khai).
- Mở **song song hai màn hình**: trái = Wazuh Dashboard (`https://10.20.30.10`, Discover trên `wazuh-alerts-*`, lọc theo agent và
  khung giờ); phải = VT-Guard (`http://10.20.30.10:8501`, trang **Trực tiếp · Hàng đợi**).
- Thư mục manifest: mỗi phiên dưới đây ghi một `*.manifest.json` vào `C:\VT-Guard-runs`; sau buổi demo chép về
  `deploy/demo/` trên VT-SIEM01 để sinh báo cáo đối chiếu (mục 4).
- Nói: “Hai bên nhận **cùng một nguồn log** từ cùng các agent; khác nhau là ở lớp phân tích.”

## 2. Các kịch bản demo

Mỗi kịch bản là một phiên của bộ điều phối. `Invoke-VTSession.ps1` nằm ở `C:\VT-Guard\orchestrator` trên máy chạy (WIN10-01 cho
Discovery, DC01 cho NTDS). Chạy PowerShell **Administrator**. Kỳ vọng VT-Guard: cảnh báo xuất hiện sau ~1 phút (trễ Wazuh 40–60 s +
chu kỳ đọc 12 s + chờ đóng cửa sổ).

### KB1 — Phản chứng: hoạt động quản trị hợp lệ (~1,5 phút) → độ tin cậy

Chạy đúng các script hard-negative đã dùng dựng dataset — quản trị viên thật làm việc với **cùng công cụ** của 5 kỹ thuật:

```powershell
.\Invoke-VTSession.ps1 -Class hard_negative -HostName WIN10-01 -User "VTLAB\admin01" -UserRole admin `
  -BenignTasks admin_net_sweep,user_inventory -Tempo burst
.\Invoke-VTSession.ps1 -Class hard_negative -HostName DC01 -User "VTLAB\admin01" -UserRole admin `
  -BenignTasks dc_db_maint -Tempo burst            # dùng ntdsutil, vssadmin HỢP LỆ (có khôi phục snapshot)
```

- **Kỳ vọng:** VT-Guard **KHÔNG cảnh báo** (hàng đợi đứng yên). Thông điệp: FPR thấp trên quản trị thật — dẫn số **T-hard 1/88** ở
  Phần B. Một IDS hay báo nhầm là vô dụng trong SOC; VT-Guard im lặng đúng lúc, kể cả khi admin dùng `ntdsutil`.
- Wazuh (trái): có thể bắn vài luật mức 4 (shell bất thường) — cho thấy luật tĩnh **không phân biệt** được admin với kẻ tấn công.

### KB2 — Trinh sát LOTL mà Wazuh gán sai (~3 phút) → YC1 + YC3

Chuỗi discovery bằng lệnh hệ thống hợp lệ (`scenarios.json`: T1016 test 1, T1018 test 3, T1087.002 test 1, T1654 test 2):

```powershell
.\Invoke-VTSession.ps1 -Class attack -HostName WIN10-01 -User "VTLAB\user01" -UserRole standard `
  -Ttps T1016,T1018,T1087.002,T1654 -TestNumbers 1,3,1,2 -Tempo burst -Variant mixed
```

- **Wazuh (trái):** không có cảnh báo hành vi tương ứng; nếu có chỉ là 92052 “abnormal process” gán T1059.003 — **sai kỹ thuật**.
- **VT-Guard (phải):** 4 kỹ thuật discovery lần lượt lên hàng đợi. Bấm một cảnh báo → trang **Chi tiết**: luật Sigma tự sinh khớp
  kèm **xuất xứ** (YC1, ví dụ `VTR-T1018-02` từ `nltest`+`%USERDNSDOMAIN%`), và **top-5 event theo attention** (YC3 — mô hình chuỗi
  hiểu trình tự lệnh LOTL). Dải “ba yêu cầu đề tài” ngay trên cảnh báo.

### KB3 — Trinh sát chậm (low-and-slow) (~2 phút, tuỳ chọn) → độ bền theo thời gian

Volt Typhoon hành động rải rác để né phát hiện. Lặp KB2 với nhịp chậm, trên DC01, tài khoản admin:

```powershell
.\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User "VTLAB\admin01" -UserRole admin `
  -Ttps T1016,T1087.002 -TestNumbers 9,12 -Tempo low_and_slow -Variant powershell
```

- **Kỳ vọng:** VT-Guard vẫn gom đúng cửa sổ và cảnh báo dù các lệnh cách nhau 45–240 s (bộ chia cửa sổ đóng theo im lặng/khoảng
  trống). Thông điệp: không dựa vào “nhiều lệnh dồn dập” mà dựa vào **nội dung + trình tự**.

### KB4 — Trích xuất NTDS T1003.003 (~2 phút) → YC2 (hợp nhất)

Chỉ trên DC01, sau khi khôi phục snapshot:

```powershell
.\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User "VTLAB\admin01" -UserRole admin `
  -Ttps T1003.003 -TestNumbers 3 -SnapshotBefore "BASELINE-CLEAN" -Tempo burst
```

- **Wazuh (trái):** cùng lắm 92052 mức 4 — **không nhận ra đây là đánh cắp CSDL tài khoản miền**.
- **VT-Guard (phải):** mở Chi tiết một cảnh báo NTDS → nguồn quyết định **`cả hai` (AI + luật xác nhận)**: AI bắt theo chuỗi hành
  vi, luật `VTR-T1003003-01` bắt theo cây tiến trình (`ntdsutil … ifm … create full`), và luật **không dựa vào dấu vết scaffold**
  (danh sách vị từ cấm). Thông điệp: hai nguồn độc lập cùng xác nhận → cảnh báo độ tin cao, lại giải thích được — đây là giá trị
  của fusion so với chỉ-AI (hộp đen) hay chỉ-luật (phủ hẹp).

### KB5 — Biến thể chưa thấy: NTDS qua Shadow Copy (~2 phút, tuỳ chọn) → tổng quát hoá

Biến thể T1003.003 bằng `vssadmin create shadow` (test 1) — kỹ thuật này **không có trong tập huấn luyện** (chỉ ở T-novel):

```powershell
.\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User "VTLAB\admin01" -UserRole admin `
  -Ttps T1003.003 -TestNumbers 1 -SnapshotBefore "BASELINE-CLEAN" -Tempo burst
```

- **Kỳ vọng:** VT-Guard vẫn bắt (Phần B: 6/6 phiên biến thể này được phát hiện). Thông điệp: học hành vi nên tổng quát sang biến
  thể mới, không chỉ khớp một chữ ký. Lưu ý trung thực: luật khớp phần nào nhờ token chung `create`, còn AI bắt theo chuỗi.

### KB6 — Dòng thời gian sự cố (~1,5 phút) → câu chuyện tấn công

Mở trang **Dòng thời gian sự cố**: các cảnh báo của KB2–KB5 trên cùng host được gom thành **một sự cố** với chuỗi kỹ thuật theo
thời gian (discovery → NTDS), kèm chiến thuật MITRE. Thông điệp: Wazuh cho các alert rời rạc cấp thấp; VT-Guard **kể một câu chuyện
tấn công hoàn chỉnh**. Nếu bật ghi ngược: sang Wazuh Dashboard, index `vtguard-alerts-*` cho thấy **chính các cảnh báo đó nằm trong
hạ tầng Wazuh** — chứng minh tích hợp.

### KB7 — Định lượng (~2 phút) → cả ba yêu cầu

Chuyển sang **Phần B – Kết quả nghiên cứu** của dashboard: biểu đồ F1 theo kỹ thuật (Wazuh 0 ở 4/5 kỹ thuật ↔ VT-Guard phủ đủ),
bảng Holm (VT-Seq-ens > GRU thuần; F3-B > chỉ-luật), 101 cảnh báo có nhãn (nhóm `cả hai` đúng 76/76). Nhấn mạnh: **số liệu chính
thức là trên tập kiểm thử đã đóng băng**, demo trực tiếp chỉ minh hoạ vận hành.

## 3. Bảng tóm tắt kịch bản

| KB | Lệnh (lớp · host · TTP) | Wazuh | VT-Guard kỳ vọng | Yêu cầu |
|---|---|---|---|---|
| 1 | hard_negative · WIN10-01/DC01 · admin_net_sweep, user_inventory, dc_db_maint | vài luật mức 4 hoặc im | **không cảnh báo** | độ tin cậy (FPR thấp) |
| 2 | attack · WIN10-01 · T1016,T1018,T1087.002,T1654 | không gán đúng (92052 → T1059.003) | 4 kỹ thuật + luật Sigma + attention | YC1, YC3 |
| 3 | attack · DC01 · T1016,T1087.002 (low_and_slow) | tương tự KB2 | vẫn cảnh báo dù lệnh rải rác | độ bền thời gian |
| 4 | attack · DC01 · T1003.003 (ntdsutil) | 92052 mức 4 | nguồn `cả hai`, luật NTDS + AI | YC2 |
| 5 | attack · DC01 · T1003.003 test 1 (vssadmin) | 92052 mức 4 | bắt biến thể chưa thấy | tổng quát hoá |
| 6 | — | alert rời rạc | dòng thời gian một sự cố | câu chuyện tấn công |
| 7 | — (Phần B) | — | biểu đồ + Holm | cả ba |

## 4. Báo cáo đối chiếu sau buổi demo

Chép manifest các phiên demo về `deploy/demo/` trên VT-SIEM01 rồi sinh bảng đối chiếu tự động (đọc `wazuh-alerts-*` và cảnh báo
VT-Guard trong volume, so theo khung thời gian từng phiên):

```bash
docker compose run --rm -v "$PWD/demo:/demo:ro" vtguard-live \
  python src/live/demo_report.py --manifests /demo --env-file /secrets/vtguard.env --out /app/reports/step9/m4
# lấy kết quả ra host:
docker compose cp vtguard-live:/app/reports/step9/m4/demo_report.md ./demo_report.md
```

File `demo_report.md` cho mỗi phiên: số cảnh báo Wazuh (và mức ≥ 4), Wazuh có gán đúng TTP không, số cảnh báo VT-Guard (nguồn
`cả hai`), VT-Guard có gán đúng TTP không, và kết luận (“VT-Guard gán đúng, Wazuh không” / “VT-Guard im lặng (đúng)”…). Đây là bằng
chứng định lượng kèm theo ảnh chụp hai màn hình để đưa vào `reports/step9_report.md` và slide bảo vệ.

## 5. Trung thực khi trình bày (bắt buộc)

- Demo trực tiếp là minh hoạ **vận hành**, không phải đánh giá: cửa sổ trực tiếp chia theo thời gian, khác cửa sổ theo phiên của
  tập kiểm thử → điểm có thể lệch. **Số liệu chính thức là kết quả trên tập test đã đóng băng** (Phần B).
- Tương phản với Wazuh lấy từ **baseline B0 thật**, không dàn dựng: nói “luật Wazuh **có sẵn** không gán được các kỹ thuật này”,
  không nói “Wazuh không bao giờ bắt được” (có thể viết luật Wazuh thủ công cho từng kỹ thuật — nhưng đó chính là việc VT-Guard tự
  động hoá bằng luật Sigma tự sinh).
- Nếu chạy tấn công từ console tay (không qua bộ điều phối), tiền xử lý có thể lệch so với lúc tạo dataset; nên chạy qua
  `Invoke-VTSession.ps1` như trên và đo bằng `demo_report.py`.
