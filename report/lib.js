// VT-Guard Buoc 10 - thu vien dinh dang bao cao Word (docx-js). Times New Roman 14, gian dong 1.5, le trai 3 / phai 2 / tren 2 / duoi 2 cm.
const fs = require("fs");
const path = require("path");
const D = require("docx");
const { Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType, HeadingLevel, ShadingType,
        BorderStyle, LevelFormat, PageBreak, VerticalAlign, HeightRule } = D;

const FONT = "Times New Roman";
const SZ = 28;                 // 14 pt (half-points)
const SZ_TBL = 24;             // 12 pt trong bang
const SZ_CAP = 26;             // 13 pt chu thich
const LINE = 360;              // 1.5 dong
const CM = 567;                // 1 cm = 567 DXA
const TEXT_W = 16 * CM;        // A4 21 cm - 3 - 2
const FIG_DIR = path.join(__dirname, "figures");
const SHOT_DIR = path.join(__dirname, "..", "reports", "step9", "screenshots");

let chap = 0, figN = 0, tblN = 0;
function setChapter(n) { chap = n; figN = 0; tblN = 0; }

// **dam**, *nghieng*, `ma` -> TextRun
function runs(text, base = {}) {
  const out = []; const re = /(\[\[[^\]]+\]\]|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, size: SZ, ...base }));
    const t = m[0];
    if (t.startsWith("[[")) out.push(new TextRun({ text: t.slice(2, -2), font: FONT, size: SZ, ...base, highlight: "yellow" }));
    else if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, size: SZ, ...base }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: t.slice(1, -1), font: "Consolas", size: (base.size || SZ) - 4, ...base, ...{ size: (base.size || SZ) - 4 } }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, size: SZ, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, size: SZ, ...base }));
  return out;
}

const P = (text, o = {}) => new Paragraph({ children: runs(text), alignment: AlignmentType.JUSTIFIED,
  indent: { firstLine: o.noIndent ? 0 : CM }, spacing: { line: LINE, after: 80 } });

// a) b) c): muc nho nhat - dau muc dam nghieng + noi dung cung doan
const A = (lead, text) => new Paragraph({ children: [new TextRun({ text: lead + " ", bold: true, italics: true, font: FONT, size: SZ }), ...runs(text)],
  alignment: AlignmentType.JUSTIFIED, indent: { firstLine: CM }, spacing: { line: LINE, after: 80 } });

const B = (text, level = 0) => new Paragraph({ children: runs(text), numbering: { reference: "dash", level }, alignment: AlignmentType.JUSTIFIED,
  spacing: { line: LINE, after: 40 } });

const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text, font: FONT, size: 30, bold: true })], spacing: { before: 0, after: 240, line: LINE } });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: FONT, size: SZ, bold: true })],
  spacing: { before: 200, after: 100, line: LINE }, keepNext: true });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, font: FONT, size: SZ, bold: true, italics: true })],
  spacing: { before: 140, after: 80, line: LINE }, keepNext: true });

function pngSize(file) {
  const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

// Hinh: anh can giua + chu thich "Hinh c.n. ..." ben duoi
function Fig(file, caption, widthCm = 16) {
  const f = fs.existsSync(path.join(FIG_DIR, file)) ? path.join(FIG_DIR, file) : path.join(SHOT_DIR, file);
  const { w, h, data } = pngSize(f);
  const wpx = Math.round(widthCm / 2.54 * 96), hpx = Math.round(wpx * h / w);
  figN += 1;
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
            children: [new ImageRun({ type: "png", data, transformation: { width: wpx, height: hpx },
                                      altText: { title: caption, description: caption, name: file } })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160, line: 300 },
            children: [new TextRun({ text: `Hình ${chap}.${figN}. `, bold: true, italics: true, font: FONT, size: SZ_CAP }),
                       new TextRun({ text: caption, italics: true, font: FONT, size: SZ_CAP })] })];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "7F8C8D" };
const borders = { top: border, bottom: border, left: border, right: border };

function cellPara(text, bold, align) {
  return new Paragraph({ alignment: align, spacing: { line: 276, before: 20, after: 20 },
    children: runs(String(text), { size: SZ_TBL, ...(bold ? { bold: true } : {}) }).map(r => r) });
}

// Bang: chu thich "Bang c.n. ..." o tren; widths theo ty le (tong bat ky) -> DXA
function Tbl(caption, header, rows, ratio, o = {}) {
  tblN += 1;
  const total = ratio.reduce((a, b) => a + b, 0);
  const cw = ratio.map(r => Math.floor(TEXT_W * r / total)); cw[cw.length - 1] += TEXT_W - cw.reduce((a, b) => a + b, 0);
  const mk = (cells, head, hl) => new TableRow({ tableHeader: head, cantSplit: true, children: cells.map((c, i) => new TableCell({
    borders, width: { size: cw[i], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: head ? { fill: "D6EAF8", type: ShadingType.CLEAR, color: "auto" } : (hl ? { fill: "E9F7EF", type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [cellPara(c, head || hl, (i === 0 || (o.leftCols || []).includes(i)) ? AlignmentType.LEFT : AlignmentType.CENTER)] })) });
  const hlRows = o.highlight || [];
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 60, line: 300 },
            children: [new TextRun({ text: `Bảng ${chap}.${tblN}. `, bold: true, font: FONT, size: SZ_CAP }),
                       new TextRun({ text: caption, font: FONT, size: SZ_CAP })] }),
          new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: cw,
            rows: [mk(header, true, false), ...rows.map((r, i) => mk(r, false, hlRows.includes(i)))] }),
          ...(o.note ? [new Paragraph({ spacing: { before: 40, after: 160, line: 276 }, alignment: AlignmentType.JUSTIFIED,
                         children: runs(o.note, { size: 22, italics: true }) })] : [new Paragraph({ spacing: { after: 100 }, children: [] })])];
}


// Khung anh trong (nguoi dung dan anh thuc nghiem vao sau): o vien dut + chu thich "Hinh c.n. ..." danh so cung day voi Fig
const dash = { style: BorderStyle.DASHED, size: 8, color: "95A5A6" };
function FigSlot(caption, heightCm = 7, hint = "") {
  figN += 1;
  const w = TEXT_W - CM;
  return [new Table({ width: { size: w, type: WidthType.DXA }, columnWidths: [w], alignment: AlignmentType.CENTER,
            rows: [new TableRow({ height: { value: Math.round(heightCm * CM), rule: HeightRule.EXACT }, cantSplit: true, children: [new TableCell({
              width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, borders: { top: dash, bottom: dash, left: dash, right: dash },
              shading: { fill: "F8F9F9", type: ShadingType.CLEAR, color: "auto" },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `[Dán ảnh Hình ${chap}.${figN} vào đây]`,
                           italics: true, color: "7F8C8D", font: FONT, size: 24 })] }),
                         ...(hint ? [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: hint, italics: true, color: "95A5A6", font: FONT, size: 22 })] })] : [])] })] })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, keepLines: true, spacing: { before: 60, after: 160, line: 300 },
            children: [new TextRun({ text: `Hình ${chap}.${figN}. `, bold: true, italics: true, font: FONT, size: SZ_CAP }),
                       new TextRun({ text: caption, italics: true, font: FONT, size: SZ_CAP })] })];
}

const PB = () => new Paragraph({ children: [new PageBreak()] });
const Center = (text, size = SZ, bold = false, after = 120) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after, line: LINE },
  children: [new TextRun({ text, font: FONT, size, bold })] });

module.exports = { D, FONT, SZ, LINE, CM, TEXT_W, P, A, B, H1, H2, H3, Fig, FigSlot, Tbl, PB, Center, setChapter, runs };
