"""Trang Chi tiet canh bao: diem AI so voi nguong (s = p + beta * r, theo TTP s_k = p_k + beta * r_k), luat Sigma khop
(YAML + provenance + tai ve), top-5 event theo attention, canh bao cung su co. Che do danh gia: them nhan that cua cua so."""
import altair as alt
import pandas as pd
import streamlit as st

import data as D
from common import (T, TTP_COLOR, badge, cached_alerts, cached_labels, cached_scores, chain_html, esc, goto_incident, header, kv,
                    note, prio_badge, prio_name, ptitle, res_md, short_split, src_badge, styled, tone_prio, ts, ttp_chips)

ev = header(T("navsec_monitor"), T("d_title"), T("d_intro"))
al = cached_alerts(); by_code = {a["code"]: a for a in al}; scores = cached_scores()
order = [r["ma"] for r in D.sort_queue(D.queue_rows(al))]

if "goto_alert" in st.session_state:
    st.session_state["detail_alert"] = st.session_state.pop("goto_alert")
elif st.session_state.get("detail_alert") not in by_code:
    qp = st.query_params.get("alert", "")
    st.session_state["detail_alert"] = qp if qp in by_code else order[0]

def _label(c):
    a = by_code[c]
    return f"{c} \u00b7 {prio_name(D.PRIORITY[a['decision_source']])} \u00b7 {a['host']} \u00b7 {ts(a['t0'], 16)} \u00b7 {a['score']:.4f}"

top = st.columns([3, 1])
code = top[0].selectbox(T("d_pick"), order, format_func=_label, key="detail_alert")
a = by_code[code]; det = D.alert_detail(a, scores); prio = D.PRIORITY[a["decision_source"]]
if top[1].button(T("d_goto_inc", c=a["incident"]), width="stretch", icon=":material/timeline:"): goto_incident(a["incident"])

# ---- the tom tat ----
facts = [(T("col_host"), esc(a["host"])), (T("d_time"), esc(f"{ts(a['t0'])} \u2192 {ts(a['t1'])} UTC")),
         (T("d_session"), f'<span class="vtg-mono">{esc(a["session"])}</span>'), (T("col_cua_so"), f'<span class="vtg-mono">{esc(a["window"])}</span>'),
         (T("col_tap"), esc(short_split(a["split"]))), (T("col_ttps"), ttp_chips(a["ttps"])),
         (T("col_luat"), esc(", ".join(r["id"] for r in a["rule_ids"]) or T("d_no_rule_short")))]
card = (f'<div class="vtg-card"><div class="head"><span class="code">{esc(code)}</span>{prio_badge(prio)} {src_badge(a["decision_source"])} '
        f'{badge(a["incident"], "violet")}</div>{kv(facts)}</div>')
if ev:
    y, yt = cached_labels()[a["window_id"]]
    c1, c2 = st.columns([2.2, 1])
    c1.markdown(card, unsafe_allow_html=True)
    with c2.container(border=True):
        ptitle(T("d_truth"), T("d_truth_h"))
        st.markdown(res_md("Dung" if y else "Nham"))
        st.markdown(kv([(T("col_ttp_that"), ttp_chips(yt)), (T("d_raw_window"), f'<span class="vtg-mono">{esc(a["window_id"])}</span>')]),
                    unsafe_allow_html=True)
else:
    st.markdown(card, unsafe_allow_html=True)
st.markdown(chain_html([k for k in D.TTPS if k in a["ttps"]]), unsafe_allow_html=True)

# ---- diem so voi nguong ----
def score_chart(rows, taus, height):
    seg = alt.Scale(domain=[T("d_seg_ai"), T("d_seg_rule")], range=["#3d8bfd", "#a78bfa"])
    names = [r["name"] for r in taus]
    bars = alt.Chart(pd.DataFrame(rows)).mark_bar(height=18).encode(
        y=alt.Y("name:N", sort=names, title=None), x=alt.X("start:Q", title=None, scale=alt.Scale(domain=[0, 1.15])), x2="end:Q",
        color=alt.Color("seg:N", scale=seg, legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("name:N", title="TTP"), alt.Tooltip("seg:N", title=T("d_component")), alt.Tooltip("val:Q", format=".4f", title=T("d_value"))])
    tdf = pd.DataFrame(taus)
    tick = alt.Chart(tdf).mark_tick(color="#f05252", thickness=3, size=26).encode(
        y=alt.Y("name:N", sort=names), x="tau:Q", tooltip=[alt.Tooltip("tau:Q", format=".4f", title=T("d_threshold"))])
    lab = alt.Chart(tdf).mark_text(align="left", dx=6, color="#d8e0ee", fontSize=11).encode(y=alt.Y("name:N", sort=names), x="s:Q", text="txt:N")
    return (bars + tick + lab).properties(height=height)

c1, c2 = st.columns([1.25, 1], gap="medium")
with c1.container(border=True):
    ptitle(T("d_score"), T("d_score_h"))
    rows = [{"name": T("d_bin"), "seg": T("d_seg_ai"), "start": 0, "end": det["p"], "val": det["p"]}]
    if det["bonus"] > 0: rows.append({"name": T("d_bin"), "seg": T("d_seg_rule"), "start": det["p"], "end": det["s"], "val": det["bonus"]})
    st.altair_chart(score_chart(rows, [{"name": T("d_bin"), "tau": det["tau"], "s": det["s"], "txt": f"s = {det['s']:.4f}"}], 70), width="stretch")
    st.markdown(f'<div class="vtg-mono" style="margin:-4px 0 12px">s = p + &beta;&middot;r = {det["p"]:.4f} + {det["beta"]} &times; {det["r"]} = '
                f'<b>{det["s"]:.4f}</b> &ge; &tau; = {det["tau"]:.4f} <span class="vtg-muted">({T("d_margin")} +{det["margin"]:.4f})</span></div>',
                unsafe_allow_html=True)
    ptitle(T("d_ttp"), T("d_ttp_h"))
    rows, taus = [], []
    for t in det["ttp"]:
        rows.append({"name": t["ttp"], "seg": T("d_seg_ai"), "start": 0, "end": t["p"], "val": t["p"]})
        if t["bonus"] > 0: rows.append({"name": t["ttp"], "seg": T("d_seg_rule"), "start": t["p"], "end": t["s"], "val": t["bonus"]})
        taus.append({"name": t["ttp"], "tau": t["tau"], "s": t["s"], "txt": f"{t['s']:.3f}" + ("  \u2713" if t["chon"] else "")})
    st.altair_chart(score_chart(rows, taus, 220), width="stretch")
    bk = T("d_col_bonus")
    tt = pd.DataFrame([{"TTP": t["ttp"], "p_k": t["p"], bk: t["bonus"], "s_k": t["s"], "\u03c4_k": t["tau"],
                        T("d_channel"): "\u2713" if t["kenh_luat"] else "\u2013", T("d_decision"): T("d_yes") if t["chon"] else T("d_no")}
                       for t in det["ttp"]])
    st.dataframe(styled(tt, {T("d_decision"): {T("d_yes"): "red", T("d_no"): "gray"}}), hide_index=True, width="stretch",
                 column_config={k: st.column_config.NumberColumn(k, format="%.4f") for k in ("p_k", bk, "s_k", "\u03c4_k")})
    note(T("d_ttp_note", ch=", ".join(a["fusion_config"]["rule_ttp_channels"]), b=det["beta"]))

with c2.container(border=True):
    ptitle(T("d_rules"), T("d_rules_h", n=len(a["rule_ids"])))
    if not a["rule_ids"]:
        st.markdown(f'<div class="vtg-strip eval" style="margin:4px 0">{esc(T("d_no_rule"))}</div>', unsafe_allow_html=True)
    for i, r in enumerate(a["rule_ids"]):
        prov, _ = D.rule_provenance(r["id"]); docs = D.sigma_docs(r["id"]); topd = docs[-1]
        with st.expander(f"{r['id']} \u00b7 {r['target']} \u00b7 {topd.get('level', '')}", expanded=i == 0, icon=":material/rule:"):
            st.markdown(kv([(T("r_pred"), f'<span class="vtg-mono">{esc(" AND ".join(prov["predicates"]))}</span>'),
                            (T("r_target"), esc(r["target"])), (T("r_kind"), esc(T("r_kind_corr") if "correlation" in topd else T("r_kind_single"))),
                            (T("r_train"), esc(T("r_train_v", n=prov["train"]["support"], tp=prov["train"]["tp"], fp=prov["train"]["fp"]))),
                            (T("r_oof"), esc(T("r_oof_v", p=prov["oof"]["precision"], n=prov["oof"]["tp"] + prov["oof"]["fp"]))),
                            (T("r_folds"), esc(f"{len(prov['oof']['folds_rediscovered'])}/5")),
                            (T("r_file"), f'<span class="vtg-mono">{esc(r["sigma_file"])}</span>')]), unsafe_allow_html=True)
            st.code(D.sigma_text(r["id"]), language="yaml", height=260)
            st.download_button(T("r_download"), D.sigma_text(r["id"]).encode("utf-8"), file_name=f"{r['id']}.yml", mime="application/x-yaml",
                               key=f"dl_{code}_{r['id']}", icon=":material/download:")
    note(T("d_rules_note"))

with st.container(border=True):
    ptitle(T("d_attn"), T("d_attn_h"))
    at = pd.DataFrame([{"#": e["idx"], "alpha": e["alpha"], T("d_image"): e["image_name"], T("d_parent"): e["parent_image_name"] or "-",
                        "Event ID": e["event_id"], T("d_channel_log"): e["channel"], T("d_cmd"): e["cmd_canon"] or "-"} for e in a["attention_top5"]])
    st.dataframe(at, hide_index=True, width="stretch",
                 column_config={"alpha": st.column_config.ProgressColumn("attention \u03b1", min_value=0.0, max_value=max(at["alpha"].max(), 0.01), format="%.4f", width="small"),
                                "#": st.column_config.NumberColumn("#", width="small"), "Event ID": st.column_config.NumberColumn("Event ID", width="small", format="%d"),
                                T("d_cmd"): st.column_config.TextColumn(T("d_cmd"), width="large")})
    note(T("d_attn_note"))

with st.container(border=True):
    inc = [x for x in al if x["incident"] == a["incident"]]
    inc.sort(key=lambda x: (D._dt(x["t0"]), x["code"]))
    ptitle(T("d_related", c=a["incident"]), T("d_related_h", n=len(inc)))
    rel = pd.DataFrame([{T("col_ma"): x["code"], T("col_uu_tien"): prio_name(D.PRIORITY[x["decision_source"]]),
                         T("col_bat_dau"): ts(x["t0"]), T("col_diem"): x["score"], T("col_ttps"): ", ".join(x["ttps"]),
                         T("col_luat"): ", ".join(r["id"] for r in x["rule_ids"]), T("d_current"): "\u25c0" if x["code"] == code else ""} for x in inc])
    rel_codes = [x["code"] for x in inc]; rel_key = f"rel_{a['incident']}"

    def _rel_pick():
        r = st.session_state[rel_key].selection.rows
        if r: st.session_state["detail_alert"] = rel_codes[r[0]]
    st.dataframe(styled(rel, {T("col_uu_tien"): tone_prio()}), hide_index=True, width="stretch", key=rel_key, on_select=_rel_pick,
                 selection_mode="single-row", column_config={T("col_diem"): st.column_config.NumberColumn(T("col_diem"), format="%.4f")})
    note(T("d_related_note"))
