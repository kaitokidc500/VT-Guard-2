"""VT-Guard dashboard - phan dung chung cho moi trang: chuoi giao dien (ui_vi.json, UTF-8 co dau; code giu ASCII),
giao dien kieu SOC/SIEM (CSS, thanh tieu de, the KPI, huy hieu), bo nho dem du lieu.
Dashboard tach HAI PHAN (thay cho cong tac che do cu):
  Phan A "siem"     - giam sat thoi gian thuc: luong live / replay, KHONG co nhan (nhu SOC that dang truc).
  Phan B "research" - ket qua nghien cuu tren tap test dong bang, CO nhan + chi so tu results JSON.
"""
import html
import json
from pathlib import Path

import streamlit as st

import data as D

_STR = json.load(open(Path(__file__).with_name("ui_vi.json"), encoding="utf-8"))

def T(key, **kw):
    s = _STR.get(key, key)
    return s.format(**kw) if kw else s

# ---------------- du lieu (dem) ----------------
@st.cache_data(show_spinner=False)
def cached_alerts(): return D.all_alerts()

@st.cache_data(show_spinner=False)
def cached_incidents(): return D.incidents(D.all_alerts())

@st.cache_data(show_spinner=False)
def cached_labels(): return D.eval_labels()

@st.cache_data(show_spinner=False)
def cached_scores(): return D.ttp_scores()

@st.cache_data(show_spinner=False)
def cached_checksum(): return D.verify_artefacts()

@st.cache_data(show_spinner=False)
def cached_pipeline(): return D.pipeline_info()

@st.cache_data(show_spinner=False, ttl=2)
def cached_live(): return D.live_alerts()

@st.cache_data(show_spinner=False, ttl=2)
def cached_live_incidents(): return D.live_incidents(D.live_alerts())

@st.cache_data(show_spinner=False)
def cached_highlights(): return D.highlights()

# ---------------- mau / nhan ----------------
PRIO_COLOR = {"Cao": "#f05252", "Can xem lai": "#f5a524"}
SRC_COLOR = {"both": "#3d8bfd", "ai": "#f5a524", "rule": "#a78bfa"}
TTP_COLOR = {"T1016": "#3d8bfd", "T1018": "#2dd4bf", "T1087.002": "#a78bfa", "T1654": "#f5a524", "T1003.003": "#f05252"}

def split_name(s): return T(f"split_{s}")

def short_split(s): return T(f"short_{s}")

def src_name(s): return T(f"src_{s}")

def prio_name(p): return T(f"prio_{p}")

def tactic_name(t): return T(f"tac_{t}")

def esc(s): return html.escape(str(s))

def badge(text, tone="gray"): return f'<span class="vtg-badge {tone}">{esc(text)}</span>'

def prio_badge(p): return badge(prio_name(p), "red" if p == "Cao" else "amber")

def src_badge(s): return badge(src_name(s), "blue" if s == "both" else "amber")

def res_md(r):
    """Huy hieu Dung / Nham cho st.markdown (khong dung trong bang: o bang dung styled())."""
    return f":{'green' if r == 'Dung' else 'red'}-badge[{T('res_' + r)}]"

CELL_TONE = {"red": "background-color: rgba(240,82,82,.16); color: #fca5a5; font-weight: 600",
             "amber": "background-color: rgba(245,165,36,.14); color: #fcd34d; font-weight: 600",
             "green": "background-color: rgba(34,197,94,.14); color: #86efac; font-weight: 600",
             "gray": "color: #8b98ae"}

def tone_prio(): return {prio_name("Cao"): "red", prio_name("Can xem lai"): "amber"}

def tone_res(): return {T("res_Dung"): "green", T("res_Nham"): "red"}

def styled(df, tones):
    """To mau o bang theo gia tri hien thi (kieu huy hieu SIEM). tones: {cot: {gia tri: tone}}. Chi them CSS, khong doi gia tri
    -> column_config (ProgressColumn, NumberColumn...) van ap dung."""
    sty = df.style
    for col, m in tones.items():
        if col in df.columns:
            sty = sty.map(lambda v, m=m: CELL_TONE.get(m.get(v, ""), ""), subset=[col])
    return sty

def ttp_chips(ttps):
    return "".join(f'<span class="vtg-chip" style="border-color:{TTP_COLOR[k]}66;color:{TTP_COLOR[k]}" title="{esc(D.MITRE[k][1])}">{k}</span>'
                   for k in ttps) or '<span class="vtg-muted">-</span>'

def ts(s, n=19):
    """Thoi gian hien thi (UTC): '2026-10-14T04:33:25.678Z' -> '2026-10-14 04:33:25'."""
    return s[:n].replace("T", " ")

# ---------------- CSS ----------------
CSS = """
<style>
:root{--vtg-bg:#0b1120;--vtg-panel:#131c2e;--vtg-panel2:#172238;--vtg-border:#24314a;--vtg-text:#d8e0ee;--vtg-muted:#8b98ae;
 --vtg-blue:#3d8bfd;--vtg-red:#f05252;--vtg-amber:#f5a524;--vtg-green:#22c55e;--vtg-violet:#a78bfa;--vtg-teal:#2dd4bf}
[data-testid="stMainBlockContainer"]{padding-top:1.1rem;padding-bottom:2.5rem;max-width:100%}
[data-testid="stHeader"]{background:transparent}
[data-testid="stDecoration"]{display:none}
[data-testid="stElementToolbar"]{display:none}
.vega-embed details{display:none}
[data-testid="stSidebarHeader"]{padding-bottom:0}
h1,h2,h3{letter-spacing:-.01em}
.vtg-muted{color:var(--vtg-muted)}
.vtg-top{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:12px 18px;border:1px solid var(--vtg-border);border-radius:8px;
 background:linear-gradient(90deg,#121b2f 0%,#0f1729 100%);border-left:4px solid var(--vtg-green)}
.vtg-top.vtg-research{border-left-color:var(--vtg-amber)}
.vtg-top .crumb{color:var(--vtg-muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.1em}
.vtg-top .title{font-size:1.32rem;font-weight:700;color:#f3f6fb;line-height:1.25}
.vtg-top .tb{flex:1 1 480px;min-width:0}
.vtg-top .sub{color:var(--vtg-muted);font-size:.8rem;margin-top:2px}
.vtg-pills{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;flex:0 1 auto}
.vtg-pill{font-size:.7rem;padding:3px 10px;border-radius:999px;border:1px solid var(--vtg-border);color:#b7c2d6;background:#0e1626;white-space:nowrap}
.vtg-pill b{color:#e6ecf5;font-weight:600}
.vtg-pill.ok{color:#86efac;border-color:#1f5135}
.vtg-pill.bad{color:#fca5a5;border-color:#7a2424}
.vtg-pill.mode{font-weight:800;letter-spacing:.06em;color:#08101e}
.vtg-pill.mode.siem{background:var(--vtg-green);border-color:var(--vtg-green)}
.vtg-pill.mode.research{background:var(--vtg-amber);border-color:var(--vtg-amber)}
.vtg-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:currentColor;margin-right:6px;vertical-align:1px}
.vtg-strip{margin:8px 0 16px;padding:7px 14px;border-radius:6px;font-size:.8rem}
.vtg-strip.siem,.vtg-strip.ops{background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.30);color:#bbf7d0}
.vtg-strip.research,.vtg-strip.eval{background:rgba(245,165,36,.09);border:1px solid rgba(245,165,36,.42);color:#fde68a}
.vtg-kpis{display:grid;grid-template-columns:repeat(var(--n,5),minmax(0,1fr));gap:12px;margin:2px 0 16px}
@media (max-width:1100px){.vtg-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:640px){.vtg-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
.vtg-kpi{background:var(--vtg-panel);border:1px solid var(--vtg-border);border-radius:8px;padding:12px 15px 11px;border-top:3px solid var(--vtg-blue)}
.vtg-kpi.red{border-top-color:var(--vtg-red)}.vtg-kpi.amber{border-top-color:var(--vtg-amber)}.vtg-kpi.green{border-top-color:var(--vtg-green)}
.vtg-kpi.violet{border-top-color:var(--vtg-violet)}.vtg-kpi.teal{border-top-color:var(--vtg-teal)}.vtg-kpi.gray{border-top-color:#64748b}
.vtg-kpi .l{font-size:.68rem;color:var(--vtg-muted);text-transform:uppercase;letter-spacing:.08em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vtg-kpi .v{font-size:1.85rem;font-weight:700;color:#f3f6fb;line-height:1.15;margin-top:5px;font-variant-numeric:tabular-nums}
.vtg-kpi .v small{font-size:.9rem;color:var(--vtg-muted);font-weight:500;margin-left:4px}
.vtg-kpi .s{font-size:.72rem;color:var(--vtg-muted);margin-top:2px}
.vtg-ptitle{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:.74rem;font-weight:700;text-transform:uppercase;
 letter-spacing:.09em;color:#c6d0e2;margin:0 0 8px}
.vtg-ptitle span{font-weight:400;text-transform:none;letter-spacing:0;color:var(--vtg-muted);font-size:.75rem}
.vtg-badge{display:inline-block;padding:1px 8px;border-radius:4px;font-size:.72rem;font-weight:700;letter-spacing:.02em;white-space:nowrap}
.vtg-badge.red{background:rgba(240,82,82,.14);color:#fca5a5;border:1px solid rgba(240,82,82,.45)}
.vtg-badge.amber{background:rgba(245,165,36,.13);color:#fcd34d;border:1px solid rgba(245,165,36,.45)}
.vtg-badge.blue{background:rgba(61,139,253,.14);color:#93c5fd;border:1px solid rgba(61,139,253,.45)}
.vtg-badge.green{background:rgba(34,197,94,.13);color:#86efac;border:1px solid rgba(34,197,94,.45)}
.vtg-badge.violet{background:rgba(167,139,250,.14);color:#c4b5fd;border:1px solid rgba(167,139,250,.45)}
.vtg-badge.gray{background:rgba(148,163,184,.12);color:#cbd5e1;border:1px solid rgba(148,163,184,.35)}
.vtg-chip{display:inline-block;padding:1px 7px;margin:1px 4px 1px 0;border:1px solid;border-radius:999px;font-size:.72rem;font-weight:600;
 font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:nowrap}
.vtg-card{background:var(--vtg-panel);border:1px solid var(--vtg-border);border-radius:8px;padding:14px 16px;margin-bottom:12px}
.vtg-card .head{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:8px}
.vtg-card .code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:1.05rem;font-weight:700;color:#f3f6fb}
.vtg-kv{display:grid;grid-template-columns:max-content 1fr;gap:5px 16px;font-size:.84rem}
.vtg-kv .k{color:var(--vtg-muted)}
.vtg-kv .v{color:var(--vtg-text);word-break:break-all}
.vtg-mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.8rem}
.vtg-chain{display:flex;align-items:stretch;flex-wrap:wrap;gap:6px 0;margin:4px 0 10px}
.vtg-step{background:var(--vtg-panel2);border:1px solid var(--vtg-border);border-radius:6px;padding:7px 11px;min-width:150px;border-top:3px solid}
.vtg-step .tac{font-size:.62rem;color:var(--vtg-muted);text-transform:uppercase;letter-spacing:.08em}
.vtg-step .tid{font-weight:700;color:#f3f6fb;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.86rem}
.vtg-step .tn{font-size:.72rem;color:#c6d0e2}
.vtg-arrow{align-self:center;color:#5b6b86;padding:0 7px;font-size:1rem}
.vtg-matrix{display:grid;grid-template-columns:3fr 1fr;gap:10px}
.vtg-tac{background:var(--vtg-panel2);border:1px solid var(--vtg-border);border-radius:6px;padding:8px}
.vtg-tac .th{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#c6d0e2;margin-bottom:6px}
.vtg-tac .th span{color:var(--vtg-muted);font-weight:400}
.vtg-tcells{display:grid;grid-template-columns:repeat(auto-fit,minmax(105px,1fr));gap:6px}
.vtg-tcell{border-radius:5px;padding:7px 9px;border:1px solid var(--vtg-border)}
.vtg-tcell .id{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-weight:700;font-size:.8rem;color:#f3f6fb}
.vtg-tcell .nm{font-size:.7rem;color:#c6d0e2;min-height:2.1em}
.vtg-tcell .ct{font-size:.7rem;color:var(--vtg-muted);margin-top:3px}
.vtg-tcell .ct b{color:#f3f6fb;font-size:.9rem}
.vtg-health{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px}
.vtg-hitem{display:flex;gap:10px;align-items:flex-start;background:var(--vtg-panel2);border:1px solid var(--vtg-border);border-radius:6px;padding:8px 10px}
.vtg-hitem .st{width:9px;height:9px;border-radius:50%;margin-top:5px;flex:none;background:var(--vtg-green);box-shadow:0 0 0 3px rgba(34,197,94,.15)}
.vtg-hitem .st.bad{background:var(--vtg-red);box-shadow:0 0 0 3px rgba(240,82,82,.15)}
.vtg-hitem .n{font-size:.78rem;font-weight:600;color:#e6ecf5}
.vtg-hitem .d{font-size:.72rem;color:var(--vtg-muted)}
.vtg-lock{text-align:center;padding:42px 20px;border:1px dashed #3a4a68;border-radius:10px;background:rgba(19,28,46,.6)}
.vtg-lock .t{font-size:1.1rem;font-weight:700;color:#f3f6fb;margin-bottom:6px}
.vtg-lock .d{color:var(--vtg-muted);font-size:.85rem;max-width:620px;margin:0 auto}
.vtg-brand{display:flex;gap:10px;align-items:center;padding:2px 0 10px}
.vtg-brand .logo{width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;
 background:linear-gradient(135deg,#3d8bfd,#2dd4bf);color:#08101e;font-weight:900;font-size:.95rem}
.vtg-brand .nm{font-weight:800;color:#f3f6fb;font-size:1.02rem;line-height:1.1}
.vtg-brand .tg{font-size:.68rem;color:var(--vtg-muted);letter-spacing:.04em}
.vtg-side{font-size:.74rem;color:var(--vtg-muted);line-height:1.55}
.vtg-side b{color:#cbd5e1;font-weight:600}
.vtg-note{font-size:.76rem;color:var(--vtg-muted);margin-top:4px}
.vtg-reqs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:2px 0 16px}
@media (max-width:1100px){.vtg-reqs{grid-template-columns:1fr}}
.vtg-req{background:var(--vtg-panel);border:1px solid var(--vtg-border);border-radius:8px;padding:14px 16px;border-top:3px solid var(--vtg-amber)}
.vtg-req .h{font-size:.74rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#fde68a}
.vtg-req .big{font-size:2rem;font-weight:800;color:#f3f6fb;line-height:1.15;margin:6px 0 4px;font-variant-numeric:tabular-nums}
.vtg-req ul{margin:4px 0 0 0;padding-left:18px}
.vtg-req li{font-size:.8rem;color:#c6d0e2;margin:3px 0}
.vtg-req .see{font-size:.72rem;color:var(--vtg-muted);margin-top:8px}
.vtg-agents{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;margin-bottom:8px}
.vtg-infra{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:.74rem;color:#c6d0e2;margin:0 0 8px}
.vtg-infra .n{background:var(--vtg-panel2);border:1px solid var(--vtg-border);border-radius:5px;padding:3px 8px}
.vtg-infra .n.on{border-color:#1f5135;color:#86efac}
</style>
"""

def inject_css(): st.html(CSS)

# ---------------- phan + thanh tieu de ----------------
def header(part, title, sub=""):
    """Thanh tieu de kieu SOC. part: 'siem' (Phan A, thoi gian thuc, khong nhan) hoac 'research' (Phan B, ket qua nghien cuu).
    Pill: phan, nguon du lieu (luong / dataset), cau hinh khoa, checksum artefact; dai bao duoi thanh ghi ro dang o phan nao."""
    assert part in ("siem", "research")
    cs = cached_checksum(); n_ok = sum(v is True for v in cs.values()); ok = n_ok == len(cs); pi = cached_pipeline()
    if part == "siem":
        stt = D.live_status() or {}; mode = stt.get("mode")
        src = f'<span class="vtg-pill">{esc(T("pill_stream"))} <b>{esc(T("lv_mode_" + (mode or "none")))}</b></span>'
    else:
        src = f'<span class="vtg-pill">{esc(T("pill_source"))} <b>dataset-{esc(pi["dataset"])}</b></span>'
    pills = [f'<span class="vtg-pill mode {part}"><span class="vtg-dot"></span>{esc(T("pill_" + part))}</span>', src,
             f'<span class="vtg-pill">{esc(T("pill_pipeline"))} <b>{esc(pi["strategy"])}-{esc(pi["variant"])} \u00b7 {esc(pi["lock_commit"])}</b></span>',
             f'<span class="vtg-pill {"ok" if ok else "bad"}">{esc(T("pill_checksum"))} <b>{n_ok}/{len(cs)}</b></span>']
    st.markdown(f'<div class="vtg-top vtg-{part}"><div class="tb"><div class="crumb">{esc(T("crumb_" + part))}</div>'
                f'<div class="title">{esc(title)}</div>' + (f'<div class="sub">{esc(sub)}</div>' if sub else "") +
                f'</div><div class="vtg-pills">{"".join(pills)}</div></div>'
                f'<div class="vtg-strip {part}">{esc(T("banner_" + part))}</div>', unsafe_allow_html=True)
    return part == "research"

def kpis(items):
    """items: [(nhan, gia tri, chu thich, tone)]; gia tri co the kem don vi nho: ('76', '/ 101')."""
    cells = []
    for lab, val, sub, tone in items:
        v = f"{esc(val[0])}<small>{esc(val[1])}</small>" if isinstance(val, tuple) else esc(val)
        cells.append(f'<div class="vtg-kpi {tone}"><div class="l" title="{esc(lab)}">{esc(lab)}</div><div class="v">{v}</div>'
                     f'<div class="s">{esc(sub)}</div></div>')
    st.markdown(f'<div class="vtg-kpis" style="--n:{len(cells)}">{"".join(cells)}</div>', unsafe_allow_html=True)

def ptitle(text, hint=""):
    st.markdown(f'<div class="vtg-ptitle">{esc(text)}<span>{esc(hint)}</span></div>', unsafe_allow_html=True)

def note(text): st.markdown(f'<div class="vtg-note">{esc(text)}</div>', unsafe_allow_html=True)

def kv(pairs):
    """Bang khoa-gia tri; gia tri da la HTML (goi esc() truoc neu la van ban)."""
    return '<div class="vtg-kv">' + "".join(f'<div class="k">{esc(k)}</div><div class="v">{v}</div>' for k, v in pairs) + "</div>"

def chain_html(chain):
    """Chuoi TTP theo thoi gian kieu kill chain: moi buoc = chien thuat + ma + ten ky thuat MITRE."""
    steps = []
    for k in chain:
        tac, name = D.MITRE[k]
        steps.append(f'<div class="vtg-step" style="border-top-color:{TTP_COLOR[k]}"><div class="tac">{esc(tactic_name(tac))} \u00b7 {tac}</div>'
                     f'<div class="tid">{k}</div><div class="tn">{esc(name)}</div></div>')
    return '<div class="vtg-chain">' + '<div class="vtg-arrow">&#8250;</div>'.join(steps) + "</div>"

def goto_alert(code):
    """Mo trang Chi tiet: LIVE-xxxx = canh bao luong truc tiep (Phan A), VTG-xxxx = canh bao tap kiem thu (Phan B)."""
    st.session_state["detail_src"] = "live" if code.startswith("LIVE-") else "test"
    st.session_state["goto_alert"] = code
    st.switch_page("pages/detail.py")

def goto_incident(code):
    st.session_state["goto_incident"] = code
    st.switch_page("pages/timeline.py")

def mitre_html(counts, inc_counts=None, stacked=False):
    """Ma tran MITRE ATT&CK gon: moi o = ky thuat, mau dam theo so canh bao."""
    mx = max(counts.values()) or 1; cols = []
    for tac in ("TA0007", "TA0006"):
        cells = []
        for k in [k for k in D.TTPS if D.MITRE[k][0] == tac]:
            a = counts.get(k, 0); alpha = 0.08 + 0.57 * a / mx
            extra = f' \u00b7 <b>{inc_counts.get(k, 0)}</b> {esc(T("ov_mitre_inc"))}' if inc_counts is not None else ""
            cells.append(f'<div class="vtg-tcell" style="background:rgba(240,82,82,{alpha:.2f})"><div class="id">{k}</div>'
                         f'<div class="nm">{esc(T("ttp_vi_" + k))}</div><div class="ct"><b>{a}</b> {esc(T("ov_mitre_alerts"))}{extra}</div></div>')
        cols.append(f'<div class="vtg-tac"><div class="th">{esc(tactic_name(tac))} <span>{tac}</span></div><div class="vtg-tcells">{"".join(cells)}</div></div>')
    sty = ' style="grid-template-columns:1fr"' if stacked else ""
    return f'<div class="vtg-matrix"{sty}>{"".join(cols)}</div>'
