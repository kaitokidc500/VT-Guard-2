"""Trang Tong quan (SOC): KPI, canh bao theo thoi gian, nguon quyet dinh, ma tran MITRE ATT&CK, host, luat, theo tap,
suc khoe + do tre pipeline. Che do danh gia: precision theo nguon (CI Wilson, tu results JSON) + dung / nham theo tap."""
import altair as alt
import pandas as pd
import streamlit as st

import data as D
from common import (PRIO_COLOR, SRC_COLOR, T, cached_alerts, cached_checksum, cached_incidents, cached_pipeline, esc, header,
                    kpis, note, prio_name, ptitle, short_split, split_name, src_name, tactic_name)

ev = header(T("navsec_monitor"), T("ov_title"), T("ov_intro"))
al = cached_alerts(); inc = cached_incidents(); ov = D.overview_counts(al); tot = ov["tong"]; pi = cached_pipeline()
n_high = tot["decision_source"].get("both", 0); n_ai = tot["decision_source"].get("ai", 0)
kpis([(T("ov_m_alerts"), str(tot["n"]), T("ov_m_alerts_s"), "blue"),
      (T("ov_m_both"), (str(n_high), f" / {tot['n']}"), T("ov_m_both_s"), "red"),
      (T("ov_m_ai"), (str(n_ai), f" / {tot['n']}"), T("ov_m_ai_s"), "amber"),
      (T("ov_m_inc"), str(len(inc)), T("ov_m_inc_s", n=sum(i["priority"] == "Cao" for i in inc)), "violet"),
      (T("ov_m_hosts"), str(len({a["host"] for a in al})), ", ".join(sorted({a["host"] for a in al})), "teal"),
      (T("ov_m_rule"), (f"{tot['with_rule'] / tot['n']:.0%}", ""), T("ov_m_rule_s", k=tot["with_rule"], n=tot["n"]), "green")])

PRIO_SCALE = alt.Scale(domain=[prio_name("Cao"), prio_name("Can xem lai")], range=[PRIO_COLOR["Cao"], PRIO_COLOR["Can xem lai"]])
df = pd.DataFrame([{"t": D._dt(a["t0"]).replace(tzinfo=None), "uu_tien": prio_name(D.PRIORITY[a["decision_source"]]), "host": a["host"],
                    "nguon": src_name(a["decision_source"])} for a in al])

c1, c2 = st.columns([2.1, 1], gap="medium")
with c1.container(border=True):
    ptitle(T("ov_timeline"), T("ov_timeline_h"))
    ch = alt.Chart(df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        x=alt.X("yearmonthdatehours(t):T", title=None, axis=alt.Axis(format="%d/%m %H:00", labelAngle=0, tickCount=8)),
        y=alt.Y("count():Q", title=T("ov_axis_alerts")), color=alt.Color("uu_tien:N", scale=PRIO_SCALE, legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("yearmonthdatehours(t):T", title=T("ov_axis_hour"), format="%d/%m %H:00"), alt.Tooltip("uu_tien:N", title=T("col_uu_tien")),
                 alt.Tooltip("count():Q", title=T("ov_axis_alerts"))]).properties(height=250)
    st.altair_chart(ch, width="stretch")
with c2.container(border=True):
    ptitle(T("ov_chart"), T("ov_chart_h"))
    ds = pd.DataFrame([{"nguon": src_name(s), "n": tot["decision_source"].get(s, 0)} for s in ("both", "ai")])
    base = alt.Chart(ds).encode(theta=alt.Theta("n:Q", stack=True),
                                color=alt.Color("nguon:N", scale=alt.Scale(domain=[src_name("both"), src_name("ai")], range=[SRC_COLOR["both"], SRC_COLOR["ai"]]),
                                                legend=alt.Legend(title=None, orient="bottom")), tooltip=["nguon:N", "n:Q"])
    pie = base.mark_arc(innerRadius=62, outerRadius=95, stroke="#0b1120", strokeWidth=2)
    txt = alt.Chart(pd.DataFrame([{"t": str(tot["n"])}])).mark_text(fontSize=26, fontWeight="bold", color="#f3f6fb").encode(text="t:N")
    st.altair_chart((pie + txt).properties(height=250), width="stretch")
    note(T("ov_no_rule_only"))

c1, c2 = st.columns([2.1, 1], gap="medium")
with c1.container(border=True):
    ptitle(T("ov_mitre"), T("ov_mitre_h"))
    tc = D.ttp_counts(al); mx = max(v["alerts"] for v in tc.values()) or 1
    cols = []
    for tac in ("TA0007", "TA0006"):
        cells = []
        for k in [k for k in D.TTPS if D.MITRE[k][0] == tac]:
            a = tc[k]["alerts"]; alpha = 0.10 + 0.55 * a / mx
            cells.append(f'<div class="vtg-tcell" style="background:rgba(240,82,82,{alpha:.2f})"><div class="id">{k}</div>'
                         f'<div class="nm">{esc(D.MITRE[k][1])}</div><div class="ct"><b>{a}</b> {esc(T("ov_mitre_alerts"))} \u00b7 '
                         f'<b>{tc[k]["incidents"]}</b> {esc(T("ov_mitre_inc"))}</div></div>')
        cols.append(f'<div class="vtg-tac"><div class="th">{esc(tactic_name(tac))} <span>{tac}</span></div><div class="vtg-tcells">{"".join(cells)}</div></div>')
    st.markdown(f'<div class="vtg-matrix">{"".join(cols)}</div>', unsafe_allow_html=True)
    note(T("ov_mitre_note"))
with c2.container(border=True):
    ptitle(T("ov_hosts"), T("ov_hosts_h"))
    ch = alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=26).encode(
        y=alt.Y("host:N", title=None, sort="-x"), x=alt.X("count():Q", title=T("ov_axis_alerts")),
        color=alt.Color("uu_tien:N", scale=PRIO_SCALE, legend=None), tooltip=["host:N", "uu_tien:N", "count():Q"]).properties(height=150)
    st.altair_chart(ch, width="stretch")
    hs = pd.DataFrame([{T("col_host"): h, T("ov_axis_alerts"): sum(a["host"] == h for a in al), T("ov_m_inc"): sum(i["host"] == h for i in inc)}
                       for h in sorted({a["host"] for a in al})])
    st.dataframe(hs, hide_index=True, width="stretch")

c1, c2 = st.columns(2, gap="medium")
with c1.container(border=True):
    ptitle(T("ov_rules"), T("ov_rules_h"))
    rc = D.rule_counts(al)
    rd = pd.DataFrame([{"luat": k, "n": v} for k, v in rc.items()])
    ch = alt.Chart(rd).mark_bar(cornerRadiusEnd=3, color="#3d8bfd").encode(
        y=alt.Y("luat:N", sort="-x", title=None), x=alt.X("n:Q", title=T("ov_axis_alerts")), tooltip=["luat:N", "n:Q"]).properties(height=300)
    st.altair_chart(ch + ch.mark_text(align="left", dx=4, color="#c6d0e2").encode(text="n:Q"), width="stretch")
with c2.container(border=True):
    ptitle(T("ov_by_split"), T("ov_by_split_h"))
    rows = [{T("ov_col_split"): split_name(s) if s == "tong" else short_split(s), T("ov_col_n"): ov[s]["n"], T("ov_col_rule"): ov[s]["with_rule"],
             T("ov_col_both"): ov[s]["decision_source"].get("both", 0), T("ov_col_ai"): ov[s]["decision_source"].get("ai", 0)}
            for s in list(D.SPLITS) + ["tong"]]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    note(T("ov_split_note"))
    st.write("")
    ptitle(T("ov_health"), T("ov_health_h"))
    cs = cached_checksum(); n_ok = sum(v is True for v in cs.values())
    items = [(n_ok == len(cs), T("h_checksum"), T("h_checksum_d", k=n_ok, n=len(cs))),
             (pi["mismatch"] == 0, T("h_pipeline"), T("h_pipeline_d", n=pi["n_windows"], m=pi["mismatch"])),
             (True, T("h_model"), T("h_model_d")), (True, T("h_rules"), T("h_rules_d", n=pi["n_rules"])),
             (True, T("h_fusion"), T("h_fusion_d", s=pi["strategy"], v=pi["variant"], b=pi["beta"], c=pi["lock_commit"]))]
    st.markdown('<div class="vtg-health">' + "".join(f'<div class="vtg-hitem"><div class="st{"" if ok else " bad"}"></div><div><div class="n">{esc(n)}</div>'
                                                     f'<div class="d">{esc(d)}</div></div></div>' for ok, n, d in items) + "</div>", unsafe_allow_html=True)

with st.container(border=True):
    lat, host = D.latency()
    ptitle(T("ov_latency"), f"{T('ov_lat_host')}: {host['cpu']} \u00b7 onnxruntime {host['onnxruntime']} \u00b7 {host['onnx_threads']} thread")
    lr = [{T("ov_lat_step"): T(f"lat_{k}"), T("ov_lat_b1m"): lat["batch1"][k][0], T("ov_lat_b1p"): lat["batch1"][k][1],
           T("ov_lat_b32m"): lat["batch32"][k][0], T("ov_lat_b32p"): lat["batch32"][k][1]} for k in ("total", "featurize", "onnx", "sigma", "fusion")]
    st.dataframe(pd.DataFrame(lr), hide_index=True, width="stretch",
                 column_config={T(k): st.column_config.NumberColumn(T(k), format="%.3f ms") for k in ("ov_lat_b1m", "ov_lat_b1p", "ov_lat_b32m", "ov_lat_b32p")})

if ev:
    c1, c2 = st.columns([1.5, 1], gap="medium")
    with c1.container(border=True):
        ptitle(T("ov_eval_title"), T("ov_eval_h"))
        pr = D.precision_by_source()
        er = []
        for s in list(D.SPLITS) + ["gop"]:
            for src in ("both", "ai"):
                v = pr[s][src]
                if not v["n"]: continue
                er.append({T("ov_col_split"): split_name("tong") if s == "gop" else short_split(s), T("ov_col_src"): src_name(src),
                           T("ov_col_tpn"): f"{v['tp']}/{v['n']}", T("ov_col_prec"): v["precision"],
                           T("ov_col_ci"): f"[{v['wilson']['lo']:.3f}; {v['wilson']['hi']:.3f}]"})
        st.dataframe(pd.DataFrame(er), hide_index=True, width="stretch",
                     column_config={T("ov_col_prec"): st.column_config.ProgressColumn(T("ov_col_prec"), min_value=0.0, max_value=1.0, format="%.3f")})
        note(T("ov_eval_note"))
    with c2.container(border=True):
        ptitle(T("ov_tpfp"), "step8_results.json")
        stt = D.results(8)["explanation"]["stats"]
        st.dataframe(pd.DataFrame([{T("ov_col_split"): short_split(s), T("ov_col_n"): stt[s]["alerts"]["n"], T("ov_col_tp"): stt[s]["tp"]["n"],
                                    T("ov_col_fp"): stt[s]["fp"]["n"], T("ov_col_missed"): stt[s]["positives_missed"]} for s in D.SPLITS]),
                     hide_index=True, width="stretch")
        note(T("ov_tpfp_note"))
