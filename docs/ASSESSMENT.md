# VT-Guard — Đánh giá khách quan đề tài (thang điểm 10)

Người đánh giá: trợ lý AI đồng hành dự án, đánh giá dựa trên bằng chứng trong repo (báo cáo từng bước, results JSON, kiểm thử,
lần chạy thật trên hạ tầng ngày 22/10). Thời điểm: 24/10/2026 — **Bước 9 mốc 4 mới chạy 1/6 kịch bản; báo cáo Word còn khung ảnh trống.**
Mục đích: giúp nhóm biết đề tài đang ở đâu so với một hội đồng khó tính, không phải để động viên.

## 1. Điểm tổng

| Tiêu chí | Trọng số | Điểm | Đóng góp |
|---|---|---|---|
| 1. Tính cấp thiết, mục tiêu, lý do chọn đối tượng | 10% | 9,5 | 0,95 |
| 2. Hạ tầng và dữ liệu | 20% | 8,5 | 1,70 |
| 3. Mô hình chuỗi tuỳ biến (YC3) | 15% | 8,0 | 1,20 |
| 4. Luật tự sinh có xuất xứ (YC1) | 10% | 8,0 | 0,80 |
| 5. Hợp nhất AI + luật (YC2) | 10% | 7,5 | 0,75 |
| 6. Phương pháp đánh giá khoa học | 15% | 9,5 | 1,43 |
| 7. Sản phẩm và triển khai thực tế | 10% | 9,0 | 0,90 |
| 8. Báo cáo và trình bày | 10% | 7,5 | 0,75 |
| **Tổng** | 100% | | **8,5 / 10** |

**Dự báo:** hoàn tất KB1–KB6 trên hạ tầng thật, dán ảnh và điền số liệu vào báo cáo → **khoảng 9,0**. Thêm một kiểm thử ngoài
(dataset công khai hoặc biến thể chưa thấy) và đo báo nhầm 24 giờ (Bước 11, nhóm A) → **9,3–9,5**. Khó lên 10 vì giới hạn quy mô dữ liệu
(mục 3) không khắc phục được trong thời gian còn lại.

## 2. Điểm mạnh (có bằng chứng)

1. **Chất lượng dữ liệu vượt mức thường thấy ở đề tài môn học.** Nhãn suy ra từ manifest + cây tiến trình Sysmon chứ không từ regex;
   bộ gán nhãn qua 5 phiên bản, mỗi lần nâng cấp đều đối chiếu từng sự kiện (v7↔v8: chỉ 2 394 event 4688 đổi, 0 event khác).
   Phát hiện và trung hoà **dấu vết bộ sinh dữ liệu** (conhost, đường dẫn cmd, `>nul`, bất đối xứng 4688/EID1) bằng định lượng —
   lỗi mà nhiều công trình đã công bố còn mắc.
2. **Quy trình đánh giá trung thực, kiểm chứng được.** Cấu hình khoá bằng commit trước khi chấm test (3ebc94b, 3fd9531); ba tập kiểm thử
   có vai trò khác nhau; bootstrap 95% + Holm; báo cả kết quả *không có ý nghĩa* (VT-Seq không hơn B1/B2; F3-B không hơn chỉ-AI).
3. **Đáp ứng đủ ba yêu cầu đề tài với bằng chứng định lượng.** YC1: 11 luật Sigma hợp lệ, có xuất xứ, 0/88 báo nhầm.
   YC2: F3-B hơn chỉ-luật sau Holm, phân mức tin cậy (76/76). YC3: chuỗi ablation chỉ ra attention là đóng góp chính, attention được
   kiểm chứng faithfulness.
4. **Tương phản với Wazuh là thật, không dàn dựng.** Lấy từ baseline B0 chạy trên chính dữ liệu: luật có sẵn gán T1059.003 cho mọi hành vi
   LOTL, F1 = 0 ở 4/5 kỹ thuật.
5. **Sản phẩm chạy được trên hạ tầng thật**, không dừng ở notebook: luồng trực tiếp đọc Wazuh Indexer, tự phục hồi, healthcheck, ghi cảnh báo
   ngược vào Wazuh Dashboard; image Docker offline với `verify` 7/7 cho phép giảng viên tái lập mọi con số bằng một lệnh.

## 3. Điểm yếu (xếp theo mức ảnh hưởng tới độ tin của kết luận)

| # | Điểm yếu | Vì sao quan trọng | Có khắc phục được trước 01/11? |
|---|---|---|---|
| W1 | **Quy mô và tính thực tế của dữ liệu:** 2 máy, 1 miền, 13,9 giờ log; hoạt động lành tính do script sinh, không có người dùng thật; tấn công do một công cụ (ART) sinh | Kết quả có thể không chuyển sang mạng thật; tỉ lệ báo nhầm thực tế chưa biết | Một phần: đo báo nhầm 24 giờ (11-A2) |
| W2 | **Chưa có kiểm thử ngoài** (dataset công khai) dù pipeline ban đầu có dự kiến | T-novel vẫn cùng lab, cùng bộ sinh; chưa chứng minh tổng quát hoá thật | Có thể làm bản nhỏ (11-A3) |
| W3 | **VT-Seq không hơn baseline đơn giản (B1 TF-IDF, B2 LightGBM)** sau Holm; chỉ hơn GRU thuần | Câu hỏi “sao không dùng mô hình đơn giản?” chắc chắn được hỏi; ưu thế chỉ ở T1654, độ bền khi bỏ tên công cụ và giải thích | Không đổi được kết quả; cần chuẩn bị câu trả lời |
| W4 | **Hợp nhất không cải thiện chỉ số** so với chỉ-AI; giá trị nằm ở giải thích và phân mức tin cậy (mô tả, mẫu nhỏ) | Dễ bị cho là YC2 “làm cho có” | Trình bày đúng giá trị: phân mức tin cậy + xuất xứ |
| W5 | **Luật tự sinh dùng token phổ biến** (`create`, `system`); chỉ 3/5 kỹ thuật có luật riêng; bắt biến thể shadow copy phần nào do trùng token | Rủi ro báo nhầm ngoài lab | Có (11-B1: cổng độ đặc hiệu token) |
| W6 | **Mẫu T1003.003 nhỏ** (6 phiên T-novel, 12 cửa sổ T-clean) | Chỉ số kỹ thuật này dao động lớn | Không; đã báo kèm khoảng tin cậy |
| W7 | **Kiểm soát độ dài cửa sổ chưa vững** ở từng seed (crop) | Mô hình có thể dựa một phần vào độ dài | Không cần trước hạn; đã ghi hạn chế |
| W8 | **Thực nghiệm trực tiếp chưa xong** (1/6 kịch bản), chưa có số liệu đối chiếu Wazuh ↔ VT-Guard trên hạ tầng | Phần “demo lấy điểm” còn thiếu bằng chứng | **Có — ưu tiên số 1** |
| W9 | **Báo cáo Word còn 25 khung ảnh trống, ô tô vàng, bìa chưa điền** | Trừ điểm trình bày trực tiếp | **Có — ưu tiên số 2** |
| W10 | Chưa đánh giá **né tránh** (dòng lệnh làm rối, đổi tên tệp, dùng PowerShell / WMI thay cmd) | APT thật sẽ biến đổi lệnh | Bản nhỏ (11-A4) |

## 4. Câu hỏi hội đồng dễ hỏi và hướng trả lời

| Câu hỏi | Hướng trả lời (trung thực) |
|---|---|
| Vì sao không dùng TF-IDF / LightGBM vì chúng ngang VT-Seq? | Đúng là ngang ở nhị phân; VT-Seq hơn rõ ở kỹ thuật khó T1654 (0,68 vs 0,57–0,59), **không sụp khi bỏ tên công cụ** (0,83 vs B2 0,45), và cho attention để giải thích; mô hình đơn giản là lựa chọn hợp lý khi chỉ cần nhị phân. |
| Dữ liệu mô phỏng có thực tế không? | Hạn chế đã nêu; đã chống rò rỉ bằng hard-negative cùng công cụ, trung hoà dấu vết bộ sinh, holdout thời gian + biến thể; (nếu làm 11-A) có thêm đo báo nhầm 24 giờ / kiểm thử ngoài. |
| Fusion có ích gì khi không tăng điểm? | Phân mức tin cậy: nhóm có luật xác nhận đúng 76/76, mọi báo nhầm nằm ở nhóm chỉ-AI; 75% cảnh báo có luật Sigma kèm xuất xứ để phân tích viên kiểm tra; AI chặn được luật khớp nhầm (auditpol). |
| Wazuh viết thêm luật là bắt được? | Đúng — và đó chính là việc VT-Guard tự động hoá: sinh luật Sigma từ dữ liệu, có kiểm định, thay vì viết tay từng luật. |

## 5. Kết luận

Đề tài đạt mức **khá giỏi đến giỏi (8,5/10)** ở thời điểm hiện tại, với điểm mạnh nổi bật là **độ chặt chẽ của dữ liệu và đánh giá** cùng một
**sản phẩm chạy thật trên hạ tầng Wazuh**. Hai việc quyết định điểm cuối cùng trong một tuần còn lại không phải là cải tiến mô hình mà là
**hoàn tất thực nghiệm trực tiếp** và **hoàn thiện báo cáo**. Cải tiến mô hình (Bước 11) chỉ nên làm sau hai việc đó.
