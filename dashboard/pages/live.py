"""Phan A - trang Truc tiep / Hang doi canh bao (man hinh chinh cua SIEM, docs/STEP9-BRIEF.md muc 2.2 + 3.1).
Doc reports/step9/live/alerts.jsonl + status.json do src/live/run.py (live / replay) ghi; tu lam moi khi luong dang chay.
Dai so (gop trang Tong quan cu), ha tang agent -> Indexer -> VT-Guard, luu luong event, dong ho do tre, MITRE, hang doi co loc / sap.
Khong co nhan (luong truc tiep khong co nhan); chon dong -> trang Chi tiet. Neu chua co luong: nut phat lai log mau."""
import statistics
import time

import altair as alt
import pandas as pd
import streamlit as st

import data as D
from common import (T, cached_live, cached_live_incidents, esc, goto_alert, header, kpis, mitre_html, note, prio_name, ptitle, src_name,
                    styled, tone_prio, ts)

REFRESH = 5
header("siem", T("lv_title"), T("lv_intro"))

def ttp_vi(ttps): return ", ".join(f"{k} ({T('ttp_vi_' + k)})" for k in ttps)

def running():
    return D.replay_running(D.live_status()) or time.time() - st.session_state.get("replay_started", 0) < 20

def start():
    if D.start_replay(10):
        st.session_state["replay_started"] = time.time(); st.cache_data.clear(); st.toast(T("lv_replay_started"))
    else:
        st.toast(T("lv_replay_busy"))

def infra_panel(stt):
    src = stt.get("source") or {}; prm = stt.get("params") or {}
    ptitle(T("lv_infra"), T("lv_infra_h"))
    ags = stt.get("agents") or {}
    nodes = "".join(f'<span class="n on">{esc(h)}</span>' for h in sorted(ags)) or '<span class="n">DC01</span><span class="n">WIN10-01</span>'
    sname = "wazuh-archives-*" if src.get("kind") == "indexer" else (src.get("name") or "-")
    st.markdown(f'<div class="vtg-infra">{nodes}<span>&#8594;</span><span class="n">Wazuh Indexer \u00b7 {esc(sname)}</span>'
                f'<span>&#8594;</span><span class="n on">VT-Guard</span><span>&#8594;</span><span class="n">{esc(T("nav_live"))}</span>'
                + ('<span>&#8594;</span><span class="n on">vtguard-alerts-*</span>' if stt.get("push_alerts") else "") + "</div>", unsafe_allow_html=True)
    rows = [{T("lv_agent"): h, T("lv_agent_events"): v["events"], T("lv_agent_last"): ts(v["last"] or "-")} for h, v in sorted(ags.items())]
    if rows: st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    drop = sum((stt.get("dropped") or {}).values())
    src_txt = (T("lv_src_live", n=src.get("name", "")) + f" \u00b7 {src.get('index', '')}") if src.get("kind") == "indexer" else T("lv_src_replay", n=src.get("name", "-"))
    st.markdown("".join(f'<div class="vtg-note"><b>{esc(k)}:</b> {esc(v)}</div>' for k, v in [
        (T("lv_infra_src"), src_txt), (T("lv_infra_cycle"), f"{stt.get('poll_s', '-')} s"),
        (T("lv_infra_win"), T("lv_infra_win_v", w=prm.get("W", 64), i=int(prm.get("idle_s", 30)))),
        (T("lv_infra_drop"), T("lv_infra_drop_v", n=drop)),
        (T("lv_infra_push"), T("lv_infra_push_on") if stt.get("push_alerts") else T("lv_infra_push_off"))]), unsafe_allow_html=True)

def rate_panel(stt):
    rate = stt.get("rate") or []
    ptitle(T("lv_rate"), T("lv_rate_h", n=len(rate)))
    if not rate: st.caption("-"); return
    df = pd.DataFrame([{"t": pd.Timestamp(t).tz_localize(None), "n": n} for t, n in rate])
    ch = alt.Chart(df).mark_area(line={"color": "#2dd4bf"}, color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0, stops=[
        alt.GradientStop(color="rgba(45,212,191,0.05)", offset=0), alt.GradientStop(color="rgba(45,212,191,0.45)", offset=1)])).encode(
        x=alt.X("t:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0, tickCount=5)), y=alt.Y("n:Q", title=None),
        tooltip=[alt.Tooltip("t:T", format="%d/%m %H:%M:%S"), "n:Q"])
    st.altair_chart(ch.properties(height=150), width="stretch")

def latency_panel(al, stt):
    ptitle(T("lv_latency"), T("lv_latency_h"))
    last = al[-1]
    def med(sel, k): return statistics.median([a["latency"][k] for a in sel if a["latency"].get(k) is not None] or [0])
    rows_l = [(T("lv_lat_latest"), [last]), (T("lv_lat_median"), al)]
    parts = [(T("lv_lat_wazuh"), "wazuh_s", 1.0, "#3d8bfd"), (T("lv_lat_wait"), "wait_s", 1.0, "#f5a524"), (T("lv_lat_infer"), "infer_ms", 0.001, "#22c55e")]
    vals = [[max(0.0, med(sel, k) * f) for _, k, f, _ in parts] for _, sel in rows_l]
    mx = max(sum(v) for v in vals) or 1.0
    html_rows = []
    for (lab, _), v in zip(rows_l, vals):
        segs = "".join(f'<div title="{esc(n)}: {x:.3f} s" style="width:{max(0.6, 100 * x / mx):.2f}%;background:{c};height:18px"></div>'
                       for (n, _, _, c), x in zip(parts, v))
        html_rows.append(f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0"><div style="width:72px;font-size:.78rem;color:#c6d0e2">{esc(lab)}</div>'
                         f'<div style="flex:1;display:flex;border-radius:4px;overflow:hidden;background:#0e1626">{segs}</div>'
                         f'<div class="vtg-mono" style="width:64px;text-align:right">{sum(v):.1f} s</div></div>')
    legend = " ".join(f'<span style="display:inline-block;width:9px;height:9px;background:{c};border-radius:2px;margin:0 4px 0 10px"></span>{esc(n)}'
                      f' <span class="vtg-mono">{vals[0][i]:.{3 if k == "infer_ms" else 1}f} s</span>' for i, (n, k, _, c) in enumerate(parts))
    st.markdown("".join(html_rows) + f'<div style="font-size:.74rem;color:#c6d0e2;margin-top:6px">{legend}</div>', unsafe_allow_html=True)
    note(T("lv_lat_note", idle=int((stt.get("params") or {}).get("idle_s", 30))))

def queue_panel(al):
    rows = D.queue_rows(al)
    with st.expander(T("q_filters"), icon=":material/filter_alt:"):
        f0, f1, f2, f3, f4 = st.columns([1.4, 1, 1, 1.1, 1])
        text = f0.text_input(T("q_search"), placeholder=T("lv_q_search_ph"), key="lv_text")
        hosts = f1.multiselect(T("q_hosts"), sorted({r["host"] for r in rows}), placeholder=T("q_all"), key="lv_hosts")
        srcs = f2.multiselect(T("q_sources"), ["both", "ai"], format_func=src_name, placeholder=T("q_all"), key="lv_src")
        ttps = f3.multiselect(T("q_ttps"), list(D.TTPS), placeholder=T("q_all"), key="lv_ttps")
        sort = f4.selectbox(T("q_sort"), ["moi nhat"] + list(D.SORTS), format_func=lambda k: T("lv_sort_new") if k == "moi nhat" else T(f"sort_{k}"),
                            key="lv_sort")
    q = D.filter_queue(rows, hosts=hosts, ttps=ttps, sources=srcs, text=text.strip() or None)
    by = {a["code"]: a for a in al}
    q = sorted(q, key=lambda r: (by[r["ma"]].get("closed_at") or "", r["ma"]), reverse=True) if sort == "moi nhat" else D.sort_queue(q, sort)
    newest = {a["code"] for a in sorted(al, key=lambda a: (a.get("closed_at") or "", a["code"]), reverse=True)[:3]}
    ptitle(T("lv_queue"), T("lv_queue_h") + f" \u00b7 {len(q)} / {len(rows)}")
    df = pd.DataFrame([{"ma": r["ma"], "moi": T("lv_new") if r["ma"] in newest else "", "uu_tien": prio_name(r["uu_tien"]), "diem": r["diem"],
                        "host": r["host"], "bat_dau": ts(r["bat_dau"]), "ttps": ttp_vi([x for x in r["ttps"].split(", ") if x]), "luat": r["luat"],
                        "nguon": src_name(r["nguon"]), "tre": by[r["ma"]]["latency"].get("total_s"), "su_co": r["su_co"]} for r in q])
    if not len(df): st.info(T("q_empty")); return
    cfg = {c: st.column_config.Column(T(f"col_{c}")) for c in ("host", "ttps", "luat", "nguon", "su_co")}
    cfg |= {"ma": st.column_config.TextColumn(T("col_ma"), pinned=True, width="small"), "moi": st.column_config.TextColumn(T("lv_col_moi"), width="small"),
            "uu_tien": st.column_config.TextColumn(T("col_uu_tien"), width="small"), "bat_dau": st.column_config.TextColumn(T("col_bat_dau")),
            "diem": st.column_config.ProgressColumn(T("col_diem"), min_value=0.8, max_value=1.1, format="%.4f", width="small"),
            "tre": st.column_config.NumberColumn(T("lv_col_tre"), format="%.1f")}
    sel = st.dataframe(styled(df, {"uu_tien": tone_prio(), "moi": {T("lv_new"): "green"}}), hide_index=True, width="stretch", height=400,
                       column_config=cfg, on_select="rerun", selection_mode="single-row", key="live_table")
    pick = sel.selection.rows if sel is not None and hasattr(sel, "selection") else []
    b1, b2, b3 = st.columns([2.2, 1, 1])
    b1.caption(T("q_open_h"))
    csv = df.rename(columns={c: T(f"lv_col_{c}") if c in ("moi", "tre") else T(f"col_{c}") for c in df.columns}).to_csv(index=False).encode("utf-8-sig")
    b2.download_button(T("q_export"), csv, file_name="vtguard_live_alerts.csv", mime="text/csv", icon=":material/download:", width="stretch")
    if b3.button(T("q_open"), type="primary", icon=":material/open_in_new:", disabled=not pick, key="live_open", width="stretch"):
        goto_alert(df.iloc[pick[0]]["ma"])

@st.fragment(run_every=REFRESH if running() else None)
def live_panel():
    al = cached_live(); inc = cached_live_incidents(); stt = D.live_status() or {}; mode = stt.get("mode")
    n_high = sum(a["decision_source"] == "both" for a in al)
    lat = [a["latency"]["total_s"] for a in al if a.get("latency", {}).get("total_s") is not None]
    src = stt.get("source") or {}
    src_txt = T("lv_src_live", n=src.get("name", "")) if mode == "live" else T("lv_src_replay", n=src.get("name", "-")) if mode else T("lv_src_none")
    state = T("lv_done_pre") if stt.get("done") else ""
    kpis([(T("lv_k_stream"), T("lv_mode_" + (mode or "none")), T("lv_k_stream_s", state=state, src=src_txt, c=(stt.get("stream_clock") or "-").replace("T", " ").replace("Z", "")), "teal"),
          (T("lv_k_events"), f"{stt.get('events_read', 0):,}".replace(",", "."), T("lv_k_events_s", w=stt.get("windows", 0)), "gray"),
          (T("lv_k_open"), str(len(al)), T("lv_k_open_s", n=len(inc)), "blue"),
          (T("ov_m_both"), str(n_high), T("ov_m_both_s"), "red"),
          (T("ov_m_ai"), str(len(al) - n_high), T("ov_m_ai_s"), "amber"),
          (T("lv_k_latency"), (f"{lat[-1]:.0f}" if lat else "-", " s"), T("lv_k_latency_s", m=f"{statistics.median(lat):.0f}" if lat else "-"), "violet")])
    run = running()
    c = st.columns([3, 1])
    c[0].caption((T("lv_running", s=REFRESH) + " \u00b7 " if run else "") + T("lv_honest"))
    if not run and c[1].button(T("lv_btn_replay_again") if al else T("lv_btn_replay"), icon=":material/replay:", width="stretch", key="lv_replay"):
        start(); st.rerun()
    if not al:
        st.info(T("lv_empty"))
        with st.expander(T("lv_cmd"), icon=":material/terminal:"):
            st.code("python src/live/run.py replay --input samples/replay_demo.jsonl.gz --speed 10\n"
                    "python src/live/run.py live --env-file <file_env> [--push-alerts]", language="bash")
        if stt:
            with st.container(border=True): infra_panel(stt)
        return
    c1, c2, c3 = st.columns([1.15, 1, 1.1], gap="medium")
    with c1.container(border=True): infra_panel(stt)
    with c2.container(border=True): rate_panel(stt)
    with c3.container(border=True): latency_panel(al, stt)
    c1, c2 = st.columns([2.6, 1], gap="medium")
    with c1.container(border=True): queue_panel(al)
    with c2.container(border=True):
        ptitle(T("lv_mitre"), T("lv_mitre_h"))
        st.markdown(mitre_html({k: sum(k in a["ttps"] for a in al) for k in D.TTPS}, {k: sum(k in i["chain"] for i in inc) for k in D.TTPS}, stacked=True),
                    unsafe_allow_html=True)
        note(T("ov_mitre_note"))
        st.write("")
        ptitle(T("ov_rules"), T("ov_rules_h"))
        rc = D.rule_counts(al)
        if rc:
            rd = pd.DataFrame([{"luat": k, "n": v} for k, v in rc.most_common()])
            ch = alt.Chart(rd).mark_bar(cornerRadiusEnd=3, color="#3d8bfd").encode(
                y=alt.Y("luat:N", sort="-x", title=None), x=alt.X("n:Q", title=T("ov_axis_alerts")), tooltip=["luat:N", "n:Q"])
            st.altair_chart((ch + ch.mark_text(align="left", dx=4, color="#c6d0e2").encode(text="n:Q")).properties(height=24 * len(rd) + 30), width="stretch")
        note(T("lv_k_rule_s", k=sum(bool(a["rule_ids"]) for a in al), n=len(al)) + " \u00b7 " + T("ov_no_rule_only"))

live_panel()
