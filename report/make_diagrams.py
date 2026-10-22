#!/usr/bin/env python3
"""VT-Guard Buoc 10 - so do minh hoa cho bao cao (HTML/CSS -> PNG bang Playwright + Chrome). Chay: python report/make_diagrams.py"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "report", "figures"); os.makedirs(OUT, exist_ok=True)

CSS = """
*{box-sizing:border-box} body{margin:0;background:#fff;font-family:'Times New Roman',serif;color:#1c2833}
.fig{display:inline-block;padding:18px 20px;background:#fff}
.row{display:flex;align-items:stretch;gap:14px}
.col{display:flex;flex-direction:column;gap:10px}
.box{border:1.5px solid #5d6d7e;border-radius:8px;padding:9px 12px;background:#fbfcfc;font-size:17px;line-height:1.3}
.box b{font-size:18px}
.box .s{font-size:14.5px;color:#4d5656}
.t{border-top:5px solid #2e86c1}.g{border-top:5px solid #1e8449}.r{border-top:5px solid #c0392b}.v{border-top:5px solid #8e44ad}
.o{border-top:5px solid #e67e22}.k{border-top:5px solid #7f8c8d}.y{border-top:5px solid #d4ac0d}
.fill-t{background:#eaf2f8}.fill-g{background:#e9f7ef}.fill-r{background:#fdedec}.fill-v{background:#f4ecf7}.fill-o{background:#fdf2e9}.fill-k{background:#f2f3f4}
.arrow{align-self:center;font-size:28px;color:#566573;padding:0 2px}
.varrow{text-align:center;font-size:24px;color:#566573;line-height:1}
.zone{border:2px dashed #85929e;border-radius:12px;padding:12px 14px;position:relative}
.zone .lbl{font-size:15px;font-weight:bold;color:#34495e;margin-bottom:8px}
.chip{display:inline-block;border:1px solid #aab7b8;border-radius:12px;padding:1px 8px;margin:2px 3px 0 0;font-size:14px;background:#fff}
.chip.on{border-color:#c0392b;color:#922b21;font-weight:bold;background:#fdedec}
.dim{opacity:.45}
.title{font-weight:bold;font-size:18px;text-align:center;margin-bottom:10px}
.mono{font-family:Consolas,monospace;font-size:14px}
"""

def page(body): return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='fig'>{body}</div></body></html>"

A = "<div class='arrow'>&#10132;</div>"
V = "<div class='varrow'>&#9660;</div>"

D = {}

D["d_killchain"] = """
<div class='row'>
 <div class='box k fill-k dim' style='width:190px'><b>Truy cập ban đầu</b><div class='s'>khai thác thiết bị biên (Fortinet, Ivanti…), mạng router SOHO (KV-botnet)</div></div>""" + A + """
 <div class='box t fill-t' style='width:470px'><b>Trinh sát nội bộ (Discovery – TA0007)</b>
  <div class='s'>chỉ dùng công cụ sẵn có của Windows (LOTL)</div>
  <div><span class='chip on'>T1016 ipconfig / netsh / arp</span><span class='chip on'>T1018 nltest / ping / net view</span>
  <span class='chip on'>T1087.002 net user|group /domain</span><span class='chip on'>T1654 wevtutil / Get-EventLog</span></div></div>""" + A + """
 <div class='box r fill-r' style='width:230px'><b>Đánh cắp thông tin xác thực (TA0006)</b><div><span class='chip on'>T1003.003 ntdsutil "ifm" / vssadmin shadow</span></div><div class='s'>lấy NTDS.dit → toàn bộ hash miền</div></div>""" + A + """
 <div class='box k fill-k dim' style='width:190px'><b>Di chuyển ngang, duy trì, tiền định vị</b><div class='s'>RDP/WMI với tài khoản hợp lệ, proxy portproxy</div></div>
</div>
<div style='margin-top:10px;font-size:15px;color:#566573'>Ô đậm viền đỏ: 5 kỹ thuật VT-Guard mô phỏng và phát hiện. Ô mờ: ngoài phạm vi đề tài.</div>"""

D["d_lab"] = """
<div class='zone' style='width:1180px'><div class='lbl'>Máy chủ vật lý (laptop) · VMware Workstation 17 · mạng ảo cách ly VMnet2 (10.20.30.0/24, không Internet) · miền CORP.VTLAB.TEST</div>
<div class='row' style='gap:22px'>
 <div class='col' style='width:360px'>
  <div class='box g fill-g'><b>DC01</b> · Windows Server, Domain Controller<div class='s'>AD DS, DNS · tài khoản user01 / admin01<br>Wazuh agent 001 · Sysmon · Audit 4688 (dòng lệnh) · PowerShell 4103/4104 · SACL thư mục NTDS<br>Atomic Red Team · snapshot BASELINE-CLEAN (cho T1003.003)</div></div>
  <div class='box g fill-g'><b>WIN10-01</b> · Windows 10, máy trạm trong miền<div class='s'>Wazuh agent 002 · Sysmon · Audit 4688 · PowerShell logging<br>Atomic Red Team + bộ điều phối phiên Invoke-VTSession.ps1</div></div>
 </div>
 <div class='col' style='justify-content:center'><div class='arrow'>&#10132;</div><div style='font-size:14px;text-align:center'>1514/tcp<br>log sự kiện</div></div>
 <div class='box t fill-t' style='width:380px'><b>VT-SIEM01</b> · Ubuntu Server · 10.20.30.10<div class='s'>Docker: wazuh-docker 4.14.8 (single-node)</div>
  <div class='box' style='margin-top:6px'><b>Wazuh Manager</b><div class='s'>giải mã, luật có sẵn, archives (logall_json)</div></div>
  <div class='box' style='margin-top:6px'><b>Wazuh Indexer</b> :9200<div class='s'>chỉ mục wazuh-archives-* (mọi event) · wazuh-alerts-*</div></div>
  <div class='box' style='margin-top:6px'><b>Wazuh Dashboard</b> :443</div></div>
 <div class='col' style='justify-content:center'><div class='arrow'>&#10132;</div><div style='font-size:14px;text-align:center'>REST :9200<br>chỉ đọc</div></div>
 <div class='box v fill-v' style='width:230px'><b>VT-Guard</b><div class='s'>Python / Docker trên máy chủ vật lý: tiền xử lý, VT-Seq-ens (ONNX), luật Sigma, hợp nhất F3-B, dashboard SOC :8501</div></div>
</div></div>"""

D["d_arch"] = """
<div class='col' style='width:1180px'>
 <div class='row'>
  <div class='box k fill-k' style='flex:1'><b>① Thu thập</b><div class='s'>Wazuh agent (DC01, WIN10-01): Sysmon, Security, PowerShell, Application, System → Wazuh Manager → Indexer (wazuh-archives-*)</div></div>""" + A + """
  <div class='box o fill-o' style='flex:1.2'><b>② Dữ liệu</b><div class='s'>chuẩn hoá (normalize v1) → gán nhãn theo cây tiến trình + manifest (labeler v8) → cửa sổ phiên 64 event → đặc trưng 268 chiều → chia tập theo nhóm phiên (dataset-v1.2)</div></div>
 </div>
 <div class='varrow'>&#9660;</div>
 <div class='row'>
  <div class='box t fill-t' style='flex:1'><b>③a Mô hình chuỗi VT-Seq (AI)</b><div class='s'>GRU + attention, đa nhiệm (nhị phân + 5 TTP), ensemble 5 seed, xuất ONNX → p, p<sub>k</sub>, α (attention)</div></div>
  <div class='box v fill-v' style='flex:1'><b>③b Bộ sinh luật tự động</b><div class='s'>RIPPER chỉ trên Train + vị từ cấm + cổng G0–G4 → 11 luật Sigma có xuất xứ → r, r<sub>k</sub></div></div>
 </div>
 <div class='varrow'>&#9660;</div>
 <div class='row'>
  <div class='box g fill-g' style='flex:1'><b>④ Hợp nhất F3-B</b><div class='s'>s = p + 0,1·r ; s<sub>k</sub> = p<sub>k</sub> + 0,1·r<sub>k</sub> → cảnh báo + nguồn quyết định (AI + luật / chỉ AI) + TTP</div></div>""" + A + """
  <div class='box r fill-r' style='flex:1.2'><b>⑤ Vận hành</b><div class='s'>pipeline suy luận 2–3 ms/cửa sổ · chế độ trực tiếp đọc Indexer · dashboard SOC (Phần A SIEM, Phần B kết quả) · ghi ngược vtguard-alerts-* · Docker offline</div></div>
 </div>
</div>"""

steps = [("1", "Hạ tầng Wazuh", "DC01, WIN10-01 → Indexer", "k"), ("2", "Bộ điều phối", "ART + manifest phiên", "k"),
         ("3", "Thu thập & gán nhãn", "479 phiên, 10 đợt", "o"), ("4", "Đóng băng dataset", "809 cửa sổ, v1.2", "o"),
         ("5", "Khung đánh giá + B0–B3", "bootstrap, Holm", "y"), ("6", "VT-Seq (YC3)", "GRU-Attention", "t"),
         ("7", "Luật tự sinh (YC1)", "RIPPER → Sigma", "v"), ("8", "Hợp nhất (YC2)", "F3-B", "g"),
         ("9", "Triển khai", "live, dashboard, Docker", "r")]
D["d_process"] = "<div class='row' style='gap:6px'>" + A.join(
    f"<div class='box {c} fill-{c}' style='width:118px;text-align:center'><div style='font-size:24px;font-weight:bold'>{n}</div><b style='font-size:15.5px'>{t}</b><div class='s'>{s}</div></div>"
    for n, t, s, c in steps) + "</div><div style='font-size:15px;color:#566573;margin-top:8px'>Mỗi bước kết thúc bằng tiêu chí chấp nhận và git tag (dataset-v1.2, step5-done … step8-done); cấu hình được khoá bằng commit TRƯỚC khi chấm tập kiểm thử.</div>"

D["d_label"] = """
<div class='row' style='width:1180px;gap:18px'>
 <div class='col' style='width:300px'>
  <div class='box o fill-o'><b>Manifest phiên</b><div class='s mono'>run_id, class, host, user<br>ttps = [T1016, T1654]<br>t_start, t_end<br>exclude_pids = [PID orchestrator]</div></div>
  <div class='box k fill-k'><b>Telemetry Wazuh</b><div class='s'>Sysmon EID 1 (process_guid, parent_guid) dựng cây tiến trình; 4688, 4103/4104, 3, 22 ghép vào tiến trình theo (host, PID, vòng đời EID1→EID5)</div></div>
 </div>
 <div class='arrow'>&#10132;</div>
 <div class='col' style='flex:1'>
  <div class='box r fill-r'><b>powershell.exe — bộ điều phối</b> <span class='chip'>LOẠI: orchestrator</span>
   <div style='margin-left:26px;margin-top:6px' class='col'>
    <div class='box'>cmd.exe /c … (executor ART) <span class='chip on'>độc hại · T1016</span>
      <div style='margin-left:26px;margin-top:4px'><span class='chip on'>ipconfig.exe /all</span><span class='chip on'>netsh interface show</span><span class='chip on'>arp -a</span> → cây con kế thừa nhãn phiên</div></div>
    <div class='box'>hostname.exe, whoami.exe, conhost.exe (khung ART) <span class='chip'>LOẠI: harness</span></div>
    <div class='box'>scp manifest → VT-SIEM01 <span class='chip'>LOẠI: upload</span></div>
   </div></div>
  <div class='box g fill-g'><b>Event nền cùng host trong [t_start, t_end]</b> (svchost, logon 4624, DNS…) <span class='chip'>lành tính</span></div>
 </div>
</div>"""

D["d_dataset"] = """
<div class='row' style='width:1180px'>
 <div class='box o fill-o' style='width:230px'><b>Luồng phiên</b><div class='s'>event cây tiến trình của phiên + event nền cùng host trong khung phiên, sắp theo ts_system</div></div>""" + A + """
 <div class='box o fill-o' style='width:230px'><b>Cửa sổ trượt</b><div class='s'>W = 64 event, bước 32, tối đa 8 cửa sổ/phiên · nhãn: có ≥1 event độc hại; TTP = hợp nhãn event</div></div>""" + A + """
 <div class='box t fill-t' style='width:260px'><b>Đặc trưng 268 chiều / event</b><div class='s'>7 trường phân loại (channel, event_id, image, parent, host_role, integrity, logon_type) · dòng lệnh chuẩn hoá → n-gram ký tự 3–5, băm 256 chiều · 5 số (Δt, mạng, DNS, kênh)</div></div>""" + A + """
 <div class='box g fill-g' style='width:300px'><b>Chia tập theo nhóm phiên</b><div class='s'>Train 483 · T-clean 89 (cùng phân phối) · T-hard 88 (quản trị hợp lệ, 0 dương) · T-novel 149 (đợt mới + biến thể ntds2v) · không phiên/nhóm chồng thời gian nào ở 2 tập</div></div>
</div>"""

D["d_vtseq"] = """
<div class='row' style='width:1180px;gap:10px'>
 <div class='col' style='width:300px'>
  <div class='box o fill-o'><b>Event i (i = 1…n ≤ 64)</b></div>
  <div class='box'>7 embedding: event_id, image, parent (16 chiều); 4 trường khác (8 chiều)</div>
  <div class='box'>dòng lệnh băm 256 → Linear 64</div>
  <div class='box'>5 đặc trưng số (log Δt, mạng, DNS, kênh)</div>
 </div>""" + A + """
 <div class='box t fill-t' style='width:150px;align-self:center'><b>Linear + LayerNorm</b><div class='s'>x<sub>i</sub> ∈ ℝ<sup>96</sup></div></div>""" + A + """
 <div class='box t fill-t' style='width:150px;align-self:center'><b>GRU 1 lớp</b><div class='s'>h<sub>i</sub> ∈ ℝ<sup>96</sup>, chỉ trên event thật (pack)</div></div>""" + A + """
 <div class='box y' style='width:190px;align-self:center'><b>Attention cộng</b><div class='s'>e<sub>i</sub> = v<sup>T</sup>tanh(W h<sub>i</sub>)<br>α = softmax(e)<br>c = Σ α<sub>i</sub> h<sub>i</sub></div></div>""" + A + """
 <div class='col' style='width:200px;justify-content:center'>
  <div class='box r fill-r'><b>Đầu nhị phân</b><div class='s'>p<sub>bin</sub> (sigmoid)</div></div>
  <div class='box v fill-v'><b>Đầu 5 TTP</b><div class='s'>p<sub>k</sub>, đa nhãn (sigmoid)</div></div>
  <div class='box k fill-k'><div class='s'>Loss = BCE<sub>bin</sub> + λ·BCE<sub>TTP</sub>; crop độ dài U[4,n]; ensemble 5 seed</div></div>
 </div>
</div>"""

D["d_rules"] = """
<div class='row' style='width:1180px;gap:8px'>
 <div class='box o fill-o' style='width:170px'><b>Cửa sổ Train</b><div class='s'>483 cửa sổ (chỉ Train, không nhìn test)</div></div>""" + A + """
 <div class='box' style='width:190px'><b>Atom "có mặt"</b><div class='s'>image, parent, event_id, token dòng lệnh, image+token cùng event</div></div>""" + A + """
 <div class='box r fill-r' style='width:190px'><b>Vị từ cấm</b><div class='s'>S1 dấu vết ART · S2 vỏ cmd · S3 PowerShell · S4 event nền · S5 tên miền lab · S4-auto</div></div>""" + A + """
 <div class='box t fill-t' style='width:170px'><b>RIPPER</b><div class='s'>chọn engine bằng macro-F1 TTP OOF (0,756 &gt; cây 0,675)</div></div>""" + A + """
 <div class='box y' style='width:180px'><b>Cổng G0–G4</b><div class='s'>support ≥ 10, precision OOF ≥ 0,9 trên ≥ 10 cửa sổ, khử trùng</div></div>""" + A + """
 <div class='box g fill-g' style='width:190px'><b>11 luật Sigma</b><div class='s'>YAML hợp lệ (pySigma 0 lỗi) + provenance: cửa sổ/phiên Train sinh luật</div></div>
</div>"""

D["d_fusion"] = """
<div class='row' style='width:1180px;gap:10px'>
 <div class='col' style='width:280px'>
  <div class='box t fill-t'><b>VT-Seq-ens</b><div class='s'>p = max(p<sub>bin</sub>, max<sub>k</sub> p<sub>k</sub>) ; p<sub>k</sub></div></div>
  <div class='box v fill-v'><b>11 luật Sigma</b><div class='s'>r = 1 nếu có luật khớp ; r<sub>k</sub> chỉ cho T1018, T1654, T1003.003</div></div>
 </div>""" + A + """
 <div class='box g fill-g' style='width:300px;align-self:center'><b>F3-B (khoá trên OOF, commit 3fd9531)</b><div class='s'>s = p + 0,1·r ≥ τ = 0,869 → cảnh báo<br>s<sub>k</sub> = p<sub>k</sub> + 0,1·r<sub>k</sub> ≥ τ<sub>k</sub> → gán TTP</div></div>""" + A + """
 <div class='col' style='width:420px'>
  <div class='box r fill-r'><b>AI + luật xác nhận → ưu tiên CAO</b><div class='s'>76/76 cảnh báo đúng trên tập kiểm thử</div></div>
  <div class='box o fill-o'><b>Chỉ AI → CẦN XEM LẠI</b><div class='s'>20/25 đúng; kèm top-5 event attention để phân tích viên xem</div></div>
  <div class='box k fill-k'><b>Luật khớp nhưng AI thấp</b><div class='s'>p + 0,1 &lt; τ → không cảnh báo (AI chặn luật khớp nhầm)</div></div>
 </div>
</div>"""

D["d_live"] = """
<div class='row' style='width:1180px;gap:8px'>
 <div class='box k fill-k' style='width:170px'><b>Wazuh Indexer</b><div class='s'>wazuh-archives-*<br>tài khoản riêng chỉ đọc</div></div>""" + A + """
 <div class='box o fill-o' style='width:180px'><b>Connector</b><div class='s'>đọc event mới mỗi 12 s, checkpoint (timestamp + _id), phân trang</div></div>""" + A + """
 <div class='box o fill-o' style='width:200px'><b>Windower</b><div class='s'>tiền xử lý giống hệt dataset; gom theo host, ≤ 64 event, đóng khi host im lặng 30 s</div></div>""" + A + """
 <div class='box t fill-t' style='width:180px'><b>Pipeline suy luận</b><div class='s'>ONNX VT-Seq-ens → Sigma → F3-B (khoá)</div></div>""" + A + """
 <div class='col' style='width:200px'>
  <div class='box g fill-g'><b>Dashboard SOC</b><div class='s'>hàng đợi tự làm mới, độ trễ, MITRE</div></div>
  <div class='box v fill-v'><b>vtguard-alerts-*</b><div class='s'>ghi ngược để xem trong Wazuh Dashboard</div></div>
 </div>
</div>
<div style='font-size:15px;color:#566573;margin-top:8px'>Chế độ phát lại (replay) thay Connector bằng FileSource đọc log đã ghi — cùng toàn bộ phần sau của luồng.</div>"""

D["d_deploy"] = """
<div class='zone' style='width:1180px'><div class='lbl'>VT-SIEM01 · Ubuntu Server · 10.20.30.10 · Docker Engine</div>
<div class='row' style='gap:18px'>
 <div class='zone' style='flex:1.15'><div class='lbl'>wazuh-docker 4.14.8 (giữ nguyên) · mạng single-node_default</div>
  <div class='col'>
   <div class='box k fill-k'><b>wazuh.manager</b><div class='s'>nhận log agent :1514–1515, API :55000, archives (logall_json)</div></div>
   <div class='box t fill-t'><b>wazuh.indexer</b> :9200<div class='s'>wazuh-archives-* (mọi sự kiện) · wazuh-alerts-* · <b>vtguard-alerts-*</b> (mới)</div></div>
   <div class='box k fill-k'><b>wazuh.dashboard</b> :443<div class='s'>Discover: wazuh-alerts-* và vtguard-alerts-*</div></div>
  </div></div>
 <div class='col' style='justify-content:center;width:150px'>
  <div style='font-size:14px;text-align:center'>REST TLS<br><span class='mono' style='font-size:12px'>wazuh.indexer:9200</span><br>(đúng CN chứng chỉ)</div>
  <div class='arrow' style='text-align:center'>&#8644;</div>
  <div style='font-size:14px;text-align:center'>đọc archives<br>ghi vtguard-alerts</div></div>
 <div class='zone' style='flex:1'><div class='lbl'>VT-Guard (deploy/docker-compose.yml)</div>
  <div class='col'>
   <div class='box o fill-o'><b>vtguard-live</b> · lệnh <span class='mono'>stream</span><div class='s'>đọc mỗi 12 s → tiền xử lý → ONNX + Sigma + F3-B → cảnh báo; healthcheck, tự khởi động lại, RAM ≤ 1 GB</div></div>
   <div class='box v fill-v'><b>volume vtguard_live</b><div class='s'>checkpoint · status.json · alerts.jsonl (giữ qua khởi động lại)</div></div>
   <div class='box g fill-g'><b>vtguard-dashboard</b> · <b>10.20.30.10:8501</b><div class='s'>Phần A SIEM thời gian thực · Phần B kết quả nghiên cứu</div></div>
  </div></div>
</div>
<div style='margin-top:10px;font-size:15px;color:#566573'>Bí mật (mật khẩu Indexer, CA) mount từ <span class='mono'>deploy/secrets/</span>, không nằm trong image; tài khoản riêng <span class='mono'>vtguard</span> chỉ đọc archives/alerts, chỉ ghi vtguard-alerts-*.</div>
</div>"""

dsteps = [("1", "Đóng gói", "build image, verify 7/7, xuất tar + sha256", "o"), ("2", "Chuyển giao", "scp tar + deploy/ sang VT-SIEM01", "o"),
          ("3", "Nạp & kiểm", "docker load, sha256, verify offline", "y"), ("4", "Phân quyền", "tạo role + user vtguard trên Indexer", "r"),
          ("5", "Cấu hình", ".env, secrets, CA, mạng Wazuh", "v"), ("6", "Kiểm kết nối", "<span style='white-space:nowrap'>stream --check</span>", "t"),
          ("7", "Khởi chạy", "docker compose <span style='white-space:nowrap'>up -d</span>; healthy", "g"), ("8", "Tích hợp Wazuh", "index template + pattern vtguard-alerts-*", "g")]
D["d_deploy_steps"] = "<div class='row' style='gap:6px;width:1180px'>" + A.join(
    f"<div class='box {c} fill-{c}' style='width:128px;text-align:center'><div style='font-size:24px;font-weight:bold'>{n}</div><b style='font-size:15.5px'>{t}</b><div class='s'>{s}</div></div>"
    for n, t, s, c in dsteps) + "</div>"

D["d_demo_flow"] = """
<div class='row' style='width:1180px;gap:8px'>
 <div class='box k fill-k' style='width:150px'><b>Chuẩn bị</b><div class='s'>khôi phục snapshot, đồng bộ giờ, hai màn hình Wazuh ↔ VT-Guard</div></div>""" + A + """
 <div class='box o fill-o' style='width:170px'><b>Chạy phiên</b><div class='s'>Invoke-VTSession.ps1 → Atomic Red Team theo mã test; ghi manifest (t_start, t_end, TTP)</div></div>""" + A + """
 <div class='col' style='width:230px'>
  <div class='box t fill-t'><b>Wazuh</b><div class='s'>wazuh-alerts-*: luật nào bắn, mức, mã ATT&CK gán</div></div>
  <div class='box g fill-g'><b>VT-Guard</b><div class='s'>hàng đợi, Chi tiết cảnh báo, dòng thời gian</div></div>
 </div>""" + A + """
 <div class='box y' style='width:180px'><b>Đối chiếu tự động</b><div class='s'>demo_report.py: theo khung thời gian + máy của từng manifest</div></div>""" + A + """
 <div class='box r fill-r' style='width:190px'><b>Đánh giá</b><div class='s'>tấn công: gán đúng TTP? · quản trị: im lặng? · độ trễ</div></div>
</div>"""

def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 1300, "height": 900}, device_scale_factor=2)
        for name, body in D.items():
            pg.set_content(page(body)); pg.wait_for_timeout(150)
            pg.locator(".fig").screenshot(path=os.path.join(OUT, f"{name}.png")); print("ghi", name)
        b.close()

if __name__ == "__main__":
    main()
