# VT-Guard — Quy tắc gán nhãn (v0)

Mục tiêu: gán nhãn **chính xác, không rò rỉ, tái lập được**. Nhãn đến từ
**manifest phiên chạy** (Bước 2) nối với **cây tiến trình**, KHÔNG từ regex
trên command line (regex sẽ làm "luật tự sinh" chỉ tìm lại chính regex đó).

## 1. Đơn vị dữ liệu
- **Event**: 1 dòng chuẩn hoá.
- **Phiên (run)**: một lần chạy kịch bản (tấn công/benign) do manifest mô tả,
  gồm run_id, host, user, danh sách TTP, t_start, t_end, biến thể.
- **Cửa sổ (window)**: đơn vị phát hiện, cắt ở Bước 4 — theo (host, user), trượt
  theo thời gian. Nhãn cửa sổ = hợp các nhãn event trong cửa sổ.

## 2. Xương sống: cây tiến trình từ Sysmon EID 1
- Mỗi process-create (Sysmon 1) có `process_guid` + `parent_process_guid`.
  Dựng rừng cây: con trỏ về cha qua GUID.
- Một phiên tấn công bắt đầu từ **tiến trình gốc** (ví dụ cmd/powershell do
  bộ điều phối khởi chạy có đánh dấu). Mọi tiến trình **con cháu** của gốc trong
  khoảng [t_start, t_end] nhận nhãn TTP của phiên.

## 3. Nối các event không có processGuid
| Loại event | Cách nối vào cây |
|---|---|
| Sysmon 3 (network), 22 (DNS) | có process_guid → nối thẳng |
| Security 4688 | nối Sysmon 1 cùng `(host, process_id, |Δt|<2s)`; nếu trùng, lấy GUID của Sysmon 1 |
| PowerShell 4103/4104 | nối tiến trình powershell/pwsh cùng `(host, system.processID)` đang sống tại thời điểm đó |
| 4624/4634/4672 (logon) | nối theo `logon_id`/`target_logon_id`; gán cho phiên nếu logon_id khớp phiên |

## 4. Nhãn
- `label_malicious`: true nếu event thuộc cây tiến trình của một phiên tấn công.
- `label_ttps`: danh sách (đa nhãn) các TTP của phiên đó — **sigmoid, không softmax**
  (một phiên có thể mang nhiều TTP; T1016/T1049/T1018 hay đi cùng nhau).
- `label_source`: "manifest" (tin cậy cao) hoặc "inferred_tree".
- Event benign hoặc nền: label_malicious=false, label_ttps=[].

## 5. Chống rò rỉ nhãn (BẮT BUỘC)
1. **Loại tiến trình điều phối**: mọi event có process_guid thuộc cây của bộ
   điều phối (orchestrator) bị loại khỏi dataset, kể cả 4104 chứa tên TTP.
2. **Không đối xứng tài khoản**: tấn công và benign phải chạy trên **cùng tập
   user** (cả user01 lẫn admin01), nếu không mô hình học tên tài khoản.
3. **Không dùng làm feature**: run_id, đường dẫn script, tên máy điều phối,
   wazuh_rule_*, và script_block_text thô.
4. **Hard negatives**: phiên admin hợp lệ dùng ĐÚNG công cụ của 5 TTP phải
   được gán benign — đây là tập test khó nhất.

## 6. Kiểm chứng nhãn (sau Bước 3)
- Đếm phiên theo TTP, theo host, theo user → phải cân đối.
- Lấy ngẫu nhiên 20 phiên, truy ngược event→manifest bằng tay để xác nhận.
- Báo cáo tỉ lệ event "inferred_tree" so với "manifest".
