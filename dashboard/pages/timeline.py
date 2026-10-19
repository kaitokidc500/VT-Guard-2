"""Phan A - trang Dong thoi gian su co (docs/STEP9-BRIEF.md muc 3.3): gom canh bao cua LUONG TRUC TIEP theo host + khoang nghi
<= 15 phut (LINC-xxx, data.live_incidents), chuoi TTP theo thoi gian kem ma / chien thuat MITRE, ban do thoi gian + Gantt tung su co.
Khong co nhan (Phan A)."""
import altair as alt
import pandas as pd
import streamlit as st

import data as D
from common import (PRIO_COLOR, T, TTP_COLOR, badge, cached_live, cached_live_incidents, chain_html, esc, goto_alert, header,
                    kpis, kv, note, prio_badge, prio_name, ptitle, styled, tone_prio, ts)

header("siem", T("tl_title"), T("tl_intro"))
al = cached_live(); inc = cached_live_incidents()
if not inc:
    st.info(T("tl_empty_live")); st.stop()
rows = D.incident_rows(inc); by_inc = {i["code"]: i for i in inc}

n_ca = sum("TA0006" in i["tactics"] for i in inc)
kp = [(T("tl_k_inc"), str(len(inc)), T("tl_k_inc_s"), "violet"), (T("tl_k_high"), str(sum(i["priority"] == "Cao" for i in inc)), T("tl_k_high_s"), "red"),
      (T("tl_k_ca"), str(n_ca), T("tl_k_ca_s"), "amber"), (T("tl_k_multi"), str(sum(len(i["chain"]) >= 3 for i in inc)), T("tl_k_multi_s"), "blue"),
      (T("tl_k_alerts"), str(sum(i["n"] for i in inc)), T("tl_k_alerts_s"), "teal")]
kpis(kp)

with st.container(border=True):
    ptitle(T("tl_filters"), "")
    f1, f2, f3, f4 = st.columns(4)
    sel_h = f1.multiselect(T("q_hosts"), sorted({i["host"] for i in inc}), placeholder=T("q_all"))
    sel_p = f2.multiselect(T("col_uu_tien"), ["Cao", "Can xem lai"], format_func=prio_name, placeholder=T("q_all"))
    sel_t = f3.multiselect(T("tl_ttp_any"), list(D.TTPS), placeholder=T("q_all"))
    sel_tac = f4.multiselect(T("tl_tactic"), list(D.TACTICS), format_func=lambda t: f"{T('tac_' + t)} ({t})", placeholder=T("q_all"))
keep = [i for i in inc if (not sel_h or i["host"] in sel_h) and (not sel_p or i["priority"] in sel_p)
        and (not sel_t or set(sel_t) & set(i["chain"])) and (not sel_tac or set(sel_tac) & set(i["tactics"]))]
codes = [i["code"] for i in keep]

PRIO_SCALE = alt.Scale(domain=[prio_name("Cao"), prio_name("Can xem lai")], range=[PRIO_COLOR["Cao"], PRIO_COLOR["Can xem lai"]])
with st.container(border=True):
    ptitle(T("tl_global"), T("tl_global_h"))
    g = pd.DataFrame([{"ma": i["code"], "host": i["host"], "start": D._dt(i["start"]).replace(tzinfo=None), "end": D._dt(i["end"]).replace(tzinfo=None),
                       "n": i["n"], "uu_tien": prio_name(i["priority"]), "chuoi": " > ".join(i["chain"]),
                       "chien_thuat": " > ".join(D.TACTICS[t] for t in i["tactics"])} for i in keep])
    if len(g):
        base = alt.Chart(g).encode(y=alt.Y("host:N", title=None), color=alt.Color("uu_tien:N", scale=PRIO_SCALE, legend=alt.Legend(title=None, orient="top")))
        tip = [alt.Tooltip("ma:N", title=T("col_ma")), alt.Tooltip("start:T", title=T("col_bat_dau"), format="%d/%m %H:%M:%S"),
               alt.Tooltip("n:Q", title=T("ov_axis_alerts")), alt.Tooltip("chuoi:N", title=T("tl_chain")), alt.Tooltip("chien_thuat:N", title=T("tl_tactic"))]
        pts = base.mark_circle(opacity=0.85, stroke="#0b1120", strokeWidth=1).encode(
            x=alt.X("start:T", title=None, axis=alt.Axis(format="%d/%m %H:%M", labelAngle=0, tickCount=8)),
            size=alt.Size("n:Q", scale=alt.Scale(range=[60, 600]), legend=None), tooltip=tip)
        st.altair_chart(pts.properties(height=190), width="stretch")
    else:
        st.info(T("tl_empty"))

def _pick():
    s = st.session_state.get("inc_table")
    r = s.selection.rows if s is not None else []
    if r: st.session_state["tl_incident"] = st.session_state["_tl_codes"][r[0]]

with st.container(border=True):
    ptitle(T("tl_list"), T("tl_list_h", n=len(keep), total=len(inc)))
    tab = pd.DataFrame([r for r in rows if r["ma"] in set(codes)])
    st.session_state["_tl_codes"] = list(tab["ma"]) if len(tab) else []
    if len(tab):
        tab["uu_tien"] = tab["uu_tien"].map(prio_name); tab["bat_dau"] = tab["bat_dau"].map(ts); tab["ket_thuc"] = tab["ket_thuc"].map(ts)
        cols = ["ma", "uu_tien", "host", "bat_dau", "thoi_luong_s", "so_canh_bao", "so_cao", "chuoi", "chien_thuat", "luat", "phien"]
        cfg = {c: st.column_config.Column(T(f"tl_col_{c}")) for c in cols}
        cfg |= {"ma": st.column_config.TextColumn(T("tl_col_ma"), pinned=True, width="small"), 
                "thoi_luong_s": st.column_config.NumberColumn(T("tl_col_thoi_luong_s"), format="%.1f s")}
        st.dataframe(styled(tab[cols], {"uu_tien": tone_prio()}), hide_index=True, width="stretch", height=min(330, 36 * (len(tab) + 1) + 4), column_config=cfg, on_select=_pick, selection_mode="single-row", key="inc_table")
    note(T("tl_list_note"))

if not codes: st.stop()
if "goto_incident" in st.session_state:
    st.session_state["tl_incident"] = st.session_state.pop("goto_incident")
if st.session_state.get("tl_incident") not in codes:
    st.session_state["tl_incident"] = codes[0]

def _ilabel(c):
    i = by_inc[c]
    return f"{c} \u00b7 {prio_name(i['priority'])} \u00b7 {i['host']} \u00b7 {ts(i['start'], 16)} \u00b7 {' > '.join(i['chain'])}"

with st.container(border=True):
    ptitle(T("tl_inc"), T("tl_inc_h"))
    c = st.selectbox(T("tl_pick"), codes, format_func=_ilabel, key="tl_incident")
    i = by_inc[c]; ia = sorted([a for a in al if a["incident"] == c], key=lambda a: (D._dt(a["t0"]), a["code"]))
    facts = [(T("col_host"), esc(i["host"])), (T("d_session"), f'<span class="vtg-mono">{esc(i["session"])}</span>'),
             (T("d_time"), esc(f"{ts(i['start'])} \u2192 {ts(i['end'])} UTC ({i['duration_s']:.1f} s)")),
             (T("tl_col_so_canh_bao"), esc(T("tl_n_alerts", n=i["n"], h=i["n_high"]))), (T("col_luat"), esc(", ".join(i["rules"]) or "-"))]
    st.markdown(f'<div class="vtg-card"><div class="head"><span class="code">{esc(c)}</span>{prio_badge(i["priority"])}'
                f'{"".join(badge(D.TACTICS[t], "violet") for t in i["tactics"])}</div>{kv(facts)}</div>', unsafe_allow_html=True)
    ptitle(T("tl_chain"), T("tl_chain_h"))
    st.markdown(chain_html(i["chain"]), unsafe_allow_html=True)

    ptitle(T("tl_gantt"), T("tl_gantt_h"))
    gr = [{"ttp": k, "ma": a["code"], "t0": D._dt(a["t0"]).replace(tzinfo=None), "t1": D._dt(a["t1"]).replace(tzinfo=None),
           "uu_tien": prio_name(D.PRIORITY[a["decision_source"]]), "diem": a["score"]} for a in ia for k in a["ttps"]]
    gdf = pd.DataFrame(gr)
    span = gdf.groupby("ttp").agg(t0=("t0", "min"), t1=("t1", "max"), n=("ma", "count")).reset_index()
    ysort = alt.Y("ttp:N", sort=i["chain"], title=None)
    bars = alt.Chart(span).mark_bar(height=18, opacity=0.35, cornerRadius=3).encode(
        y=ysort, x=alt.X("t0:T", title=None, axis=alt.Axis(format="%H:%M:%S", labelAngle=0)), x2="t1:T",
        color=alt.Color("ttp:N", scale=alt.Scale(domain=list(TTP_COLOR), range=list(TTP_COLOR.values())), legend=None),
        tooltip=[alt.Tooltip("ttp:N", title="TTP"), alt.Tooltip("t0:T", format="%H:%M:%S", title=T("tl_first")),
                 alt.Tooltip("t1:T", format="%H:%M:%S", title=T("tl_last")), alt.Tooltip("n:Q", title=T("ov_axis_alerts"))])
    ticks = alt.Chart(gdf).mark_tick(thickness=3, size=22).encode(
        y=ysort, x="t0:T", color=alt.Color("uu_tien:N", scale=PRIO_SCALE, legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("ma:N", title=T("col_ma")), alt.Tooltip("ttp:N", title="TTP"), alt.Tooltip("t0:T", format="%H:%M:%S", title=T("col_bat_dau")),
                 alt.Tooltip("t1:T", format="%H:%M:%S", title=T("col_ket_thuc")), alt.Tooltip("uu_tien:N", title=T("col_uu_tien")),
                 alt.Tooltip("diem:Q", format=".4f", title=T("col_diem"))])
    st.altair_chart((bars + ticks).resolve_scale(color="independent").properties(height=max(110, 40 * len(i["chain"]) + 30)), width="stretch")

    ptitle(T("tl_alerts"), T("tl_alerts_h"))
    at = pd.DataFrame([{"ma": a["code"], "uu_tien": prio_name(D.PRIORITY[a["decision_source"]]), "bat_dau": ts(a["t0"]), "ket_thuc": ts(a["t1"]),
                        "diem": a["score"], "ttps": ", ".join(a["ttps"]), "luat": ", ".join(r["id"] for r in a["rule_ids"])} for a in ia])
    cfg = {k: st.column_config.Column(T(f"col_{k}")) for k in at.columns}
    cfg |= {"diem": st.column_config.NumberColumn(T("col_diem"), format="%.4f")}
    sel = st.dataframe(styled(at, {"uu_tien": tone_prio()}), hide_index=True, width="stretch", column_config=cfg,
                       on_select="rerun", selection_mode="single-row", key=f"inc_alerts_{c}")
    pr = sel.selection.rows if sel is not None and hasattr(sel, "selection") else []
    b1, b2 = st.columns([3, 1])
    b1.caption(T("tl_open_h"))
    if b2.button(T("q_open"), type="primary", width="stretch", icon=":material/open_in_new:", disabled=not pr):
        goto_alert(at.iloc[pr[0]]["ma"])
