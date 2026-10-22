// VT-Guard Buoc 10 - dung bao cao Word. Chay: node report/build.js  -> report/VT-Guard_BaoCao.docx
const fs = require("fs");
const path = require("path");
const { D, FONT, SZ, LINE, CM, P, B, H1, Tbl, PB, Center, setChapter, runs } = require("./lib");
const { Document, Packer, Paragraph, TextRun, AlignmentType, Footer, PageNumber, TableOfContents, LevelFormat, HeadingLevel } = D;

const cover = [
  Center("BỘ GIÁO DỤC VÀ ĐÀO TẠO", 28, true, 0),
  Center("[TÊN TRƯỜNG / HỌC VIỆN]", 28, true, 0),
  Center("[KHOA AN TOÀN THÔNG TIN]", 28, true, 600),
  Center("BÁO CÁO ĐỀ TÀI", 32, true, 120),
  Center("MÔN HỌC: GIÁM SÁT AN NINH MẠNG", 28, true, 700),
  Center("VT-GUARD: PHÁT HIỆN TẤN CÔNG APT KIỂU VOLT TYPHOON", 34, true, 60),
  Center("KẾT HỢP MÔ HÌNH CHUỖI GRU-ATTENTION VÀ LUẬT TỰ SINH", 34, true, 60),
  Center("TRÊN NỀN TẢNG SIEM WAZUH", 34, true, 1100),
  new Paragraph({ indent: { left: 5 * CM }, spacing: { line: LINE }, children: runs("**Giảng viên hướng dẫn:** [Họ và tên]") }),
  new Paragraph({ indent: { left: 5 * CM }, spacing: { line: LINE }, children: runs("**Sinh viên thực hiện:** [Họ và tên]") }),
  new Paragraph({ indent: { left: 5 * CM }, spacing: { line: LINE }, children: runs("**Mã sinh viên:** [MSSV]") }),
  new Paragraph({ indent: { left: 5 * CM }, spacing: { line: LINE, after: 1400 }, children: runs("**Lớp:** [Lớp]") }),
  Center("Hà Nội, tháng 10 năm 2026", 28, false, 0),
];

const abbr = [
  new Paragraph({ alignment: AlignmentType.CENTER, pageBreakBefore: true, spacing: { after: 200, line: LINE },
                  children: [new TextRun({ text: "DANH MỤC TỪ VIẾT TẮT", font: FONT, size: 30, bold: true })] }),
  ...(() => { setChapter(0); return []; })(),
  ...Tbl("Thuật ngữ và từ viết tắt", ["Viết tắt", "Tiếng Anh", "Ý nghĩa"],
    [["APT", "Advanced Persistent Threat", "Tấn công có chủ đích kéo dài"],
     ["ART", "Atomic Red Team", "Thư viện test mô phỏng kỹ thuật ATT&CK"],
     ["ATT&CK", "Adversarial Tactics, Techniques & Common Knowledge", "Khung tri thức hành vi tấn công của MITRE"],
     ["CI", "Confidence Interval", "Khoảng tin cậy"],
     ["EID", "Event ID", "Mã sự kiện Windows/Sysmon"],
     ["FP / FPR", "False Positive (Rate)", "Cảnh báo nhầm (tỉ lệ)"],
     ["GRU", "Gated Recurrent Unit", "Đơn vị hồi quy có cổng"],
     ["IFM", "Install From Media", "Chế độ sao chép CSDL AD của ntdsutil"],
     ["LOTL", "Living off the Land", "Tấn công bằng công cụ sẵn có của hệ thống"],
     ["NTDS", "NT Directory Services", "CSDL Active Directory (NTDS.dit)"],
     ["OOF", "Out-of-fold", "Dự đoán ngoài fold trong kiểm định chéo"],
     ["ONNX", "Open Neural Network Exchange", "Định dạng mô hình trung lập"],
     ["PR-AUC", "Precision–Recall Area Under Curve", "Diện tích dưới đường Precision–Recall"],
     ["SIEM", "Security Information and Event Management", "Quản lý thông tin và sự kiện an ninh"],
     ["SOC", "Security Operations Center", "Trung tâm giám sát an ninh"],
     ["TTP", "Tactics, Techniques and Procedures", "Chiến thuật, kỹ thuật và thủ tục tấn công"]],
    [1.6, 4.4, 4], { leftCols: [1, 2] }),
];

const toc = [
  new Paragraph({ alignment: AlignmentType.CENTER, pageBreakBefore: true, spacing: { after: 200, line: LINE },
                  children: [new TextRun({ text: "MỤC LỤC", font: FONT, size: 30, bold: true })] }),
  new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ spacing: { line: LINE }, children: runs("*(Nếu mục lục hiển thị trống, trong Word bấm chuột phải vào vùng mục lục → Update Field → Update entire table.)*") }),
];

const conclusion = () => [
  H1("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN"),
  new Paragraph({ spacing: { before: 120, after: 80, line: LINE }, children: runs("**1. Kết quả đạt được**") }),
  P("Đề tài đã xây dựng hoàn chỉnh **VT-Guard** — một lớp phân tích gắn thêm vào SIEM Wazuh để phát hiện chuỗi hành vi “living off the land” kiểu Volt Typhoon, từ hạ tầng lab, dữ liệu, mô hình, luật đến sản phẩm vận hành. Những đóng góp chính gồm:"),
  B("**Bộ dữ liệu bảo mật có nhãn chính xác** (479 phiên, 62 917 sự kiện, 809 cửa sổ) với quy trình gán nhãn theo cây tiến trình, chống rò rỉ nhãn và trung hoà dấu vết bộ sinh dữ liệu được kiểm chứng định lượng, đóng băng với 12 kiểm tra chấp nhận."),
  B("**Mô hình chuỗi tuỳ biến VT-Seq** (GRU + attention, đa nhiệm, ensemble 5 seed): F1 0,964 trên dữ liệu mới, macro-F1 theo kỹ thuật 0,82 so với 0,12 của luật Wazuh; vượt GRU thuần có ý nghĩa thống kê sau hiệu chỉnh Holm; attention được kiểm chứng trung thực."),
  B("**Bộ sinh luật tự động** cho 11 luật Sigma hợp lệ có xuất xứ đầy đủ, 0 cảnh báo nhầm trên hoạt động quản trị hợp lệ, phủ 3 kỹ thuật mà luật Wazuh bỏ sót."),
  B("**Bộ hợp nhất F3-B** phân mức tin cậy cảnh báo: nhóm có cả AI và luật xác nhận đúng 76/76; giảm cảnh báo nhầm trên quản trị hợp lệ từ 17/88 (Wazuh) xuống 1/88."),
  B("**Sản phẩm triển khai được trên hạ tầng thật:** chạy liên tục cạnh Wazuh trên máy chủ VT-SIEM01 (cổng 8501), đọc log trực tiếp qua tài khoản quyền tối thiểu, tự phục hồi khi gián đoạn, ghi cảnh báo ngược vào Wazuh Dashboard; suy luận 2–3 ms/cửa sổ trên CPU; image Docker offline với lệnh verify tái lập 7/7 số liệu báo cáo."),
  P("Về phương pháp, đề tài cho thấy một quy trình nghiên cứu phát hiện xâm nhập **có thể kiểm chứng**: mọi lựa chọn chỉ dựa trên tập huấn luyện, cấu hình được khoá bằng commit trước khi chấm, mọi tuyên bố “tốt hơn” đều qua kiểm định thống kê, và mọi con số trong báo cáo có thể chạy lại bằng một lệnh."),
  new Paragraph({ spacing: { before: 120, after: 80, line: LINE }, children: runs("**2. Hướng phát triển**") }),
  B("Mở rộng sang các giai đoạn khác của chuỗi tấn công Volt Typhoon: di chuyển ngang (RDP/WMI với tài khoản hợp lệ), duy trì truy cập và proxy `netsh portproxy`."),
  B("Mở rộng hạ tầng thử nghiệm: nhiều máy, nhiều miền, dữ liệu nền từ người dùng thực để đánh giá tỉ lệ cảnh báo nhầm ở quy mô vận hành."),
  B("Vận hành trực tiếp dài ngày trên Wazuh, học tiếp từ phản hồi của phân tích viên; chuyển luật Sigma tự sinh thành luật Wazuh gốc."),
];

const refs = () => [
  H1("TÀI LIỆU THAM KHẢO"),
  ...[
    "[1] CISA, NSA, FBI và đối tác (2023), *People’s Republic of China State-Sponsored Cyber Actor Living off the Land to Evade Detection*, Cybersecurity Advisory AA23-144A.",
    "[2] CISA, NSA, FBI và đối tác (2024), *PRC State-Sponsored Actors Compromise and Maintain Persistent Access to U.S. Critical Infrastructure*, Cybersecurity Advisory AA24-038A.",
    "[3] Microsoft Threat Intelligence (2023), *Volt Typhoon targets US critical infrastructure with living-off-the-land techniques*, Microsoft Security Blog.",
    "[4] B. E. Strom và cộng sự (2018), *MITRE ATT&CK: Design and Philosophy*, The MITRE Corporation.",
    "[5] Red Canary, *Atomic Red Team* – thư viện test mô phỏng kỹ thuật ATT&CK, github.com/redcanaryco/atomic-red-team.",
    "[6] Wazuh Inc., *Wazuh Documentation 4.x* – kiến trúc, archives, Indexer API, documentation.wazuh.com.",
    "[7] Microsoft Sysinternals, *Sysmon (System Monitor)* – tài liệu sự kiện.",
    "[8] SigmaHQ, *Sigma – Generic Signature Format for SIEM Systems* và thư viện pySigma, github.com/SigmaHQ.",
    "[9] W. W. Cohen (1995), “Fast Effective Rule Induction”, *Proceedings of the 12th International Conference on Machine Learning (ICML)*, tr. 115–123.",
    "[10] K. Cho và cộng sự (2014), “Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation”, *EMNLP 2014*.",
    "[11] D. Bahdanau, K. Cho, Y. Bengio (2015), “Neural Machine Translation by Jointly Learning to Align and Translate”, *ICLR 2015*.",
    "[12] M. Du, F. Li, G. Zheng, V. Srikumar (2017), “DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning”, *ACM CCS 2017*.",
    "[13] S. Jain, B. C. Wallace (2019), “Attention is not Explanation”, *NAACL-HLT 2019*.",
    "[14] G. Ke và cộng sự (2017), “LightGBM: A Highly Efficient Gradient Boosting Decision Tree”, *NeurIPS 2017*.",
    "[15] S. Holm (1979), “A Simple Sequentially Rejective Multiple Test Procedure”, *Scandinavian Journal of Statistics*, 6(2), tr. 65–70.",
    "[16] B. Efron, R. J. Tibshirani (1993), *An Introduction to the Bootstrap*, Chapman & Hall.",
  ].map(t => new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { left: 700, hanging: 700 }, spacing: { line: 336, after: 40 }, children: runs(t) })),
];

const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 26 })] })] });

const margins = { top: 2 * CM, bottom: 2 * CM, left: 3 * CM, right: 2 * CM };
const page = { size: { width: 11906, height: 16838 }, margin: margins };

const doc = new Document({
  creator: "VT-Guard", title: "VT-Guard – Báo cáo đề tài", features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: SZ } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 30, bold: true, color: "000000" }, paragraph: { spacing: { before: 0, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: SZ, bold: true, color: "000000" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: SZ, bold: true, italics: true, color: "000000" }, paragraph: { spacing: { before: 140, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "dash", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1000, hanging: 360 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "+", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1440, hanging: 360 } } } }] }] },
  sections: [
    { properties: { page }, children: cover },
    { properties: { page, pageNumbers: { start: 1 } }, footers: { default: footer },
      children: [...abbr, ...toc, ...require("./ch1")(), ...require("./ch2")(), ...require("./ch3")(), ...conclusion(), ...refs()] },
  ],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(__dirname, "VT-Guard_BaoCao.docx"); fs.writeFileSync(out, buf);
  console.log("ghi", out, (buf.length / 1e6).toFixed(1), "MB");
});
