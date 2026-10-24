// VT-Guard - ban Word tom tat noi dung de lam slide thuyet trinh. Chay: node report/slides.js -> report/VT-Guard_DanY_Slide.docx
// Moi slide: [SLIDE n] tieu de -> Hinh anh / bang / so do -> Noi dung tom tat -> Loi noi goi y. Hinh lay tu report/figures va reports/step9/screenshots.
const fs = require("fs");
const path = require("path");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType, ShadingType,
        BorderStyle, LevelFormat, VerticalAlign, HeightRule, Footer, PageNumber, HeadingLevel } = D;

const FONT = "Times New Roman";
const SZ = 26;                 // 13 pt
const SZ_TBL = 22;             // 11 pt
const CM = 567;
const TEXT_W = 17 * CM;        // A4 21 cm - 2 - 2
const FIG_DIR = path.join(__dirname, "figures");
const SHOT_DIR = path.join(__dirname, "..", "reports", "step9", "screenshots");
const MAX_H_CM = 9.5;
const NAVY = "1F3864", BLUE = "2E75B6", GREEN = "E2EFDA", HEAD = "DDEBF7";

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

let n = 0;
// Thanh tieu de slide: nen xanh dam, chu trang
const Slide = (title, minutes) => { n += 1; return new Paragraph({
  heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 280, after: 100 },
  shading: { fill: NAVY, type: ShadingType.CLEAR, color: "auto" }, indent: { left: 60, right: 60 },
  children: [new TextRun({ text: `[SLIDE ${n}]  `, bold: true, color: "FFC000", font: FONT, size: 28 }),
             new TextRun({ text: title, bold: true, color: "FFFFFF", font: FONT, size: 28 }),
             ...(minutes ? [new TextRun({ text: `   (~${minutes})`, italics: true, color: "D9E1F2", font: FONT, size: 22 })] : [])] }); };

const Part = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 4 } },
  children: [new TextRun({ text, bold: true, color: NAVY, font: FONT, size: 30 })] });

const Label = (text) => new Paragraph({ keepNext: true, spacing: { before: 100, after: 40 },
  children: [new TextRun({ text: "▸ " + text, bold: true, color: BLUE, font: FONT, size: SZ })] });
const Bul = (text, level = 0) => new Paragraph({ children: runs(text), numbering: { reference: "dot", level },
  spacing: { after: 30, line: 276 }, alignment: AlignmentType.LEFT });
const Note = (text) => new Paragraph({ spacing: { before: 60, after: 120, line: 276 }, indent: { left: 360 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: "A9D08E", space: 8 } },
  children: [new TextRun({ text: "Lời nói gợi ý: ", bold: true, italics: true, color: "548235", font: FONT, size: 24 }),
             ...runs(text, { italics: true, size: 24, color: "404040" })] });
const Line = (text) => new Paragraph({ children: runs(text), spacing: { after: 40, line: 276 } });

function pngSize(file) { const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b }; }
// Hinh co san: chen anh + ten tep de chep sang slide
function Img(file, caption, widthCm = 12) {
  const f = fs.existsSync(path.join(FIG_DIR, file)) ? path.join(FIG_DIR, file) : path.join(SHOT_DIR, file);
  const rel = path.relative(path.join(__dirname, ".."), f).split(path.sep).join("/");
  const { w, h, data } = pngSize(f);
  const cm = Math.min(widthCm, MAX_H_CM * w / h);   // anh doc (chup dashboard) gioi han chieu cao
  const wpx = Math.round(cm / 2.54 * 96), hpx = Math.round(wpx * h / w);
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 60, after: 20 },
            children: [new ImageRun({ type: "png", data, transformation: { width: wpx, height: hpx },
                                      altText: { title: caption, description: caption, name: file } })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
            children: [new TextRun({ text: caption + "  ", italics: true, font: FONT, size: 22 }),
                       new TextRun({ text: `[${rel}]`, font: "Consolas", size: 18, color: "7F7F7F" })] })];
}
// Anh chup thuc nghiem (lay tu bao cao Word sau khi dan anh)
const dash = { style: BorderStyle.DASHED, size: 6, color: "A6A6A6" };
function Shot(text) {
  const w = TEXT_W - 2 * CM;
  return new Table({ width: { size: w, type: WidthType.DXA }, columnWidths: [w], alignment: AlignmentType.CENTER,
    rows: [new TableRow({ height: { value: Math.round(1.3 * CM), rule: HeightRule.ATLEAST }, children: [new TableCell({
      width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, borders: { top: dash, bottom: dash, left: dash, right: dash },
      shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" }, margins: { left: 120, right: 120, top: 60, bottom: 60 },
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: runs("[ẢNH THỰC NGHIỆM] " + text, { italics: true, size: 22, color: "595959" }) })] })] })] });
}

const bd = { style: BorderStyle.SINGLE, size: 4, color: "8EA9DB" };
function Tb(header, rows, ratio, hl = []) {
  const total = ratio.reduce((a, b) => a + b, 0);
  const cw = ratio.map(r => Math.floor(TEXT_W * r / total)); cw[cw.length - 1] += TEXT_W - cw.reduce((a, b) => a + b, 0);
  const row = (cells, head, h) => new TableRow({ tableHeader: head, cantSplit: true, children: cells.map((c, i) => new TableCell({
    borders: { top: bd, bottom: bd, left: bd, right: bd }, width: { size: cw[i], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: head ? { fill: HEAD, type: ShadingType.CLEAR, color: "auto" } : (h ? { fill: GREEN, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 30, bottom: 30, left: 70, right: 70 },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, spacing: { line: 252 },
      children: runs(String(c), { size: SZ_TBL, ...(head || h ? { bold: true } : {}) }) })] })) });
  return [new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: cw,
            rows: [row(header, true, false), ...rows.map((r, i) => row(r, false, hl.includes(i)))] }),
          new Paragraph({ spacing: { after: 60 }, children: [] })];
}

// ---------------------------------------------------------------- noi dung
const intro = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "DÀN Ý NỘI DUNG SLIDE THUYẾT TRÌNH", bold: true, color: NAVY, font: FONT, size: 34 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: "VT-GUARD: PHÁT HIỆN TẤN CÔNG APT KIỂU VOLT TYPHOON KẾT HỢP MÔ HÌNH CHUỖI GRU-ATTENTION", bold: true, font: FONT, size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: "VÀ LUẬT TỰ SINH TRÊN NỀN TẢNG SIEM WAZUH", bold: true, font: FONT, size: 26 })] }),
  Label("Cách dùng tài liệu"),
  Bul("Mỗi khối **[SLIDE n]** tương ứng một slide: *tiêu đề* → *hình ảnh / bảng / sơ đồ* → *nội dung tóm tắt* (đưa lên slide) → *lời nói gợi ý* (không đưa lên slide)."),
  Bul("Hình có sẵn được chèn kèm đường dẫn tệp gốc (ví dụ `report/figures/d_arch.png`) để chép thẳng vào PowerPoint với độ phân giải đầy đủ."),
  Bul("Ô **[ẢNH THỰC NGHIỆM]** là ảnh chụp thực nghiệm trên hạ tầng thật — lấy từ ảnh đã dán vào báo cáo Word (Hình 3.18–3.42). Ô **tô vàng** là số liệu điền sau khi chạy đủ các kịch bản."),
  Bul("Tổng **32 slide chính** cho khoảng **20 phút** + 3 slide dự phòng (33–35) cho phần hỏi đáp. Trọng tâm thời gian dành cho Phần 3–4 (kết quả và triển khai)."),
  ...Tb(["Phần", "Slide", "Thời lượng"],
    [["Mở đầu, bối cảnh, mục tiêu", "1 – 7", "3 phút"],
     ["1. Kiến trúc và hạ tầng", "8 – 10", "2 phút"],
     ["2. Dữ liệu và phương pháp đánh giá", "11 – 14", "3 phút"],
     ["3. Kết quả: VT-Seq (YC3), luật tự sinh (YC1), hợp nhất (YC2), so sánh Wazuh", "15 – 24", "7 phút"],
     ["4. Sản phẩm, triển khai lên Wazuh, thực nghiệm trực tiếp + demo", "25 – 29", "5 phút"],
     ["Kết luận, hướng phát triển, hỏi đáp", "30 – 32", "1 phút"]],
    [6, 1.6, 1.4]),
];

const opening = [
  Part("MỞ ĐẦU"),
  Slide("Trang bìa", "20 giây"),
  Label("Hình ảnh"), Line("Logo trường; nền tối có hình mạng máy tính / lá chắn; có thể đặt mờ sơ đồ kiến trúc `d_arch.png` phía sau."),
  Label("Nội dung tóm tắt"),
  Bul("**VT-GUARD**: phát hiện tấn công APT kiểu Volt Typhoon kết hợp mô hình chuỗi GRU-Attention và luật tự sinh trên nền tảng SIEM Wazuh"),
  Bul("Môn học: Giám sát an ninh mạng"),
  Bul("Giảng viên hướng dẫn: [[Họ và tên]] · Sinh viên thực hiện: [[Họ và tên – MSSV – Lớp]]"),
  Note("Kính chào thầy cô và các bạn. Em xin trình bày đề tài VT-Guard — một lớp phân tích thông minh gắn thêm vào Wazuh để bắt kiểu tấn công mà luật có sẵn bỏ sót."),

  Slide("Nội dung trình bày", "20 giây"),
  Label("Hình ảnh"), Line("Thanh tiến trình 5 khối ngang (mỗi khối một biểu tượng)."),
  Label("Nội dung tóm tắt"),
  Bul("Bối cảnh và mục tiêu đề tài"), Bul("Kiến trúc hệ thống và hạ tầng lab Wazuh"), Bul("Dữ liệu và phương pháp đánh giá"),
  Bul("Kết quả: mô hình VT-Seq · luật Sigma tự sinh · hợp nhất AI + luật · so sánh với Wazuh"),
  Bul("Sản phẩm, triển khai lên hạ tầng và demo trực tiếp"), Bul("Kết luận và hướng phát triển"),

  Slide("Bối cảnh: APT “sống nhờ tài nguyên sẵn có” (LOTL)", "40 giây"),
  Label("Hình ảnh"), Line("Hai cột đối lập: *“Quản trị viên”* và *“Kẻ tấn công”* cùng gõ một lệnh `net group \"Domain Admins\" /domain` — dấu hỏi ở giữa."),
  Label("Nội dung tóm tắt"),
  Bul("APT hiện đại không cần mã độc: chỉ dùng **công cụ có sẵn của Windows** (`net`, `nltest`, `ipconfig`, `wevtutil`, `ntdsutil`, PowerShell)."),
  Bul("Né được cơ chế phát hiện theo chữ ký, tồn tại hàng tháng đến hàng năm, hoà lẫn vào hoạt động quản trị."),
  Bul("Ranh giới giữa quản trị viên và kẻ tấn công nằm ở **ngữ cảnh và trình tự** chuỗi sự kiện, không nằm ở từng lệnh đơn lẻ."),
  Note("Cùng một câu lệnh, có thể là quản trị viên kiểm kê tài khoản, cũng có thể là kẻ tấn công trinh sát trước khi leo thang. Đó là lý do bài toán này khó."),

  Slide("Vấn đề: SIEM luật tĩnh bỏ sót LOTL", "40 giây"),
  Label("Bảng (số đo thực tế trên dữ liệu của đề tài)"),
  ...Tb(["Luật Wazuh có sẵn (B0)", "Kết quả"],
    [["Số kỹ thuật gán đúng trên 5 kỹ thuật nghiên cứu", "**1/5** (F1 = 0 ở T1016, T1018, T1654, T1003.003)"],
     ["macro-F1 theo kỹ thuật trên dữ liệu mới", "**0,12**"],
     ["Cảnh báo nhầm trên 88 cửa sổ quản trị hợp lệ", "**17/88** (19,3%)"],
     ["Luật hay bắn nhất cho mọi hành vi LOTL", "92052 “command prompt started by an abnormal process” → gán T1059.003 (sai kỹ thuật)"]],
    [5, 5]),
  Label("Nội dung tóm tắt"),
  Bul("Luật tĩnh đánh giá **từng sự kiện riêng lẻ** → không thấy chuỗi hành vi."),
  Bul("Học máy thuần thì chính xác nhưng là **hộp đen** — SOC không kiểm chứng được."),
  Bul("⇒ Cần một lớp phân tích **vừa học theo chuỗi, vừa sinh luật giải thích được**, gắn trực tiếp vào SIEM sẵn có."),
  Note("Đây là số đo trên chính dữ liệu của đề tài, không phải giả định: Wazuh mù 4 trên 5 kỹ thuật và gắn nhầm tất cả thành 'chạy cmd bất thường'."),

  Slide("Đối tượng nghiên cứu: Volt Typhoon", "40 giây"),
  Label("Sơ đồ"), ...Img("d_killchain.png", "Chuỗi tấn công Volt Typhoon và 5 kỹ thuật thuộc phạm vi đề tài", 14),
  Label("Nội dung tóm tắt"),
  Bul("Nhóm APT được nhà nước hậu thuẫn, nhắm **hạ tầng trọng yếu** (viễn thông, năng lượng, nước, giao thông) — khuyến cáo CISA AA23-144A, AA24-038A."),
  Bul("Duy trì truy cập **≥ 5 năm** với mục đích “tiền định vị”; hành vi **LOTL thuần tuý**, hands-on-keyboard."),
  Bul("Chuỗi điển hình: trinh sát mạng → trinh sát máy → liệt kê tài khoản miền → liệt kê nhật ký → **đánh cắp CSDL Active Directory (NTDS.dit)**."),

  Slide("Năm kỹ thuật MITRE ATT&CK được chọn", "30 giây"),
  Label("Bảng"),
  ...Tb(["Mã", "Kỹ thuật", "Thủ tục Volt Typhoon (CISA)"],
    [["T1016", "System Network Configuration Discovery", "ipconfig /all, netsh, arp -a"],
     ["T1018", "Remote System Discovery", "nltest /dclist, net view, ping"],
     ["T1087.002", "Account Discovery: Domain Account", "net user /domain, net group \"Domain Admins\""],
     ["T1654", "Log Enumeration", "wevtutil qe Security (sự kiện 4624)"],
     ["T1003.003", "OS Credential Dumping: NTDS", "ntdsutil “ifm create full”, vssadmin shadow copy"]],
    [1.3, 3.6, 4.4]),
  Label("Nội dung tóm tắt"),
  Bul("Có trong khuyến cáo chính thống · dùng công cụ hợp lệ, khó phân biệt với quản trị · tạo thành chuỗi trinh sát → đánh cắp thông tin xác thực · tái hiện an toàn bằng Atomic Red Team."),
  Bul("Bài toán **đa nhãn**: mỗi cửa sổ sự kiện vừa được đánh giá độc hại, vừa được gán đúng mã kỹ thuật ATT&CK."),

  Slide("Mục tiêu và ba yêu cầu của đề tài", "40 giây"),
  Label("Hình ảnh"), Line("Ba thẻ lớn màu khác nhau YC1 · YC2 · YC3 (sẽ lặp lại làm “nhãn” ở góc các slide kết quả tương ứng)."),
  Label("Nội dung tóm tắt"),
  Bul("**Mục tiêu:** xây dựng VT-Guard — lớp phân tích gắn thêm vào Wazuh, phát hiện chuỗi LOTL ở mức cửa sổ sự kiện, gán đúng kỹ thuật, giải thích được cảnh báo."),
  Bul("**YC1 – Luật tự sinh có xuất xứ:** quy nạp tự động từ dữ liệu → chuẩn Sigma, truy vết được về dữ liệu sinh ra luật."),
  Bul("**YC2 – Hợp nhất AI + luật:** cảnh báo có mức tin cậy và lời giải thích."),
  Bul("**YC3 – Mô hình chuỗi tuỳ biến:** GRU + attention đa nhiệm, chứng minh đóng góp từng thành phần bằng ablation."),
  Note("Ba yêu cầu này là xương sống của bài; mỗi kết quả phía sau em sẽ gắn nhãn YC tương ứng."),
];

const arch = [
  Part("PHẦN 1. KIẾN TRÚC VÀ HẠ TẦNG"),
  Slide("Kiến trúc tổng thể VT-Guard", "50 giây"),
  Label("Sơ đồ"), ...Img("d_arch.png", "Kiến trúc năm tầng của VT-Guard", 15),
  Label("Nội dung tóm tắt"),
  Bul("**Gắn thêm, không thay thế Wazuh:** chỉ cần quyền đọc `wazuh-archives-*`, ghi cảnh báo vào chỉ mục riêng `vtguard-alerts-*`."),
  Bul("5 tầng: thu thập (Wazuh agent) → xử lý (chuẩn hoá, gán nhãn, cửa sổ, đặc trưng) → hai bộ phát hiện song song (**VT-Seq** + **Auto Rule Engine**) → **hợp nhất F3-B** → vận hành (pipeline, luồng trực tiếp, dashboard, Docker)."),

  Slide("Hạ tầng lab giám sát Wazuh", "40 giây"),
  Label("Sơ đồ"), ...Img("d_lab.png", "Mô hình lab: hai endpoint Windows, máy chủ Wazuh và VT-Guard", 14),
  Label("Nội dung tóm tắt"),
  Bul("Mạng ảo cách ly **VMnet2 10.20.30.0/24**, không Internet; miền AD `CORP.VTLAB.TEST`."),
  Bul("**DC01** (Domain Controller) + **WIN10-01** (máy trạm): Wazuh agent, Sysmon, kiểm toán 4688 kèm dòng lệnh, PowerShell logging, SACL thư mục NTDS."),
  Bul("**VT-SIEM01 (10.20.30.10)**: wazuh-docker 4.14.8 (Manager, Indexer, Dashboard); bật archives JSON để lưu **mọi** sự kiện."),
  Bul("5 kênh nhật ký: Sysmon, Security, PowerShell, Application, System."),

  Slide("Mô phỏng tấn công và hoạt động quản trị “dễ nhầm”", "50 giây"),
  Label("Bảng"),
  ...Tb(["Lớp phiên", "Số phiên", "Cách sinh"],
    [["Tấn công", "151", "Atomic Red Team theo mã test, 5 kỹ thuật, 2 nhịp (dồn dập / chậm rải rác)"],
     ["Lành tính", "164", "thao tác người dùng, kiểm tra mạng"],
     ["Quản trị hợp lệ (hard-negative)", "164", "**dùng đúng công cụ của 5 kỹ thuật**: kiểm kê tài khoản, rà soát log, quét dải, bảo trì CSDL AD…"]],
    [3, 1.3, 6]),
  Label("Nội dung tóm tắt"),
  Bul("Bộ điều phối `Invoke-VTSession.ps1` ghi **manifest** từng phiên (máy, tài khoản, kỹ thuật, thời gian, PID cần loại) — “sự thật nền” cho gán nhãn."),
  Bul("Mọi lớp chạy dưới **cả hai tài khoản** user01 / admin01 → tên tài khoản không thành tín hiệu nhãn."),
  Bul("T1003.003 chạy trên DC01 với **kỷ luật snapshot**: khôi phục trạng thái sạch trước và sau mỗi phiên."),
  Note("Điểm mấu chốt: quản trị hợp lệ dùng đúng những công cụ kẻ tấn công dùng, nên mô hình không thể học mẹo 'thấy nltest là tấn công'."),
];

const data = [
  Part("PHẦN 2. DỮ LIỆU VÀ PHƯƠNG PHÁP ĐÁNH GIÁ"),
  Slide("Quy trình thực nghiệm 9 bước và 3 nguyên tắc khoa học", "40 giây"),
  Label("Sơ đồ"), ...Img("d_process.png", "Chín bước thực nghiệm, mỗi bước đóng bằng git tag", 15),
  Label("Nội dung tóm tắt"),
  Bul("**Khoá trước khi chấm:** cấu hình, ngưỡng, tham số hợp nhất được commit **trước** khi chấm tập kiểm thử; chấm **một lần**."),
  Bul("**Mọi quyết định chỉ dựa trên Train** (dự đoán out-of-fold, kiểm định chéo 5 fold theo nhóm phiên)."),
  Bul("**Mọi tuyên bố “tốt hơn” đều qua kiểm định:** bootstrap 95% + paired bootstrap + hiệu chỉnh Holm."),

  Slide("Thu thập và gán nhãn theo cây tiến trình", "50 giây"),
  Label("Sơ đồ"), ...Img("d_label.png", "Gán nhãn theo manifest + cây tiến trình Sysmon; loại bỏ dấu vết công cụ mô phỏng", 14),
  Label("Nội dung tóm tắt"),
  Bul("**479 phiên** trong 10 đợt · 423 597 sự kiện thô → **62 917 sự kiện** sạch (5 509 độc hại)."),
  Bul("Nhãn đến từ **manifest + cây tiến trình** (process_guid), *không* từ regex dòng lệnh → luật sinh ra không “tìm lại” regex gán nhãn."),
  Bul("Loại hơn **350 000 sự kiện** của công cụ mô phỏng để chống rò rỉ nhãn; bộ gán nhãn hoàn thiện qua 5 phiên bản, mỗi lần **đối chiếu từng sự kiện**."),

  Slide("Bộ dữ liệu đóng băng dataset-v1.2", "50 giây"),
  Label("Biểu đồ + bảng"), ...Img("c_splits.png", "Số cửa sổ âm / dương của bốn tập", 11),
  ...Tb(["Tập", "Cửa sổ", "Dương", "Vai trò"],
    [["Train", "483", "176", "huấn luyện + mọi lựa chọn (OOF)"],
     ["T-clean", "89", "42", "kiểm thử cùng phân phối"],
     ["T-hard", "88", "0", "**quản trị hợp lệ khó** — đo cảnh báo nhầm"],
     ["T-novel", "149", "54", "**đợt mới theo thời gian + biến thể NTDS chưa thấy**"]],
    [1.5, 1.2, 1.2, 5]),
  Label("Nội dung tóm tắt"),
  Bul("**809 cửa sổ** (64 sự kiện, bước 32), mỗi sự kiện **268 chiều**: 7 trường phân loại + dòng lệnh băm n-gram 256 chiều + 5 đặc trưng số."),
  Bul("Phát hiện và trung hoà **dấu vết bộ sinh dữ liệu** (conhost, đường dẫn cmd, `>nul`, bất đối xứng 4688): mức tách đặc trưng đơn lẻ **0,942 → 0,735** ⇒ mô hình buộc phải học hành vi."),
  Bul("Đóng băng bằng git tag + sha256 sau **12/12 kiểm tra chấp nhận**."),
  Note("Đây là điểm mà nhiều nghiên cứu dùng dữ liệu mô phỏng mắc phải: mô hình học cách công cụ được khởi chạy chứ không học hành vi. Đề tài đã đo và loại bỏ nó."),

  Slide("Khung đánh giá và các mô hình cơ sở", "40 giây"),
  Label("Bảng"),
  ...Tb(["Mô hình cơ sở", "Mô tả"],
    [["B0", "luật Wazuh có sẵn (mức luật ≥ L chọn trên Train)"],
     ["B1", "TF-IDF + hồi quy logistic"],
     ["B2", "LightGBM trên đặc trưng tỉ lệ"],
     ["B3", "GRU thuần (không attention, đơn nhiệm)"]],
    [1.5, 8]),
  Label("Nội dung tóm tắt"),
  Bul("Chỉ số chính: **macro-F1 theo kỹ thuật**; F1, PR-AUC nhị phân; **cảnh báo nhầm trên T-hard**; recall theo phiên cho T1003.003; **phát hiện sớm** (k = 4…32 sự kiện đầu)."),
  Bul("Ngưỡng chọn trên Train OOF rồi khoá; ablation: (a) đầy đủ, (b) **bỏ tên tiến trình**, (c′) che sự kiện nền một phía."),
  Bul("Học máy giảm cảnh báo nhầm từ **17/88 (Wazuh) xuống 0–5/88**."),
];

const results = [
  Part("PHẦN 3. KẾT QUẢ NGHIÊN CỨU"),
  Slide("YC3 · Mô hình chuỗi tuỳ biến VT-Seq", "50 giây"),
  Label("Sơ đồ"), ...Img("d_vtseq.png", "Kiến trúc VT-Seq: GRU + attention, đa nhiệm", 14),
  Label("Nội dung tóm tắt"),
  Bul("Nhúng sự kiện (phân loại + dòng lệnh + số) → **GRU 96 chiều** → **attention cộng** chỉ ra sự kiện quan trọng → **2 đầu ra**: độc hại / 5 kỹ thuật."),
  Bul("Chống học đường tắt: **cắt ngẫu nhiên độ dài** cửa sổ; ngưỡng **FPR ≤ 1%** trên OOF (ưu tiên ít báo động giả cho SOC)."),
  Bul("Triển khai **VT-Seq-ens**: trung bình 5 seed, xuất **ONNX** — sai lệch ≤ 3,3·10⁻⁷, **~1 ms/cửa sổ trên CPU**."),

  Slide("YC3 · Ablation: attention là bước nhảy chính", "50 giây"),
  Label("Biểu đồ"), ...Img("c_ablation.png", "Đóng góp của từng thành phần M0 → M4b", 13),
  Label("Bảng rút gọn"),
  ...Tb(["Cấu hình", "macro-F1 OOF", "F1 T1654 (T-novel)"],
    [["M0 – GRU thuần (= B3)", "0,774", "0,46"],
     ["M1 – + attention", "**0,822**", "**0,73**"],
     ["M3 – + đa nhiệm + cắt độ dài (triển khai)", "0,825", "0,69"]],
    [5, 2, 2.5], [1]),
  Label("Nội dung tóm tắt"),
  Bul("Thêm attention: macro-F1 OOF **+0,048**; kỹ thuật khó nhất T1654 **0,46 → 0,73**; mọi seed có attention vượt mọi seed không attention."),
  Bul("Đa nhiệm + cắt độ dài làm mô hình **ổn định**: độ lệch chuẩn giữa các seed giảm từ 0,08 xuống **0,01**."),
  Bul("Bỏ hẳn tên công cụ vẫn đạt macro-F1 **0,83** (LightGBM sụp còn 0,45) ⇒ VT-Seq học **hành vi**, không học tên tiến trình."),

  Slide("YC3 · Kết quả VT-Seq trên tập kiểm thử", "50 giây"),
  Label("Bảng"),
  ...Tb(["Mô hình", "F1 T-clean", "F1 T-novel", "macro-F1 kỹ thuật (novel)", "Cảnh báo nhầm T-hard", "Phiên NTDS mới"],
    [["B0 – luật Wazuh", "0,988", "0,898", "0,12", "17/88", "0 gán đúng"],
     ["B3 – GRU thuần", "1,000", "0,938", "0,75", "1,7/88", "6/6"],
     ["**VT-Seq-ens**", "**1,000**", "**0,964**", "**0,82** (cao nhất)", "**1/88**", "**6/6**"]],
    [2.4, 1.3, 1.3, 2.2, 1.8, 1.6], [2]),
  Label("Nội dung tóm tắt"),
  Bul("F1 **1,000** trên T-clean, **0,964** [0,927; 0,992] trên dữ liệu mới; bắt đủ **6/6** phiên trích xuất NTDS biến thể chưa từng thấy."),
  Bul("Vượt GRU thuần **có ý nghĩa thống kê** sau hiệu chỉnh Holm: macro-F1 kỹ thuật **+0,092** (p = 0,009) — trả lời RQ1."),
  Bul("So với luật Wazuh: macro-F1 kỹ thuật **0,82 vs 0,12**, cảnh báo nhầm **1 vs 17**."),

  Slide("YC3 · Giải thích được: attention trung thực", "30 giây"),
  Label("Bảng"),
  ...Tb(["Xoá k sự kiện", "Điểm giảm khi xoá top-k attention", "Khi xoá ngẫu nhiên"],
    [["k = 1", "0,025", "0,001"], ["k = 3", "0,111", "0,002"], ["k = 5", "**0,230**", "0,003"]],
    [2, 4, 3]),
  Label("Hình ảnh"), ...Img("A2_chi_tiet_truc_tiep.png", "Top-5 sự kiện attention trên trang Chi tiết cảnh báo", 10),
  Label("Nội dung tóm tắt"),
  Bul("Xoá các sự kiện mô hình “chú ý” làm điểm giảm **gấp ~75 lần** so với xoá ngẫu nhiên; khoảng tin cậy không chứa 0 ở mọi k."),
  Bul("⇒ Top-5 sự kiện attention là **lời giải thích đáng tin** cho phân tích viên."),

  Slide("YC1 · Bộ sinh luật tự động (Auto Rule Engine)", "50 giây"),
  Label("Sơ đồ"), ...Img("d_rules.png", "Từ Train đến luật Sigma có xuất xứ", 14),
  Label("Nội dung tóm tắt"),
  Bul("Atom “cửa sổ có sự kiện thoả …” (tiến trình, cha, mã sự kiện, token dòng lệnh) → ánh xạ **chính xác** sang Sigma."),
  Bul("**Danh sách vị từ cấm** chặn mọi dấu vết công cụ mô phỏng (446/706 atom bị chặn)."),
  Bul("So sánh 3 engine: **RIPPER 0,756** > cây quyết định 0,675 / 0,658 (macro-F1 OOF)."),
  Bul("5 cổng chất lượng: precision OOF ≥ 0,9, support ≥ 10, tái lập trên fold, khử trùng → **11 luật** được duyệt."),

  Slide("YC1 · 11 luật Sigma tự sinh", "50 giây"),
  Label("Bảng"),
  ...Tb(["Kỹ thuật", "Luật Wazuh có sẵn", "Luật tự sinh", "Token học được (khớp thủ tục Volt Typhoon)"],
    [["T1018", "0,00", "**0,47**", "`nltest /dclist`, `%USERDNSDOMAIN%` (luật tương quan)"],
     ["T1654", "0,00", "**0,62**", "`wevtutil enum-logs`"],
     ["T1003.003", "0,00", "**1,00**", "`ntdsutil … ifm create full`"],
     ["Nhị phân – cảnh báo nhầm T-hard", "17/88", "**0/88**", "`adsisearcher … .FindAll()`, `net … administrator`"]],
    [2.6, 1.8, 1.6, 5]),
  Label("Hình ảnh"), ...Img("B3_luat_sigma.png", "Trang Luật Sigma trên dashboard (YAML + xuất xứ)", 11),
  Label("Nội dung tóm tắt"),
  Bul("Kiểm định **pySigma 2.0.1 + 31 validator: 0 lỗi**; bộ so khớp đọc YAML trùng **100%** với vị từ luật."),
  Bul("**0 cảnh báo nhầm** trên 88 cửa sổ quản trị hợp lệ; phủ **3 kỹ thuật** mà luật Wazuh bỏ sót."),
  Bul("Mỗi luật có **xuất xứ đầy đủ**: cửa sổ/phiên Train sinh ra luật, literal gốc, kết quả từng fold."),
  Note("Token mà máy tự học trùng khớp với các lệnh trong khuyến cáo CISA về Volt Typhoon — đây là dấu hiệu luật học đúng hành vi."),

  Slide("YC2 · Hợp nhất AI + luật F3-B", "50 giây"),
  Label("Sơ đồ"), ...Img("d_fusion.png", "Bộ hợp nhất F3-B và phân mức tin cậy cảnh báo", 14),
  Label("Bảng"),
  ...Tb(["Cấu hình", "F1 T-novel", "PR-AUC T-novel", "macro-F1 kỹ thuật"],
    [["Chỉ luật", "0,878", "0,852", "0,42"],
     ["Chỉ AI (VT-Seq-ens)", "0,964", "0,986", "0,82"],
     ["**F3-B (triển khai)**", "**0,964**", "**0,998**", "**0,82**"]],
    [3.5, 2, 2, 2.2], [2]),
  Label("Nội dung tóm tắt"),
  Bul("Điểm hợp nhất **s = p + 0,1·r** (thêm kênh luật theo từng kỹ thuật); chọn trên OOF, khoá trước khi chấm."),
  Bul("Hơn chỉ-luật **có ý nghĩa thống kê**: macro-F1 kỹ thuật **+0,40**, PR-AUC **+0,15** (p Holm = 0,006)."),
  Bul("PR-AUC đạt **0,998** — xếp hạng cảnh báo gần như hoàn hảo."),

  Slide("YC2 · Cảnh báo phân mức tin cậy và giải thích được", "50 giây"),
  Label("Bảng"),
  ...Tb(["Nguồn quyết định", "Mức ưu tiên", "Độ chính xác (101 cảnh báo, 3 tập kiểm thử)"],
    [["**AI + luật cùng xác nhận**", "CAO", "**76/76 = 100%**"],
     ["Chỉ AI", "CẦN XEM LẠI (kèm top-5 attention)", "20/25"]],
    [3, 3, 4], [0]),
  Label("Nội dung tóm tắt"),
  Bul("Nhóm ưu tiên CAO **đúng 76/76** → phân tích viên xử lý ngay, không cần nghi ngờ."),
  Bul("**75%** cảnh báo có luật Sigma kèm xuất xứ; **100%** có top-5 sự kiện attention."),
  Bul("AI **chặn được luật khớp nhầm**: lệnh quản trị `auditpol … \"System Integrity\"` khớp luật nhưng không sinh cảnh báo."),
  Bul("⇒ Trả lời RQ3: hợp nhất bổ sung **minh bạch, xuất xứ, phân mức tin cậy** mà không đánh đổi độ chính xác."),

  Slide("So sánh tổng hợp: VT-Guard và luật Wazuh", "50 giây"),
  Label("Biểu đồ"), ...Img("c_per_ttp_t_novel.png", "F1 theo kỹ thuật trên dữ liệu mới T-novel", 14),
  ...Img("c_compare.png", "macro-F1 kỹ thuật (trái) và cảnh báo nhầm trên quản trị hợp lệ (phải)", 14),
  Label("Nội dung tóm tắt"),
  Bul("Wazuh chỉ gán được 1/5 kỹ thuật; **VT-Guard phủ đủ 5/5**: T1016 0,81 · T1018 0,85 · T1087.002 0,76 · T1654 0,68 · T1003.003 **1,00**."),
  Bul("macro-F1 kỹ thuật **0,82 vs 0,12** (gấp ~7 lần) · cảnh báo nhầm **1 vs 17**."),
  Note("Đây là slide quan trọng nhất của phần kết quả: cùng một dữ liệu, Wazuh mù 4 kỹ thuật, VT-Guard bắt đủ cả năm và báo nhầm ít hơn 17 lần."),

  Slide("Phát hiện sớm: chặn từ giai đoạn trinh sát", "30 giây"),
  Label("Biểu đồ"), ...Img("c_early.png", "Recall theo số sự kiện đầu tiên k quan sát được", 13),
  Label("Nội dung tóm tắt"),
  Bul("Chỉ với **4 sự kiện đầu**: VT-Seq-ens recall **0,88** (T-clean) và **1,00** (T-novel); luật Wazuh 0,69 / 0,87."),
  Bul("Trích xuất NTDS: VT-Guard bắt **6/6 phiên ngay từ k = 4**; luật Wazuh phải tới k = 32."),
  Bul("⇒ Cảnh báo **trước khi** CSDL tài khoản miền bị đánh cắp."),
];

const product = [
  Part("PHẦN 4. SẢN PHẨM, TRIỂN KHAI VÀ THỰC NGHIỆM TRỰC TIẾP"),
  Slide("Sản phẩm: pipeline, dashboard SOC, đóng gói Docker", "50 giây"),
  Label("Hình ảnh"), ...Img("A1_truc_tiep_hang_doi.png", "Dashboard Phần A – Giám sát SIEM thời gian thực", 13),
  ...Img("B1_ket_qua_nghien_cuu.png", "Dashboard Phần B – Kết quả nghiên cứu", 13),
  Label("Nội dung tóm tắt"),
  Bul("Pipeline đầu–cuối: đặc trưng → ONNX VT-Seq-ens → 11 luật Sigma → F3-B → cảnh báo; **2–3 ms/cửa sổ CPU một luồng**, 0 lệch so với kết quả đã chấm."),
  Bul("Dashboard tiếng Việt 2 phần: **A – SIEM thời gian thực** (hàng đợi, chi tiết cảnh báo, dòng thời gian sự cố, ma trận MITRE) · **B – Kết quả nghiên cứu**."),
  Bul("Image `vtguard:step9` (223 MB) chạy offline; lệnh `verify` tái lập toàn bộ số liệu báo cáo: **ĐẠT 7/7, 0 lệch, ~10 giây**."),

  Slide("Triển khai VT-Guard lên hạ tầng giám sát Wazuh", "50 giây"),
  Label("Sơ đồ"), ...Img("d_deploy.png", "VT-Guard chạy cạnh wazuh-docker trên VT-SIEM01", 14),
  ...Img("d_deploy_steps.png", "Tám bước triển khai", 14),
  Shot("Ảnh: hai container vtguard-live, vtguard-dashboard ở trạng thái healthy (Hình 3.20 trong báo cáo)"),
  Label("Nội dung tóm tắt"),
  Bul("Chạy **trên chính máy chủ SIEM 10.20.30.10**, dashboard cổng riêng **:8501**; Wazuh giữ nguyên cấu hình."),
  Bul("Kết nối Indexer qua mạng Docker nội bộ, **xác thực TLS đầy đủ**; tài khoản riêng **quyền tối thiểu** (đọc archives, ghi `vtguard-alerts-*`)."),
  Bul("Vận hành ổn định: checkpoint, tự thử lại khi mất kết nối, healthcheck, dọn trạng thái cũ; cảnh báo **hiển thị ngay trong Wazuh Dashboard**."),

  Slide("Thực nghiệm trực tiếp theo kịch bản", "50 giây"),
  Label("Sơ đồ + bảng"), ...Img("d_demo_flow.png", "Quy trình thực hiện và đánh giá một kịch bản", 13),
  ...Tb(["KB", "Kịch bản", "Chứng minh"],
    [["1", "Quản trị hợp lệ (phản chứng)", "VT-Guard im lặng, không báo nhầm"],
     ["2", "Trinh sát LOTL 4 kỹ thuật", "Wazuh gán sai, VT-Guard gán đúng (YC1, YC3)"],
     ["3", "Trinh sát chậm (low-and-slow)", "bền với nhịp tấn công rải rác"],
     ["4", "Trích xuất NTDS", "AI + luật cùng xác nhận, ưu tiên CAO (YC2)"],
     ["5", "Biến thể NTDS chưa thấy", "tổng quát hoá sang biến thể mới"],
     ["6", "Dòng thời gian sự cố", "dựng lại chuỗi tấn công, tích hợp Wazuh"]],
    [0.7, 4, 5]),

  Slide("Kết quả thực nghiệm trực tiếp: Wazuh ↔ VT-Guard", "60 giây"),
  Label("Bảng 1 – Kỹ thuật Wazuh gán cho hành vi LOTL (trên toàn bộ dữ liệu đã thu) và kỹ thuật VT-Guard gán"),
  ...Tb(["Hành vi thật", "Wazuh gán", "VT-Guard gán"],
    [["Dò cấu hình mạng (T1016)", "T1059.003 – sai", "**T1016**"],
     ["Dò máy trong mạng (T1018)", "T1059.003 / T1082 – sai", "**T1018** (+ luật Sigma)"],
     ["Liệt kê tài khoản miền (T1087.002)", "T1059.003 / T1018 – sai", "**T1087.002**"],
     ["Liệt kê nhật ký (T1654)", "T1059.003 / T1082 – sai", "**T1654** (+ luật Sigma)"],
     ["Trích xuất NTDS (T1003.003)", "T1059.003 – không nhận ra đánh cắp", "**T1003.003**, ưu tiên CAO"]],
    [3.6, 3.4, 3]),
  Label("Bảng 2 – Đối chiếu theo kịch bản chạy trên hạ tầng thật"),
  ...Tb(["KB", "Wazuh: cảnh báo / gán đúng kỹ thuật", "VT-Guard: cảnh báo (ưu tiên cao)", "Độ trễ"],
    [["1 – quản trị", "[[…]]", "[[0]] – im lặng", "—"],
     ["2 – trinh sát LOTL", "[[…]] / [[…]]", "**2 (1)** — 6 233 sự kiện, 56 cửa sổ", "**46 s** (trung vị 30 s)"],
     ["3 – trinh sát chậm", "[[…]]", "[[…]]", "[[…]]"],
     ["4 – trích xuất NTDS", "[[…]]", "[[…]]", "[[…]]"],
     ["5 – biến thể NTDS", "[[…]]", "[[…]]", "[[…]]"]],
    [2.6, 3, 3, 1.8]),
  Shot("Ảnh ghép: Wazuh Discover (trái, luật 92052 → T1059.003) và cảnh báo VT-Guard trong Wazuh (phải) cùng khung giờ (Hình 3.41)"),
  Label("Nội dung tóm tắt"),
  Bul("Trên log thật của hạ tầng: VT-Guard **gán đúng kỹ thuật** mà Wazuh gán nhầm thành “chạy cmd bất thường”."),
  Bul("Cảnh báo xuất hiện sau **khoảng nửa phút**, có luật Sigma + top-5 sự kiện giải thích, hiển thị ngay trong Wazuh Dashboard."),
  Note("Ô tô vàng điền từ báo cáo demo_report.md sau khi chạy đủ 6 kịch bản."),

  Slide("DEMO trực tiếp", "2–3 phút"),
  Label("Hình ảnh"), Line("Slide nền tối chỉ có chữ “DEMO” + địa chỉ `http://10.20.30.10:8501` và `https://10.20.30.10` (Wazuh)."),
  Label("Kịch bản demo trên lớp (theo docs/STEP9-M4-DEMO.md)"),
  Bul("Mở song song Wazuh Dashboard và VT-Guard dashboard."),
  Bul("Chạy KB2 (trinh sát LOTL) bằng bộ điều phối trên WIN10-01 → trong ~30–60 s cảnh báo hiện trên hàng đợi VT-Guard."),
  Bul("Mở **Chi tiết cảnh báo**: điểm AI (YC3) · luật Sigma khớp + xuất xứ (YC1) · nguồn quyết định AI + luật (YC2) · top-5 attention."),
  Bul("Sang Wazuh Discover: luật có sẵn gán T1059.003; cảnh báo VT-Guard có mặt trong `vtguard-alerts-*`."),
  Bul("Phương án dự phòng: nút **phát lại log mẫu** trên dashboard (cùng luồng xử lý, không cần mạng lab)."),
];

const ending = [
  Part("KẾT LUẬN"),
  Slide("Kết luận: đề tài đáp ứng đủ ba yêu cầu", "50 giây"),
  Label("Bảng"),
  ...Tb(["Yêu cầu", "Kết quả đạt được"],
    [["YC1 – Luật tự sinh", "11 luật Sigma hợp lệ, có xuất xứ, **0/88 báo nhầm**, phủ 3 kỹ thuật Wazuh bỏ sót"],
     ["YC2 – Hợp nhất", "F3-B hơn chỉ-luật có ý nghĩa thống kê; ưu tiên CAO **đúng 76/76**; 75% cảnh báo có luật giải thích"],
     ["YC3 – Mô hình chuỗi", "VT-Seq-ens F1 **0,964**, macro-F1 kỹ thuật **0,82** (Wazuh 0,12); hơn GRU thuần sau Holm; attention trung thực"],
     ["Triển khai", "Chạy thật cạnh Wazuh trên VT-SIEM01; cảnh báo ~30 s; **2–3 ms/cửa sổ CPU**; `verify` 7/7"]],
    [2.4, 7.6]),
  Label("Nội dung tóm tắt"),
  Bul("Đóng góp phương pháp: dữ liệu có nhãn chính xác theo cây tiến trình, chống rò rỉ có kiểm chứng; quy trình đánh giá **khoá trước khi chấm, kiểm định thống kê, tái lập bằng một lệnh**."),

  Slide("Hướng phát triển", "30 giây"),
  Label("Hình ảnh"), Line("Lộ trình 3 mũi tên: Mở rộng chuỗi tấn công → Mở rộng hạ tầng → Khép vòng với SIEM."),
  Label("Nội dung tóm tắt"),
  Bul("Mở rộng sang các giai đoạn khác của Volt Typhoon: di chuyển ngang (RDP/WMI), duy trì truy cập, proxy `netsh portproxy`."),
  Bul("Kiểm thử trên dataset công khai và mạng nhiều máy, nhiều miền; vận hành trực tiếp dài ngày."),
  Bul("Chuyển luật Sigma tự sinh thành **luật Wazuh gốc** + active response; học tiếp từ phản hồi của phân tích viên."),

  Slide("Cảm ơn và hỏi đáp", "—"),
  Label("Hình ảnh"), Line("Ảnh chụp dashboard Phần A làm nền mờ; mã QR tới repo GitHub (tuỳ chọn)."),
  Label("Nội dung tóm tắt"),
  Bul("Em xin chân thành cảm ơn thầy cô và các bạn đã lắng nghe!"),
  Bul("Mã nguồn và tái lập: `docker run --network none vtguard:step9 verify`"),
];

const backup = [
  Part("PHỤ LỤC – SLIDE DỰ PHÒNG CHO PHẦN HỎI ĐÁP (chỉ mở khi được hỏi)"),
  Slide("Dự phòng · Vì sao cần VT-Seq khi mô hình đơn giản cũng tốt?"),
  ...Tb(["Mô hình", "F1 T-novel", "macro-F1 kỹ thuật", "F1 T1654", "Khi bỏ tên công cụ"],
    [["B1 TF-IDF", "0,946", "0,73", "0,57", "giữ được"],
     ["B2 LightGBM", "0,936", "0,80", "0,59", "**sụp: 0,45**"],
     ["**VT-Seq-ens**", "**0,964**", "**0,82**", "**0,68**", "**giữ được: 0,83**"]],
    [2.4, 1.6, 2, 1.5, 2.4], [2]),
  Bul("Ở bài toán nhị phân các mô hình đều gần trần; ưu thế của VT-Seq ở **kỹ thuật khó T1654**, **độ bền khi bỏ tên công cụ** và **attention để giải thích** — điều TF-IDF/LightGBM không cung cấp theo chuỗi."),

  Slide("Dự phòng · Dữ liệu mô phỏng có đáng tin không?"),
  Bul("Quản trị hợp lệ dùng **đúng công cụ** của tấn công (164 phiên hard-negative); T-hard chọn theo chữ ký công cụ."),
  Bul("Dấu vết bộ sinh được **đo và trung hoà** (mức tách 0,942 → 0,735); 12 kiểm tra chấp nhận; quét tĩnh chặn trường cấm."),
  Bul("Kiểm thử trên **đợt mới theo thời gian** và **biến thể NTDS chưa từng thấy**; xác nhận thêm bằng thực nghiệm trực tiếp trên hạ tầng."),

  Slide("Dự phòng · Wazuh viết thêm luật là bắt được?"),
  Bul("Đúng — và đó chính là việc VT-Guard **tự động hoá**: sinh luật Sigma từ dữ liệu, có kiểm định chất lượng và xuất xứ, thay vì viết tay từng luật."),
  Bul("Luật Sigma xuất ra dùng được cho mọi SIEM (Wazuh, Splunk, Elastic); AI bổ sung phần hành vi mà luật đơn không mô tả được (T1016, T1087.002)."),
];

const doc = new Document({
  creator: "VT-Guard", title: "VT-Guard – dàn ý slide thuyết trình",
  styles: { default: { document: { run: { font: FONT, size: SZ } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true }, paragraph: { outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "dot", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 500, hanging: 280 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 900, hanging: 280 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 2 * CM, bottom: 2 * CM, left: 2 * CM, right: 2 * CM } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 22 })] })] }) },
    children: [...intro, ...opening, ...arch, ...data, ...results, ...product, ...ending, ...backup],
  }],
});

const out = path.join(__dirname, "VT-Guard_DanY_Slide.docx");
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log(`${n} slide -> ${out}`); });
