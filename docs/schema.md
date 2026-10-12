# VT-Guard — Schema chuẩn hoá sự kiện (v0)

Nguồn: `wazuh-archives-*` (Indexer), 1 document = 1 Windows event.
Đầu ra chuẩn hoá: **JSONL, mỗi dòng 1 event phẳng**. Tên trường cố định,
không phụ thuộc channel, để AI và bộ sinh luật dùng chung.

## Nguyên tắc
- **Không mất mát**: giữ mọi trường cần cho phát hiện; trường thừa bỏ qua.
- **Chống rò rỉ nhãn**: `wazuh_rule_*` tách riêng, CHỈ dùng cho baseline B0,
  **không bao giờ** đưa vào feature của AI hay điều kiện luật tự sinh.
- **PID chuẩn hoá về số nguyên**: Security ghi hex (`0x1b94`), Sysmon ghi thập phân.
- **Thời gian**: dùng `ts` (trường `timestamp` gốc, đã có offset `+0000`).

## Trường chính (nhóm)
| Nhóm | Trường | Nguồn gốc | Ghi chú |
|---|---|---|---|
| Định danh/thời gian | event_uid, ts, ts_system, host, host_role, agent_id, channel, event_id, provider, record_id | agent.*, data.win.system.* | host_role suy từ tên máy |
| Tiến trình | process_guid, parent_process_guid, process_id, parent_process_id, image, image_name, parent_image, parent_image_name, command_line, parent_command_line, original_file_name, integrity_level | data.win.eventdata.* | **Sysmon EID 1 là xương sống** (xem labeling.md) |
| Danh tính/logon | user, subject_user, subject_domain, subject_logon_id, target_user, target_domain, target_logon_id, logon_id, logon_type, logon_guid, auth_package | eventdata.* | 4624/4634/4672/4648 |
| Mạng/DNS | dst_ip, dst_port, dst_host, protocol, dns_query, dns_result | Sysmon 3/22 | có process_guid, nối thẳng vào cây |
| Script | script_block_text, ps_payload | PowerShell 4104/4103 | nhạy cảm, xem cảnh báo bên dưới |
| Ngữ cảnh Wazuh (chỉ B0) | wazuh_rule_id, wazuh_rule_level, wazuh_rule_mitre | rule.* | KHÔNG làm feature |
| Nhãn (điền ở Bước 4) | run_id, label_malicious, label_ttps, label_source | manifest | rỗng ở v0 |

## Thực tế dữ liệu (đo trên mẫu 2026-10-12)
- **processGuid có ở**: Sysmon 1 (100%), Sysmon 3 (100%), Sysmon 22 (100%), Sysmon 5.
- **KHÔNG có processGuid ở**: Security 4688, 4624/4634/4672/4648; PowerShell 4103/4104.
  → 4688 nối vào cây qua `(host, process_id, thời gian)`; PowerShell nối qua
  `(host, system.processID, thời gian)`. Chi tiết trong labeling.md.
- **command_line có ở**: Sysmon 1 và Security 4688 (đã bật "include command line").
- **4688 và Sysmon 1 trùng lặp** về process-create. Quy ước: **Sysmon 1 là bản ghi
  chính** (có GUID + parent GUID + hash); 4688 là bản ghi phụ, dùng để đối chiếu.

## Cảnh báo rò rỉ (script_block_text)
PowerShell 4104 ghi lại **toàn bộ nội dung script**. Nếu bộ điều phối phiên
(Bước 2) viết bằng PowerShell, tên TTP trong comment sẽ lọt vào đây và làm
mô hình "ăn gian". Bắt buộc ở Bước 2–4:
1. Loại mọi event sinh ra bởi chính tiến trình điều phối (lọc theo process_guid gốc).
2. Không dùng `script_block_text` thô làm feature; chỉ trích đặc trưng trung tính
   (độ dài, có gọi cmdlet discovery hay không) — quyết định ở Bước 6.
