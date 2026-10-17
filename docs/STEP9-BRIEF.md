# VT-Guard — Bàn giao & đặc tả BƯỚC 9 (Dashboard SOC + demo trực tiếp + đóng gói Docker)

Tự chứa. Đọc cùng `reports/step8_report.md`, `reports/step8/alerts_<split>.jsonl`, `src/pipeline/infer.py`,
`src/rules/apply.py`, `rules/sigma/`, `reports/step7/rules_provenance.json`, `reports/dataset_card.md`
và các `reports/step{5,6,7,8}_results.json`.

## 0. Bối cảnh — HAI KIỂU DEMO
Cả 3 yêu cầu môn học đã có bằng chứng (Bước 6, 7, 8). Bước 9 KHÔNG huấn luyện thêm, KHÔNG đổi kết quả nào.
Bước 9 làm hai thứ phục vụ hai mục đích khác nhau:

- **Kiểu A — Docker offline cho giảng viên (đã gần xong).** Image chạy trên artefact đã đóng băng, không cần lab,
  không cần Internet. Lệnh `verify` chạy lại và ra đúng số liệu trong báo cáo. Đây là bằng chứng chạy-lại-được.
  Mọi con số CHÍNH THỨC lấy từ đây. Phần này giữ như cũ, chỉ hoàn thiện (mục 6).
- **Kiểu B — Dashboard SOC + demo trực tiếp trong lab (TRỌNG TÂM BƯỚC 9).** Đây là phần lấy điểm trước hội đồng.
  VT-Guard chạy như một lớp phân tích gắn thêm vào Wazuh, xử lý log thật gần thời gian thực, và dashboard hoạt
  động giống một màn hình SOC. Kịch bản demo (mục 4) phải làm bật được 3 yêu cầu đề tài VÀ chỉ ra chỗ Wazuh mù
  mà VT-Guard thấy. Hạn 01/11/2026.

## 1. Nguyên tắc chung của dashboard
- **Tiếng Việt hoàn toàn.** Mọi nhãn, tiêu đề, nút, chú thích, thông báo đều tiếng Việt có dấu. Mã MITRE
  (T1016, T1003.003...) và tên kỹ thuật giữ nguyên, nhưng kèm mô tả tiếng Việt ngắn. Không để lẫn chuỗi tiếng Anh
  của thư viện ra giao diện.
- **Trực quan, không rối.** Mỗi trang có đúng một thông điệp chính. Ưu tiên bảng gọn, nhãn màu mức độ, vài con số
  lớn dễ đọc. KHÔNG nhồi mọi chỉ số lên màn hình. Chi tiết kỹ thuật đặt sau một cú bấm (mở rộng / trang chi tiết),
  không bày hết ra trang đầu. Tông màu SOC: nền tối, cảnh báo cao = đỏ/cam, cần xem lại = vàng, bình thường = xám.
- **Giống SOC thật.** Màn hình chính là HÀNG ĐỢI CẢNH BÁO tự cập nhật, sắp theo mức ưu tiên và thời gian, mỗi
  dòng một cảnh báo, bấm vào để điều tra (triage). Đây là nhịp làm việc của một analyst.
- **Chỉ đọc artefact đã đóng băng.** Dashboard không tự tính lại chỉ số. Chế độ đánh giá chỉ hiển thị lại số đã
  chấm ở Bước 5–8.
- Code: `dashboard/app.py`, `dashboard/pages/`, `dashboard/data.py`. Mọi đường dẫn qua `VTGUARD_HOME`, không
  hard-code đường dẫn Windows, để chạy được cả trên host, trong container và khi nối Wazuh.
- **Hai chế độ:** *vận hành* (mặc định; KHÔNG hiện nhãn đúng/sai, giống SOC thật đang trực) và *đánh giá* (công tắc
  bật; hiện TP/FP và bảng chỉ số, dùng khi trình bày định lượng). Giao diện ghi rõ đang ở chế độ nào.

## 2. Chế độ VẬN HÀNH TRỰC TIẾP (kiểu B) — VT-Guard nằm ở đâu trong hạ tầng
Luồng: agent Wazuh (DC01, WIN10-01) → Manager + Indexer trên VT-SIEM01 (giữ nguyên) → **container VT-Guard chạy
chế độ `live`** đọc log thật, chấm, và đẩy cảnh báo ra dashboard (và tuỳ chọn ra chính Wazuh).

**2.1 Thành phần mới (code duy nhất phải viết mới cho kiểu B)**
- `src/live/connector.py`: mỗi ~10–15 giây đọc event MỚI trong `wazuh-archives-*` qua REST API Indexer (tái dùng
  logic truy vấn của `export_batch.py`, chỉ lấy phần sau mốc đã đọc). Thông tin đăng nhập nạp lúc chạy (mục 5).
- `src/live/windower.py`: **bộ chia cửa sổ trực tiếp.** Lúc chạy thật KHÔNG có manifest/nhãn phiên như khi tạo
  dataset, nên gom event theo (host + thời gian), tối đa 64 event/cửa sổ; đóng cửa sổ khi đủ 64 event hoặc host
  im lặng quá ngưỡng thời gian. **Tiền xử lý phải GIỐNG HỆT lúc tạo dataset:** cùng `normalize.py` (v1), cùng quy
  tắc loại event nền đã ghi trong dataset card; không thêm/bớt quy tắc để demo đẹp hơn.
- Phần còn lại gọi lại nguyên `infer.py`: `featurize.py` (vocab đóng băng) → ONNX VT-Seq-ens → matcher Sigma
  (`apply.py`) → fusion F3-B (cấu hình đã khoá) → `alerts.jsonl` đúng schema Bước 8.
- **Tuỳ chọn, NÊN làm (điểm "tích hợp hạ tầng" dễ thấy nhất):** ghi cảnh báo ngược vào index riêng
  `vtguard-alerts-*` trên Indexer, để cảnh báo VT-Guard hiện ngay trong Wazuh Dashboard cạnh cảnh báo gốc.

**2.2 Trang "Trực tiếp" trên dashboard**
- Tự làm mới (auto-refresh) đọc `alerts.jsonl` đang được chế độ live ghi; cảnh báo mới trôi lên đầu hàng đợi.
- Có đồng hồ độ trễ: thời gian Wazuh nhận log (thường 40–60 s) + chu kỳ đọc + chờ đóng cửa sổ. Suy luận ~3 ms/cửa sổ.
  Hiển thị để hội đồng hiểu vì sao cảnh báo xuất hiện sau ~1 phút.

**2.3 Chế độ `replay` (DỰ PHÒNG BẮT BUỘC cho buổi bảo vệ)**
- Ghi lại log một lần chạy thử thành công thành file, rồi `replay` phát lại qua ĐÚNG pipeline trực tiếp
  (connector đọc từ file thay vì Indexer). Nếu lab trục trặc hôm bảo vệ, vẫn demo được luồng trực tiếp mà không
  phụ thuộc mạng/VM. Đây là lưới an toàn, không phải để thay demo thật.

## 3. Các trang dashboard (giữ gọn, đúng nhịp SOC)
Năm màn hình, không hơn. Ưu tiên ít trang, mỗi trang rõ một việc.

1. **Trực tiếp / Hàng đợi cảnh báo (màn hình chính):** dải số trên cùng (số cảnh báo đang mở, phân bố nguồn
   `cả hai`/`chỉ AI`, độ trễ hiện tại). Bên dưới là bảng cảnh báo: thời gian, host, điểm, TTP (mã + mô tả Việt),
   **mức ưu tiên** (`cả hai nguồn` = CAO đỏ, `chỉ AI` = CẦN XEM LẠI vàng), nguồn quyết định. Lọc/sắp theo cột.
   Bấm một dòng → mở Chi tiết.
2. **Chi tiết cảnh báo (triage):** một màn hình kể trọn một cảnh báo, phục vụ cả 3 yêu cầu cùng lúc:
   - Điểm AI so với ngưỡng, kết luận đa nhãn TTP — *(yêu cầu 3: mô hình chuỗi tùy biến)*.
   - Luật Sigma khớp: xem YAML + **xuất xứ** (cửa sổ/phiên Train sinh ra luật, support/precision) —
     *(yêu cầu 1: luật tự sinh có provenance)*.
   - Nguồn quyết định `cả hai`/`chỉ AI`/`chỉ luật` và vì sao — *(yêu cầu 2: fusion)*.
   - Top-5 event theo attention (chỉ số event + trường quan sát được), giải thích "vì sao AI báo".
3. **Dòng thời gian sự cố:** gom cảnh báo theo host + phiên thành một chuỗi TTP theo thời gian, gắn mã MITRE.
   Đây là câu chuyện tấn công hoàn chỉnh — thứ Wazuh rời rạc không dựng được.
4. **So sánh & Đánh giá (chế độ đánh giá):** bảng B0 (luật Wazuh) ↔ VT-Seq-ens ↔ fusion trên 3 tập test;
   chuỗi ablation; bảng Holm. Đọc từ results JSON. Mỗi bảng một câu kết luận tiếng Việt ("Wazuh mù 3 TTP này",
   "fusion không kém AI về recall, thắng về minh bạch"). Ghi chú "mô tả, mẫu nhỏ" ở chỗ CI rộng.
5. **Luật Sigma:** 11 luật, mã TTP, vị từ, support/precision Train/OOF, provenance, tải YAML. Cho thấy luật
   là tự sinh có kiểm định, không viết tay.

Trang "Tổng quan" cũ gộp thành dải số đầu trang 1, không làm trang riêng, để bớt rối.

## 4. KỊCH BẢN DEMO TRỰC TIẾP (kiểu B) — phần lấy điểm
Mục tiêu: trong ~10–12 phút, mỗi màn vừa chứng minh một yêu cầu đề tài, vừa đặt Wazuh và VT-Guard cạnh nhau.
Mở SONG SONG hai màn hình: **Wazuh Dashboard** (bên trái) và **VT-Guard Dashboard chế độ Trực tiếp** (bên phải).
Mọi bước tấn công thực thi QUA Atomic Red Team theo test ID, trên lab cô lập (không tự viết lệnh tấn công).

**Màn 0 — Chuẩn bị (30 s).** Revert snapshot về trạng thái sạch. Bật connector + dashboard live. Nói rõ:
"Hai bên nhận cùng một nguồn log từ cùng các agent; khác nhau là ở lớp phân tích."

**Màn 1 — Không gây nhiễu (phản chứng, ~1 phút).** Chạy hoạt động quản trị LÀNH TÍNH (chính các script
hard-negative đã dùng tạo dataset: `admin_net_sweep`, `dc_db_maint`...). Kỳ vọng: VT-Guard KHÔNG cảnh báo.
→ Thông điệp: FPR thấp trên hành vi quản trị thật (dẫn số T-hard 1/88 ở trang Đánh giá). Một IDS hay cảnh báo
nhầm là vô dụng trong SOC; VT-Guard im lặng đúng lúc.

**Màn 2 — LOTL discovery mà luật Wazuh mù (~3 phút) → YÊU CẦU 1 + 3.** Chạy ART cho chuỗi discovery
(T1016 / T1018 / T1087.002 / T1654). Đây là lệnh hệ thống hợp lệ (net, nltest, nslookup...), nên:
- **Wazuh (trái):** không có cảnh báo hành vi tương ứng — đúng với kết quả B0 (luật có sẵn mù các TTP này).
  Chỉ ra màn Wazuh trống để hội đồng tự thấy.
- **VT-Guard (phải):** cảnh báo xuất hiện sau ~1 phút. Bấm vào → trang Chi tiết: luật Sigma tự sinh khớp kèm
  **xuất xứ** (yêu cầu 1) và top-5 event attention (yêu cầu 3, mô hình chuỗi tùy biến hiểu được chuỗi lệnh LOTL).

**Màn 3 — Dump NTDS T1003.003 (~2 phút) → YÊU CẦU 2 (fusion).** Chạy ART cho T1003.003. Mở Chi tiết một cảnh báo
NTDS: cho thấy nguồn quyết định `cả hai` — AI bắt theo chuỗi hành vi, luật Sigma bắt theo cây tiến trình
(`ntdsutil ... ifm ... create full` / `vssadmin ... create shadow`), và luật của ta KHÔNG dựa vào dấu vết scaffold
(giải thích ngắn danh sách vị từ cấm). → Thông điệp: hai nguồn độc lập cùng xác nhận → cảnh báo độ tin cao, lại
có giải thích được. Đây chính là giá trị của fusion so với chỉ-AI (hộp đen) hay chỉ-luật (phủ hẹp).

**Màn 4 — Dòng thời gian sự cố (~1,5 phút).** Mở trang Dòng thời gian: chuỗi TTP theo host dựng lại cả chiến dịch
từ discovery → thu thập NTDS. → Thông điệp: Wazuh cho các alert rời rạc; VT-Guard kể một câu chuyện tấn công.
Nếu đã bật ghi ngược `vtguard-alerts-*`: chuyển sang Wazuh Dashboard chỉ cùng cảnh báo đó nằm trong index của ta,
chứng minh tích hợp vào hạ tầng sẵn có.

**Màn 5 — Định lượng (~2 phút, chế độ đánh giá).** Bật công tắc đánh giá, mở trang So sánh:
- Bảng B0 (Wazuh) vs VT-Seq vs fusion: Wazuh mù T1016/T1654/T1003; VT-Seq phủ được, T-hard FPR ~1/88;
  fusion không kém AI về recall, thắng rõ về precision khi cả hai nguồn khớp (76/76) và về minh bạch.
- Một bảng ablation + Holm để chứng minh mô hình tùy biến (yêu cầu 3) hơn baseline GRU trơn sau hiệu chỉnh.

**Chốt (30 s).** Một câu: Wazuh là SIEM thu thập và luật tĩnh; VT-Guard thêm lớp phát hiện APT kiểu LOTL thích ứng,
có mô hình chuỗi tùy biến + luật tự sinh có xuất xứ + hợp nhất hai nguồn, chạy ngay trên hạ tầng Wazuh hiện có.

**Trung thực khi trình bày (BẮT BUỘC, tránh bị hội đồng bắt lỗi):**
- Demo trực tiếp là minh hoạ VẬN HÀNH, không phải đánh giá. Cửa sổ lúc chạy thật chia theo thời gian, cửa sổ trong
  dataset dựa trên manifest phiên → điểm có thể lệch. **Số liệu chính thức là kết quả trên tập test đã đóng băng.**
- Sự tương phản với Wazuh phải LẤY TỪ kết quả B0 thật, không dàn dựng. Nói "theo baseline B0 của chúng tôi, luật
  Wazuh có sẵn không phủ các TTP này", không nói "Wazuh không bao giờ bắt được".
- Chênh lệch tiền xử lý: nếu ở chế độ trực tiếp không loại được đúng các event nền mà pipeline train đã loại, phân
  phối sẽ lệch. Giảm thiểu bằng cách chạy tấn công từ console bình thường và lọc công cụ demo đã biết; và đo trước
  (mục 6.3).

## 5. Thông tin đăng nhập & an toàn (kiểu B)
- Tạo tài khoản Indexer RIÊNG cho VT-Guard: chỉ đọc `wazuh-archives-*`, chỉ ghi `vtguard-alerts-*` (nếu dùng mục 2.1).
- Mật khẩu + chứng chỉ CA nạp lúc chạy bằng `--env-file` và mount từ ngoài. **KHÔNG bao giờ đưa vào image.**
- Container chỉ nối mạng lab, không mở cổng ra ngoài; dashboard chỉ mở trên máy trình chiếu.
- Mọi bước tấn công qua Atomic Red Team theo test ID trên lab cô lập.

## 6. Đóng gói Docker (kiểu A — BẮT BUỘC, giữ như cũ)
Giảng viên không có lab. Image chạy hoàn toàn trên artefact đã đóng băng.

**6.1 Nội dung image**
- Runtime gọn: Python 3.12-slim + onnxruntime, numpy, pandas, pyyaml, pySigma (nếu dùng), streamlit. Ghim phiên bản
  trong `docker/requirements.lock`. KHÔNG cần PyTorch (suy luận bằng ONNX).
- Code: `src/` (pipeline, eval, rules, fusion, **live**), `dashboard/`.
- Artefact: `models/*.onnx`, `rules/sigma/`, provenance, `vocab.json`, split/windows của 3 tập test,
  `reports/` (results JSON, preds, alerts), một file log mẫu cho `replay`. Ghi sha256 vào `docker/MANIFEST.json`.
- KHÔNG đưa vào image: log thô, checkpoint `.pt`, mọi thông tin đăng nhập. Thêm `.dockerignore` + bước quét tự động.

**6.2 Entrypoint (các lệnh con)**
- `dashboard` (mặc định): mở dashboard cổng 8501, chế độ đọc alerts đã đóng băng.
- `verify`: chạy lại `infer.py` + `evaluate.py` trên 3 tập test, so số liệu báo cáo, in ĐẠT/KHÔNG ĐẠT (0 lệch).
- `infer --input <file>`: chạy pipeline trên file cửa sổ người dùng cung cấp (mount), xuất alerts.
- `replay --input <log>`: phát lại log mẫu qua pipeline trực tiếp để xem luồng kiểu B mà không cần lab.
- `live --env-file <...>`: (chỉ dùng trong lab) nối Indexer thật, chế độ trực tiếp. Giảng viên không cần lệnh này.
- `selftest`: unit test không cần GPU.

**6.3 Kiểm thử & độ lệch**
- Build `linux/amd64`; xuất `vtguard.tar` bằng `docker save` (repo private, không phụ thuộc registry). Ghi kích
  thước + sha256. Hỏi trước kiến trúc máy giảng viên; nếu Apple Silicon, dựng thêm `linux/arm64`.
- `verify` chạy với `--network none` để chứng minh offline; kết quả trong container trùng host (0 lệch).
- Quét image: 0 file log thô / `.pt` / thông tin đăng nhập.
- **Đo độ lệch trực tiếp↔offline:** cho `windower` chạy trên một batch đã export sẵn rồi so quyết định với pipeline
  offline (tỉ lệ cửa sổ cảnh báo trùng; số cảnh báo sai trên phần lành tính). Đưa con số vào hạn chế — đây là câu
  trả lời cho "chạy thật có khác không".
- `README_DOCKER.md`: 3 lệnh chính, yêu cầu máy, thời gian chạy, cách đọc kết quả `verify`.

## 7. Tiêu chí chấp nhận Bước 9
1. Dashboard tiếng Việt hoàn toàn, 5 trang gọn, hai chế độ tách bạch; số liệu trùng artefact (test 0 lệch).
2. Chế độ `live` chạy được trong lab: đọc `wazuh-archives-*` → cảnh báo lên trang Trực tiếp; (tuỳ chọn) ghi
   `vtguard-alerts-*`. `replay` phát lại được luồng này không cần Indexer.
3. Kịch bản demo kiểu B (mục 4) chạy trọn, mỗi màn gắn đúng một yêu cầu + một tương phản với Wazuh.
4. Docker kiểu A: image build được, `verify` ĐẠT với `--network none`; không chứa log thô/checkpoint/đăng nhập.
5. `vtguard.tar` + `README_DOCKER.md` + `docker/MANIFEST.json` + báo cáo độ lệch trực tiếp↔offline.
6. `reports/step9_report.md` ngắn + ảnh chụp từng trang (`reports/step9/screenshots/`). Commit, push, tag `step9-done`.

## 8. Thứ tự thực hiện (DỪNG mỗi mốc để tôi duyệt)
1. `dashboard/data.py` + trang Trực tiếp/Hàng đợi + Chi tiết + test số liệu (đọc alerts đóng băng). **DỪNG — gửi ảnh.**
2. Dòng thời gian + So sánh/Đánh giá + Luật. Chuẩn hoá tiếng Việt toàn bộ. **DỪNG — gửi ảnh.**
3. `src/live/connector.py` + `windower.py` + chế độ `replay` + đo độ lệch trực tiếp↔offline. **DỪNG — gửi số liệu.**
4. (Trong lab, bạn tự chạy) nối Indexer thật, chạy thử kịch bản mục 4, ghi log mẫu cho `replay`; tuỳ chọn ghi
   `vtguard-alerts-*`. **DỪNG — gửi ảnh Wazuh ↔ VT-Guard song song.**
5. Docker: Dockerfile, entrypoint (gồm `replay`/`live`), kiểm offline, quét file nhạy cảm, `vtguard.tar`. **DỪNG.**
6. `step9_report.md` + ảnh, tag `step9-done`.

Seed 1337. ASCII trong code (giao diện hiển thị tiếng Việt UTF-8; nguồn Python chỉ chú thích/chuỗi hiển thị dùng
tiếng Việt, logic ASCII). Không huấn luyện thêm, không đổi kết quả, không dời tag.

## 9. Lộ trình đến hạn
| Ngày | Việc |
|---|---|
| 18–20/10 | Mốc 1–2: dashboard SOC tiếng Việt (5 trang) |
| 21–22/10 | Mốc 3–4: chế độ trực tiếp + replay + chạy thử kịch bản demo trong lab |
| 23/10 | Mốc 5: Docker + chạy thử máy sạch |
| 24–28/10 | Bước 10: báo cáo cuối (tiếng Việt có dấu) |
| 29/10 | Slide bảo vệ + tổng duyệt kịch bản demo kiểu B |
| 30–31/10 | Dự phòng, rà soát, nộp |
