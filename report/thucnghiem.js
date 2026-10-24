// VT-Guard - ban Word HUONG DAN THUC NGHIEM cac kich ban de hoan thien bao cao.
// Chay: node report/thucnghiem.js -> report/HuongDan_ThucNghiem.docx  (docx chi giu cuc bo, khong commit)
// Moi KB: muc tieu -> lenh -> thao tac -> ANH CAN CHUP (kem so Hinh trong bao cao) -> ky vong -> cach dien so lieu.
const fs = require("fs");
const path = require("path");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, ShadingType,
        BorderStyle, LevelFormat, VerticalAlign, Footer, PageNumber, HeadingLevel, PageBreak } = D;

const FONT = "Times New Roman";
const SZ = 26, SZ_TBL = 22, CM = 567, TEXT_W = 17 * CM;
const NAVY = "1F3864", BLUE = "2E75B6", GREEN = "E2EFDA", HEAD = "DDEBF7", RED = "C00000";

function runs(text, base = {}) {
  const out = []; const re = /(\[\[[^\]]+\]\]|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g; let last = 0, m;
  const T = (t, o = {}) => new TextRun({ text: t, font: FONT, size: SZ, ...base, ...o });
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(T(text.slice(last, m.index)));
    const t = m[0];
    if (t.startsWith("[[")) out.push(T(t.slice(2, -2), { highlight: "yellow" }));
    else if (t.startsWith("**")) out.push(T(t.slice(2, -2), { bold: true }));
    else if (t.startsWith("`")) out.push(T(t.slice(1, -1), { font: "Consolas", size: (base.size || SZ) - 2 }));
    else out.push(T(t.slice(1, -1), { italics: true }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(T(text.slice(last)));
  return out;
}

const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, spacing: { before: 0, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 4 } },
  children: [new TextRun({ text, bold: true, color: NAVY, font: FONT, size: 30 })] });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 90 }, keepNext: true,
  children: [new TextRun({ text, bold: true, color: NAVY, font: FONT, size: 28 })] });
// Thanh tieu de KB
const KB = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 260, after: 100 },
  shading: { fill: NAVY, type: ShadingType.CLEAR, color: "auto" }, indent: { left: 60, right: 60 },
  children: [new TextRun({ text, bold: true, color: "FFFFFF", font: FONT, size: 27 })] });
const Lab = (text) => new Paragraph({ keepNext: true, spacing: { before: 90, after: 30 },
  children: [new TextRun({ text: "▸ " + text, bold: true, color: BLUE, font: FONT, size: SZ })] });
const P = (text) => new Paragraph({ children: runs(text), alignment: AlignmentType.JUSTIFIED, spacing: { after: 50, line: 300 } });
const Bul = (text, lv = 0) => new Paragraph({ children: runs(text), numbering: { reference: "dot", level: lv },
  spacing: { after: 30, line: 288 }, alignment: AlignmentType.JUSTIFIED });
const Step = (nx, text) => new Paragraph({ spacing: { after: 40, line: 288 }, indent: { left: 360, hanging: 360 },
  children: [new TextRun({ text: nx + "  ", bold: true, color: BLUE, font: FONT, size: SZ }), ...runs(text)] });
// Khung anh can chup: vien xanh + so Hinh trong bao cao
function Shot(fig, what) {
  const w = TEXT_W;
  return new Table({ width: { size: w, type: WidthType.DXA }, columnWidths: [w], alignment: AlignmentType.CENTER,
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({ width: { size: w, type: WidthType.DXA },
      borders: { top: { style: BorderStyle.SINGLE, size: 6, color: "A6A6A6" }, bottom: { style: BorderStyle.SINGLE, size: 6, color: "A6A6A6" },
                 left: { style: BorderStyle.SINGLE, size: 24, color: "70AD47" }, right: { style: BorderStyle.SINGLE, size: 6, color: "A6A6A6" } },
      shading: { fill: "F2F7EC", type: ShadingType.CLEAR, color: "auto" }, margins: { left: 140, right: 140, top: 70, bottom: 70 },
      children: [new Paragraph({ spacing: { line: 276 }, children: [
        new TextRun({ text: "📷 ẢNH CẦN CHỤP", bold: true, color: "548235", font: FONT, size: 22 }),
        ...(fig ? [new TextRun({ text: `  → dán vào ${fig} của báo cáo`, bold: true, italics: true, color: RED, font: FONT, size: 22 })] : []),
      ] }),
      new Paragraph({ spacing: { line: 276 }, children: runs(what, { size: 23 }) })] })] })] });
}
const Cmd = (lines) => new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [TEXT_W], alignment: AlignmentType.CENTER,
  rows: [new TableRow({ children: [new TableCell({ width: { size: TEXT_W, type: WidthType.DXA },
    shading: { fill: "1E1E1E", type: ShadingType.CLEAR, color: "auto" }, margins: { left: 140, right: 140, top: 70, bottom: 70 },
    borders: { top: { style: BorderStyle.SINGLE, size: 4, color: "1E1E1E" }, bottom: { style: BorderStyle.SINGLE, size: 4, color: "1E1E1E" }, left: { style: BorderStyle.SINGLE, size: 4, color: "1E1E1E" }, right: { style: BorderStyle.SINGLE, size: 4, color: "1E1E1E" } },
    children: lines.map(l => new Paragraph({ spacing: { after: 0, line: 264 },
      children: [new TextRun({ text: l || " ", font: "Consolas", size: 20, color: l && l.startsWith("#") ? "9CDCFE" : "D4D4D4" })] })) })] })] });

const bd = { style: BorderStyle.SINGLE, size: 4, color: "8EA9DB" };
function Tb(cap, header, rows, ratio, hl = []) {
  const total = ratio.reduce((a, b) => a + b, 0);
  const cw = ratio.map(r => Math.floor(TEXT_W * r / total)); cw[cw.length - 1] += TEXT_W - cw.reduce((a, b) => a + b, 0);
  const row = (cells, head, h) => new TableRow({ tableHeader: head, cantSplit: true, children: cells.map((c, i) => new TableCell({
    borders: { top: bd, bottom: bd, left: bd, right: bd }, width: { size: cw[i], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: head ? { fill: HEAD, type: ShadingType.CLEAR, color: "auto" } : (h ? { fill: GREEN, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 30, bottom: 30, left: 70, right: 70 },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, spacing: { line: 252 },
      children: runs(String(c), { size: SZ_TBL, ...(head ? { bold: true } : {}) }) })] })) });
  return [...(cap ? [new Paragraph({ keepNext: true, spacing: { before: 120, after: 50 }, children: [new TextRun({ text: cap, bold: true, italics: true, font: FONT, size: 23 })] })] : []),
          new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: cw, rows: [row(header, true, false), ...rows.map((r, i) => row(r, false, hl.includes(i)))] }),
          new Paragraph({ spacing: { after: 80 }, children: [] })];
}

// --------------------------------------------------------------- noi dung
const body = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "HƯỚNG DẪN THỰC NGHIỆM CÁC KỊCH BẢN", bold: true, color: NAVY, font: FONT, size: 34 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: "ĐỂ HOÀN THIỆN BÁO CÁO VT-GUARD (BƯỚC 9 – MỐC 4)", bold: true, font: FONT, size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
    children: [new TextRun({ text: "Chạy 7 kịch bản trên hạ tầng thật · chụp ảnh điền Hình 3.18–3.45 · điền số liệu Bảng 3.19", italics: true, font: FONT, size: 24 })] }),
  P("Tài liệu này hướng dẫn **thao tác thực tế trong lab** để lấy đủ bằng chứng còn thiếu của báo cáo: các khung ảnh trống (Hình 3.18–3.45) và các ô tô vàng (Bảng 3.19). Làm theo đúng thứ tự; mỗi kịch bản ghi rõ **ảnh nào chụp xong dán vào hình nào**. Tài liệu tham chiếu: `docs/STEP9-M4-DEPLOY.md` (triển khai) và `docs/STEP9-M4-DEMO.md` (kịch bản demo)."),
  P("So với bản demo gốc, tài liệu này **bổ sung Kịch bản 7 – tấn công thủ công không qua bộ điều phối** (mục 5) để chứng minh khả năng phát hiện không phụ thuộc khung mô phỏng."),

  H1("1. Chuẩn bị chung (làm một lần trước tất cả kịch bản)"),
  Lab("Điều kiện tiên quyết"),
  Bul("VT-Guard đã triển khai xong lên VT-SIEM01 theo `docs/STEP9-M4-DEPLOY.md` (8 bước). Nếu chưa, hoàn thành phần triển khai trước — phần đó cho các Hình 3.18–3.22."),
  Bul("Hai máy DC01, WIN10-01 đã bật, Wazuh agent *Active*, đồng hồ đồng bộ (`w32tm /resync /force` trên DC01, nhất là sau khi khôi phục snapshot)."),
  Bul("Có quyền Administrator trên máy sẽ chạy; `orchestrator/Invoke-VTSession.ps1` nằm tại `C:\\VT-Guard\\orchestrator` (WIN10-01 cho trinh sát, DC01 cho NTDS)."),
  Lab("Khởi động và làm sạch VT-Guard (trên VT-SIEM01)"),
  Cmd(["cd ~/vtguard/deploy",
       "docker compose ps                 # vtguard-live & vtguard-dashboard = healthy",
       "# kiem tra ket noi Indexer / tai khoan / co event moi moi agent:",
       "docker compose exec vtguard-live python src/live/run.py live --env-file /secrets/vtguard.env --check",
       "# lam sach canh bao cu de buoi thuc nghiem bat dau tu trang thai sach:",
       "docker compose exec vtguard-live sh -c 'rm -f /app/reports/step9/live/connector_state.json; : > /app/reports/step9/live/alerts.jsonl'",
       "docker compose restart vtguard-live"]),
  Bul("Mở **hai màn hình song song**: trái = Wazuh Dashboard `https://10.20.30.10` (Discover trên `wazuh-alerts-*`); phải = VT-Guard `http://10.20.30.10:8501` (trang **Trực tiếp · Hàng đợi**)."),
  Bul("Tạo thư mục manifest trên máy chạy: mỗi phiên của bộ điều phối ghi một `*.manifest.json` vào `C:\\VT-Guard-runs` (dùng cho `demo_report.py` ở mục 6). Kịch bản 7 gõ tay **không** có manifest."),
  Lab("Quy ước chụp ảnh"),
  Bul("Chụp **toàn cửa sổ** (thấy được đồng hồ / khung giờ) để đối chiếu thời gian hai bên; định dạng PNG."),
  Bul("Đặt tên theo hình: ví dụ `hinh_3_27_kb2_buoc1.png`. Mỗi khung ảnh trong tài liệu ghi sẵn **số hình** cần dán."),
  Bul("Với mỗi cảnh báo VT-Guard quan trọng, chụp cả trang **Chi tiết** (điểm AI, luật Sigma + xuất xứ, nguồn quyết định, top-5 attention)."),
  ...Tb("Bảng A. Ảnh mỗi kịch bản bổ sung cho báo cáo",
    ["Kịch bản", "Hình cần chụp", "Ô số liệu cần điền"],
    [["Triển khai (mục 1)", "3.18 – 3.22", "—"],
     ["KB1 – quản trị hợp lệ", "3.24, 3.25, 3.26", "Bảng 3.19 dòng 1"],
     ["KB2 – trinh sát LOTL", "3.27 – 3.32", "Bảng 3.19 dòng 2"],
     ["KB3 – trinh sát chậm", "3.33, 3.34", "Bảng 3.19 dòng 3"],
     ["KB4 – trích xuất NTDS", "3.35, 3.36, 3.37", "Bảng 3.19 dòng 4"],
     ["KB5 – biến thể NTDS", "3.38, 3.39", "Bảng 3.19 dòng 5"],
     ["KB6 – dòng thời gian", "3.40, 3.41", "—"],
     ["**KB7 – gõ tay (mới)**", "**3.42, 3.43, 3.44**", "**Bảng 3.19 dòng 7**"],
     ["Bảng demo_report", "3.45", "—"]],
    [2.4, 2.1, 2.4]),

  H1("2. Nguyên tắc trình bày trung thực (đọc trước khi chạy)"),
  Bul("Thực nghiệm trực tiếp là **minh hoạ vận hành**, không phải đánh giá: cửa sổ trực tiếp chia theo thời gian, khác cửa sổ theo phiên của tập kiểm thử nên điểm có thể lệch. **Số liệu chính thức vẫn là kết quả trên tập test đã đóng băng** (mục 3.6–3.10 của báo cáo)."),
  Bul("Tương phản với Wazuh lấy từ **baseline B0 thật**: nói “luật Wazuh **có sẵn** không gán được các kỹ thuật này”, không nói “Wazuh không bao giờ bắt được”."),
  Bul("Nếu một kịch bản cho kết quả khác kỳ vọng (ví dụ VT-Guard bỏ sót, hoặc báo nhầm), **ghi trung thực** vào ô tương ứng và nêu lý do — không ép số liệu."),

  H1("3. Kịch bản 1–3 · Trinh sát (trên WIN10-01 / DC01)"),

  KB("KỊCH BẢN 1 — Hoạt động quản trị hợp lệ (phản chứng) → độ tin cậy"),
  Lab("Mục tiêu"), P("Quản trị viên dùng **đúng công cụ** của 5 kỹ thuật nhưng là thao tác hợp lệ; kỳ vọng VT-Guard **im lặng** (minh hoạ FPR thấp — T-hard 1/88 ở Phần B)."),
  Lab("Lệnh (PowerShell Administrator)"),
  Cmd([".\\Invoke-VTSession.ps1 -Class hard_negative -HostName WIN10-01 -User \"VTLAB\\admin01\" -UserRole admin `",
       "  -BenignTasks admin_net_sweep,user_inventory -Tempo burst",
       ".\\Invoke-VTSession.ps1 -Class hard_negative -HostName DC01 -User \"VTLAB\\admin01\" -UserRole admin `",
       "  -BenignTasks dc_db_maint -Tempo burst      # ntdsutil, vssadmin HOP LE (co khoi phuc snapshot)"]),
  Lab("Ảnh cần chụp"),
  Shot("Hình 3.24", "Cửa sổ PowerShell chạy phiên quản trị hợp lệ trên WIN10-01 và DC01 (thấy lệnh và thời gian)."),
  Shot("Hình 3.25", "Wazuh Discover trong khung giờ phiên quản trị — các luật đã bắn (nếu có, thường là luật chung mức 4)."),
  Shot("Hình 3.26", "Hàng đợi VT-Guard **không phát sinh cảnh báo** trong khung giờ đó (hàng đợi đứng yên)."),
  Lab("Kỳ vọng & điền số liệu"),
  Bul("VT-Guard: **không cảnh báo** → điền Bảng 3.19 dòng 1 cột VT-Guard = `0 (im lặng)`. Wazuh: có thể vài luật mức 4 (không phân biệt được admin)."),
  Bul("Nếu VT-Guard có báo: ghi số và kiểm tra trang Chi tiết để giải thích (thường là cửa sổ có công cụ nhạy như `ntdsutil`)."),

  KB("KỊCH BẢN 2 — Trinh sát LOTL mà Wazuh gán sai → YC1 + YC3"),
  Lab("Mục tiêu"), P("Chuỗi trinh sát bằng lệnh hệ thống hợp lệ; Wazuh gán nhầm (T1059.003), VT-Guard gán đúng 4 kỹ thuật kèm luật Sigma và attention. **Đây là kịch bản lấy điểm chính.**"),
  Lab("Lệnh (trên WIN10-01)"),
  Cmd([".\\Invoke-VTSession.ps1 -Class attack -HostName WIN10-01 -User \"VTLAB\\user01\" -UserRole standard `",
       "  -Ttps T1016,T1018,T1087.002,T1654 -TestNumbers 1,3,1,2 -Tempo burst -Variant mixed"]),
  Lab("Ảnh cần chụp (6 hình)"),
  Shot("Hình 3.27", "Cửa sổ bộ điều phối chạy phiên trinh sát LOTL trên WIN10-01."),
  Shot("Hình 3.28", "Wazuh Discover lọc theo mã ATT&CK của 4 kỹ thuật — cho thấy không gán đúng / không có cảnh báo hành vi."),
  Shot("Hình 3.29", "Các luật Wazuh đã bắn: cột `rule.id`, `rule.description`, `rule.mitre.id` (ví dụ 92052 → T1059.003)."),
  Shot("Hình 3.30", "4 cảnh báo trinh sát lên hàng đợi VT-Guard, đã gán đúng kỹ thuật và mức ưu tiên."),
  Shot("Hình 3.31", "Trang Chi tiết một cảnh báo: luật Sigma tự sinh + xuất xứ (YC1), top-5 sự kiện attention (YC3), dải ba yêu cầu."),
  Shot("Hình 3.32", "Cảnh báo VT-Guard hiển thị trong Discover của Wazuh (chỉ mục `vtguard-alerts-*`)."),
  Lab("Kỳ vọng & điền số liệu"),
  Bul("VT-Guard gán đúng T1016/T1018/T1087.002/T1654; Wazuh gán nhầm sang T1059.003. Điền Bảng 3.19 dòng 2 (số cảnh báo Wazuh, có gán đúng không, số cảnh báo VT-Guard + nguồn, độ trễ)."),

  KB("KỊCH BẢN 3 — Trinh sát chậm (low-and-slow) → độ bền thời gian"),
  Lab("Mục tiêu"), P("Lặp trinh sát với nhịp chậm (lệnh cách nhau 45–240 s), trên DC01; kỳ vọng VT-Guard vẫn gom đúng cửa sổ và cảnh báo (dựa trên nội dung + trình tự, không dựa vào lệnh dồn dập)."),
  Lab("Lệnh (trên DC01)"),
  Cmd([".\\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User \"VTLAB\\admin01\" -UserRole admin `",
       "  -Ttps T1016,T1087.002 -TestNumbers 9,12 -Tempo low_and_slow -Variant powershell"]),
  Lab("Ảnh cần chụp"),
  Shot("Hình 3.33", "Cửa sổ chạy phiên trinh sát nhịp chậm trên DC01 (thấy khoảng cách thời gian giữa các lệnh)."),
  Shot("Hình 3.34", "Cảnh báo VT-Guard cho chuỗi trinh sát rải rác (có thể mất vài phút để đóng cửa sổ im lặng)."),
  Lab("Kỳ vọng & điền số liệu"),
  Bul("VT-Guard vẫn cảnh báo dù lệnh thưa → điền Bảng 3.19 dòng 3. Lưu ý: độ trễ sẽ dài hơn KB2 do chờ đóng cửa sổ theo im lặng (30 s) hoặc khoảng trống (120 s)."),

  H1("4. Kịch bản 4–6 · Trích xuất NTDS và dòng thời gian (trên DC01)"),
  P("⚠ **Kỷ luật snapshot bắt buộc:** trước mỗi phiên T1003.003, khôi phục DC01 về `BASELINE-CLEAN`, chờ dịch vụ AD sẵn sàng, `w32tm /resync /force`; sau phiên khôi phục lại. Tham số `-SnapshotBefore` ghi vào manifest để đối chiếu."),

  KB("KỊCH BẢN 4 — Trích xuất CSDL Active Directory (T1003.003) → YC2"),
  Lab("Mục tiêu"), P("Hành vi nghiêm trọng nhất; kỳ vọng cảnh báo được **cả AI và luật cùng xác nhận** (nguồn `cả hai`, ưu tiên CAO) — giá trị của bộ hợp nhất."),
  Lab("Lệnh (trên DC01, sau khôi phục snapshot)"),
  Cmd([".\\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User \"VTLAB\\admin01\" -UserRole admin `",
       "  -Ttps T1003.003 -TestNumbers 3 -SnapshotBefore \"BASELINE-CLEAN\" -Tempo burst"]),
  Lab("Ảnh cần chụp"),
  Shot("Hình 3.35", "Cửa sổ chạy phiên trích xuất NTDS bằng bộ điều phối trên DC01."),
  Shot("Hình 3.36", "Wazuh trong khung giờ đó: kỳ vọng chỉ luật chung mức 4, không nhận ra đánh cắp thông tin xác thực."),
  Shot("Hình 3.37", "Chi tiết cảnh báo NTDS trên VT-Guard: nguồn quyết định **AI + luật**, luật `VTR-T1003003-01`, T1003.003, ưu tiên CAO."),
  Lab("Kỳ vọng & điền số liệu"),
  Bul("Điền Bảng 3.19 dòng 4: số cảnh báo, nguồn quyết định (`cả hai`), độ trễ. Nhấn mạnh Wazuh không gán T1003.003."),

  KB("KỊCH BẢN 5 — Biến thể NTDS chưa từng thấy (shadow copy) → tổng quát hoá"),
  Lab("Mục tiêu"), P("Biến thể T1003.003 bằng `vssadmin create shadow` (test 1) — **không có trong tập huấn luyện** (Phần B: 6/6 phiên được phát hiện). Kỳ vọng VT-Guard vẫn bắt."),
  Lab("Lệnh (trên DC01, sau khôi phục snapshot)"),
  Cmd([".\\Invoke-VTSession.ps1 -Class attack -HostName DC01 -User \"VTLAB\\admin01\" -UserRole admin `",
       "  -Ttps T1003.003 -TestNumbers 1 -SnapshotBefore \"BASELINE-CLEAN\" -Tempo burst"]),
  Lab("Ảnh cần chụp"),
  Shot("Hình 3.38", "Cửa sổ chạy phiên biến thể shadow copy trên DC01."),
  Shot("Hình 3.39", "Cảnh báo VT-Guard cho biến thể NTDS chưa từng thấy (mở Chi tiết nếu cần)."),
  Lab("Kỳ vọng & điền số liệu"),
  Bul("Điền Bảng 3.19 dòng 5. Lưu ý trung thực: luật khớp phần nào nhờ token chung `create`, còn AI bắt theo chuỗi hành vi."),

  KB("KỊCH BẢN 6 — Dòng thời gian sự cố và tích hợp Wazuh → câu chuyện tấn công"),
  Lab("Mục tiêu"), P("Gom các cảnh báo KB2–KB5 trên cùng máy thành **một sự cố** với chuỗi kỹ thuật theo thời gian (trinh sát → NTDS); đồng thời cho thấy cảnh báo nằm trong Wazuh Dashboard."),
  Lab("Thao tác"),
  Step("Bước 1.", "Mở trang **Dòng thời gian sự cố** trên VT-Guard, chọn sự cố trên DC01 / WIN10-01, xem chuỗi kỹ thuật và biểu đồ diễn biến."),
  Step("Bước 2.", "Trong Wazuh Dashboard, so sánh `wazuh-alerts-*` (rời rạc, mức thấp) với `vtguard-alerts-*` (đã gán kỹ thuật, có ưu tiên) cùng khung thời gian."),
  Lab("Ảnh cần chụp"),
  Shot("Hình 3.40", "Dòng thời gian sự cố — chuỗi kỹ thuật trinh sát đến trích xuất NTDS."),
  Shot("Hình 3.41", "So sánh cảnh báo Wazuh (trái) và cảnh báo VT-Guard trong Wazuh (phải) cùng khung thời gian."),

  H1("5. Kịch bản 7 (MỚI) · Tấn công thủ công KHÔNG qua bộ điều phối"),
  Lab("Vì sao có kịch bản này"),
  P("Sáu kịch bản trên đều sinh phiên qua `Invoke-VTSession.ps1`. Một câu hỏi hội đồng có thể đặt ra: *“liệu VT-Guard phát hiện được là nhờ bộ điều phối / khung mô phỏng?”*. Kịch bản 7 trả lời bằng cách **gõ trực tiếp từng lệnh trinh sát trong một phiên PowerShell tương tác** — không bộ điều phối, không Atomic Red Team — mô phỏng thao tác “hands-on-keyboard” của kẻ tấn công thật."),
  Lab("Cơ sở kỹ thuật (vì sao vẫn phát hiện được)"),
  Bul("Luồng trực tiếp gom sự kiện theo **máy + thời gian**, không cần phiên hay manifest → lệnh gõ tay vẫn được cắt cửa sổ và chấm."),
  Bul("Lệnh gõ tay là tiến trình con của console tương tác, **không khớp dấu hiệu khung mô phỏng** (quy tắc loại R4 chỉ loại tiến trình chạy khung ART/VT nhận biết qua script block) → sự kiện được giữ."),
  Bul("Tiền xử lý **áp đồng nhất**: gộp tiến trình cha `cmd/powershell` thành `<launcher>`, bỏ `conhost` — giống hệt lúc dựng dataset, nên mô hình và luật nhìn thấy cùng dạng đặc trưng."),
  Bul("**Không có manifest** → kịch bản này không chạy `demo_report.py`; đối chiếu bằng ảnh chụp hai màn hình và điền tay vào Bảng 3.19 dòng 7."),
  Lab("Thao tác (trên WIN10-01, tài khoản VTLAB\\user01)"),
  P("Mở một cửa sổ **PowerShell tương tác** (không chạy script), gõ lần lượt các lệnh trinh sát LOTL theo thủ tục Volt Typhoon trong khuyến cáo CISA, nghỉ vài giây giữa các nhóm:"),
  Cmd(["# T1016 - cau hinh mang",
       "ipconfig /all",
       "arp -a",
       "route print",
       "# T1018 - may trong mien",
       "nltest /dclist:vtlab.test",
       "net view /domain",
       "# T1087.002 - tai khoan mien",
       "net group \"Domain Admins\" /domain",
       "net user /domain",
       "# T1654 - liet ke nhat ky",
       "wevtutil qe Security /c:5 /rd:true /f:text"]),
  P("*(Đây là các lệnh quản trị/trinh sát tiêu chuẩn của Windows, đã liệt kê trong Chương I và khuyến cáo CISA; chạy trong lab cô lập. NTDS vẫn chạy qua bộ điều phối ở KB4/KB5 để giữ kỷ luật snapshot — kịch bản gõ tay này chỉ gồm trinh sát.)*"),
  Lab("Ảnh cần chụp"),
  Shot("Hình 3.42", "Cửa sổ PowerShell gõ trực tiếp chuỗi lệnh trinh sát trên WIN10-01 (thấy rõ không gọi Invoke-VTSession / Atomic)."),
  Shot("Hình 3.43", "Wazuh Discover trong khung giờ đó: luật gán nhầm hoặc không gán đúng kỹ thuật."),
  Shot("Hình 3.44", "Chi tiết cảnh báo VT-Guard: kỹ thuật gán đúng, luật Sigma + xuất xứ, top-5 attention — dù chuỗi lệnh gõ tay."),
  Lab("Kỳ vọng & điền số liệu"),
  Bul("Kỳ vọng VT-Guard vẫn gán đúng các kỹ thuật trinh sát. Điền Bảng 3.19 dòng 7 (cột Wazuh và VT-Guard; độ trễ ước lượng theo đồng hồ)."),
  Bul("Nếu kết quả yếu hơn khi chạy qua bộ điều phối, ghi trung thực và nêu lý do (ví dụ cửa sổ gom khác do nhịp gõ tay). Thông điệp cốt lõi: **phát hiện đến từ hành vi trong log, không từ khung mô phỏng.**"),

  H1("6. Sau buổi thực nghiệm · sinh báo cáo và hoàn thiện Word"),
  Lab("Bước 1 — Sinh bảng đối chiếu tự động (KB1–KB5)"),
  P("Chép manifest các phiên (từ `C:\\VT-Guard-runs` trên máy chạy) về `deploy/demo/` trên VT-SIEM01, rồi:"),
  Cmd(["cd ~/vtguard/deploy",
       "chmod -R a+rX demo                 # file phai doc duoc boi uid 1000 trong container",
       "docker compose exec vtguard-live python src/live/demo_report.py \\",
       "  --manifests /demo --env-file /secrets/vtguard.env --out /app/reports/step9/live/m4",
       "docker compose cp vtguard-live:/app/reports/step9/live/m4/demo_report.md ./demo_report.md"]),
  Bul("`demo_report.md` cho mỗi phiên: số cảnh báo Wazuh (≥ mức 4), Wazuh có gán đúng TTP không, số cảnh báo VT-Guard (nguồn `cả hai`), VT-Guard có gán đúng TTP không, kết luận. Đây là nguồn số liệu cho Bảng 3.19 dòng 1–5 và cho Hình 3.45 (chụp lại bảng này)."),
  Lab("Bước 2 — Dán ảnh và điền số liệu vào báo cáo Word"),
  Bul("Mở `report/VT-Guard_BaoCao.docx`, tìm từng khung *[Dán ảnh Hình 3.xx vào đây]*, dán ảnh tương ứng đã chụp."),
  Bul("Tìm các ô **tô vàng** (`[[…]]`) trong Bảng 3.19 và các câu kết quả KB1–KB7, thay bằng số liệu thật từ `demo_report.md` và ảnh chụp."),
  Bul("Cập nhật mục lục: chuột phải vùng mục lục → *Update Field* → *Update entire table*."),
  Lab("Bước 3 — Cập nhật báo cáo bước và tài liệu"),
  Bul("Đưa bảng đối chiếu và nhận xét vào `reports/step9_report.md`; cập nhật `agent.md` (mục 3/6/7)."),
  Bul("Nếu sửa số liệu trong mã dựng báo cáo: sửa `report/ch3_deploy.js` rồi chạy `node report/build.js` (file `.docx` không commit)."),
  Bul("Sau khi hoàn tất và người dùng xác nhận: `git add -A` (không kèm `.docx`), commit, push; gắn tag `step9-done`."),

  H1("7. Xử lý sự cố thường gặp"),
  ...Tb(null,
    ["Hiện tượng", "Nguyên nhân & cách xử lý"],
    [["`docker compose` báo không kết nối được daemon", "Docker chưa chạy → khởi động Docker trên VT-SIEM01 (`sudo systemctl start docker`)."],
     ["`run.py --check` báo 401/403", "Sai tài khoản Indexer → kiểm tra `/secrets/vtguard.env`; tài khoản `vtguard` cần quyền đọc `wazuh-archives-*`."],
     ["PermissionError khi đọc `/secrets/vtguard.env` hoặc cert", "File thuộc root → `chown 1000:1000` (container chạy uid 1000); chép `root-ca.pem` vào `deploy/certs`."],
     ["Không thấy cảnh báo VT-Guard trong Wazuh Discover", "Chưa tạo index pattern `vtguard-alerts-*` → tạo template + index trước (xem DEPLOY); bật `--push-alerts`."],
     ["`demo_report.py` báo lỗi khi dùng `compose run`", "Phải dùng `docker compose exec vtguard-live python …` và ghi vào `/app/reports/step9/live/m4` (trong volume) để lấy ra được."],
     ["VT-Guard cảnh báo trễ > 1 phút", "Bình thường: trễ Wazuh nhận log 40–60 s + chu kỳ đọc 12 s + chờ đóng cửa sổ (im lặng 30 s)."],
     ["Đồng hồ DC01 lệch sau khôi phục snapshot", "`w32tm /resync /force` trên DC01 trước khi chạy; kiểm tra lại khung giờ khi đối chiếu."]],
    [3.2, 6.8]),

  H1("8. Danh mục kiểm hoàn thành (đánh dấu khi xong)"),
  Bul("☐ Triển khai xong, có Hình 3.18–3.22."),
  Bul("☐ KB1 → Hình 3.24–3.26; Bảng 3.19 dòng 1 đã điền."),
  Bul("☐ KB2 → Hình 3.27–3.32; Bảng 3.19 dòng 2 đã điền."),
  Bul("☐ KB3 → Hình 3.33–3.34; Bảng 3.19 dòng 3 đã điền."),
  Bul("☐ KB4 → Hình 3.35–3.37; Bảng 3.19 dòng 4 đã điền."),
  Bul("☐ KB5 → Hình 3.38–3.39; Bảng 3.19 dòng 5 đã điền."),
  Bul("☐ KB6 → Hình 3.40–3.41."),
  Bul("☐ **KB7 (gõ tay) → Hình 3.42–3.44; Bảng 3.19 dòng 7 đã điền.**"),
  Bul("☐ `demo_report.md` sinh xong; Hình 3.45 đã chụp."),
  Bul("☐ Báo cáo Word: đã dán hết ảnh, điền hết ô tô vàng, cập nhật mục lục."),
  Bul("☐ Cập nhật `reports/step9_report.md`, `agent.md`; commit + push; gắn tag `step9-done`."),
];

const doc = new Document({
  creator: "VT-Guard", title: "VT-Guard – hướng dẫn thực nghiệm các kịch bản",
  styles: { default: { document: { run: { font: FONT, size: SZ } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true }, paragraph: { outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "dot", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 460, hanging: 260 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 860, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 2 * CM, bottom: 2 * CM, left: 2.5 * CM, right: 2 * CM } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 22 })] })] }) },
    children: body,
  }],
});

const out = path.join(__dirname, "HuongDan_ThucNghiem.docx");
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log(`-> ${out}`); });
