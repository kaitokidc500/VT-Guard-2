"""Trang Hang doi canh bao (SOC triage): loc / sap xep theo diem, host, thoi gian, TTP, nguon, tap, tim kiem; cot uu tien
(both = Cao, ai = Can xem lai); chon mot dong -> khung xem nhanh + mo Chi tiet. Xuat CSV danh sach dang loc.
Che do van hanh: khong co cot nhan, khong hien window_id goc. Che do danh gia: them Ket qua (Dung / Nham), TTP that, window_id."""
from datetime import datetime, time, timezone

import pandas as pd
import streamlit as st

import data as D
from common import (T, cached_alerts, cached_labels, esc, goto_alert, header, kpis, kv, prio_badge, prio_name, ptitle, short_split,
                    src_badge, src_name, styled, tone_prio, tone_res, ts, ttp_chips)

ev = header(T("navsec_monitor"), T("q_title"), T("q_intro"))
al = cached_alerts(); by_code = {a["code"]: a for a in al}
rows = D.queue_rows(al, eval_mode=ev, labels=cached_labels() if ev else None)
hosts = sorted({r["host"] for r in rows}); dates = sorted(D._dt(r["bat_dau"]).date() for r in rows)

with st.container(border=True):
    ptitle(T("q_filters"), T("q_filters_h"))
    f0, f1, f2, f3 = st.columns([1.4, 1, 1, 1.2])
    text = f0.text_input(T("q_search"), placeholder=T("q_search_ph"))
    sel_hosts = f1.multiselect(T("q_hosts"), hosts, placeholder=T("q_all"))
    sel_src = f2.multiselect(T("q_sources"), ["both", "ai"], format_func=src_name, placeholder=T("q_all"))
    sel_ttps = f3.multiselect(T("q_ttps"), list(D.TTPS), placeholder=T("q_all"))
    f4, f5, f6, f7 = st.columns([1.4, 1, 1, 1.2])
    min_score = f4.slider(T("q_min_score"), 0.80, 1.10, 0.80, 0.01)
    sel_split = f5.multiselect(T("q_splits"), list(D.SPLITS), format_func=short_split, placeholder=T("q_all"))
    dr = f6.date_input(T("q_dates"), (dates[0], dates[-1]), min_value=dates[0], max_value=dates[-1])
    sort = f7.selectbox(T("q_sort"), list(D.SORTS), format_func=lambda k: T(f"sort_{k}"))

t_from = t_to = None
if isinstance(dr, (list, tuple)) and len(dr) == 2:
    t_from = datetime.combine(dr[0], time.min, tzinfo=timezone.utc); t_to = datetime.combine(dr[1], time.max, tzinfo=timezone.utc)
q = D.sort_queue(D.filter_queue(rows, min_score, sel_hosts, sel_ttps, sel_src, sel_split, t_from, t_to, text.strip() or None), sort)

nh = sum(r["uu_tien"] == "Cao" for r in q)
kp = [(T("q_k_shown"), (str(len(q)), f" / {len(rows)}"), T("q_k_shown_s"), "blue"), (T("ov_m_both"), str(nh), T("ov_m_both_s"), "red"),
      (T("ov_m_ai"), str(len(q) - nh), T("ov_m_ai_s"), "amber"), (T("q_k_hosts"), str(len({r["host"] for r in q})), T("q_k_hosts_s"), "teal")]
if ev: kp.append((T("q_k_fp"), str(sum(r["ket_qua"] == "Nham" for r in q)), T("q_k_fp_s"), "gray"))
kpis(kp)

with st.container(border=True):
    head = st.columns([3, 1])
    with head[0]: ptitle(T("q_table"), T("q_table_h"))
    df = pd.DataFrame(q)
    if len(df):
        out = df.copy()
        out["uu_tien"] = out["uu_tien"].map(prio_name)
        out["nguon"] = out["nguon"].map(src_name)
        out["tap"] = out["tap"].map(short_split)
        if ev: out["ket_qua"] = out["ket_qua"].map(lambda v: T(f"res_{v}"))
        cols = (["ma", "uu_tien", "ket_qua", "diem", "host", "bat_dau", "ttps", "ttp_that", "luat", "nguon", "su_co", "tap", "window_id"] if ev else
                ["ma", "uu_tien", "diem", "host", "bat_dau", "ttps", "luat", "nguon", "su_co", "tap", "cua_so"])
        csv = out[cols].rename(columns={c: T(f"col_{c}") for c in cols}).to_csv(index=False).encode("utf-8-sig")
        head[1].download_button(T("q_export"), csv, file_name="vtguard_alerts.csv", mime="text/csv", icon=":material/download:", width="stretch")
        out["bat_dau"] = out["bat_dau"].map(ts)
        out = out[cols]
        cfg = {c: st.column_config.Column(T(f"col_{c}")) for c in cols}
        cfg |= {"ma": st.column_config.TextColumn(T("col_ma"), pinned=True, width="small"),
                "diem": st.column_config.ProgressColumn(T("col_diem"), min_value=0.8, max_value=1.1, format="%.4f", width="small"),
                "bat_dau": st.column_config.TextColumn(T("col_bat_dau"), width="medium")}
        sel = st.dataframe(styled(out, {"uu_tien": tone_prio(), "ket_qua": tone_res()}), hide_index=True, width="stretch", height=520,
                           column_config=cfg, on_select="rerun", selection_mode="single-row", key="queue_table")
        picked = sel.selection.rows if sel is not None and hasattr(sel, "selection") else []
    else:
        st.info(T("q_empty")); picked = []

if len(df) and picked:
    a = by_code[df.iloc[picked[0]]["ma"]]
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f'<div style="margin-bottom:8px"><span class="vtg-mono" style="font-size:1.05rem;font-weight:700;color:#f3f6fb">{esc(a["code"])}</span> '
                    f'{prio_badge(D.PRIORITY[a["decision_source"]])} {src_badge(a["decision_source"])}</div>', unsafe_allow_html=True)
        c1.markdown(kv([(T("col_host"), esc(a["host"])), (T("d_time"), esc(f"{ts(a['t0'])} \u2192 {ts(a['t1'])} UTC")),
                        (T("col_diem"), esc(f"{a['score']:.4f}  ({T('d_threshold')} {a['threshold']:.4f})")),
                        (T("col_ttps"), ttp_chips(a["ttps"])), (T("col_luat"), esc(", ".join(r["id"] for r in a["rule_ids"]) or "-")),
                        (T("col_su_co"), esc(a["incident"]))]), unsafe_allow_html=True)
        c2.caption(T("q_open_h"))
        if c2.button(T("q_open"), type="primary", width="stretch", icon=":material/open_in_new:"): goto_alert(a["code"])
else:
    st.caption(T("q_pick"))
