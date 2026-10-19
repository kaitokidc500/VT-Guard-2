"""Phan B - trang Ket qua nghien cuu (docs/STEP9-BRIEF.md muc 3.4 + kich ban man 5): 3 the yeu cau de tai (YC1 luat tu sinh co xuat
xu, YC2 hop nhat AI + luat, YC3 mo hinh chuoi tuy bien) roi cac tab bang chung: VT-Guard so voi Wazuh (B0) theo tung ky thuat,
chuoi ablation + Holm (YC3), hop nhat OOF / test + Holm + precision theo nguon (YC2), bang so sanh mo hinh, 101 canh bao tap kiem thu
co nhan, tai lap (verify / Docker / do lech truc tiep) + tieu chi chap nhan. Moi so lieu doc tu results / eval JSON, khong tinh lai."""
import altair as alt
import pandas as pd
import streamlit as st

import data as D
from common import (T, badge, cached_alerts, cached_highlights, cached_labels, esc, goto_alert, header, kpis, note, prio_name, ptitle,
                    short_split, src_name, styled, tone_prio, tone_res, ts)

header("research", T("res_title"), T("res_intro"))
H = cached_highlights(); y1, y2, y3 = H["yc1"], H["yc2"], H["yc3"]
cmp_ = D.model_comparison(); cm = {r["key"]: r for r in cmp_}; hr = D.holm_rows(); acc = D.acceptance()
h8 = {r["metric"]: r for r in y2["holm"] if r["cmp"] == "F3-B - F1"}

# ---------------- 3 yeu cau de tai ----------------
def req(title, big, lines, see):
    return (f'<div class="vtg-req"><div class="h">{esc(title)}</div><div class="big">{esc(big)}</div><ul>'
            + "".join(f"<li>{esc(x)}</li>" for x in lines) + f'</ul><div class="see">{esc(T("res_yc_see"))}: {esc(see)}</div></div>')

ptitle(T("res_req_title"), T("res_req_h"))
st.markdown('<div class="vtg-reqs">' + "".join([
    req(T("res_yc1"), T("res_yc1_big", n=y1["n_rules"]),
        [T("res_yc1_l1", e=y1["engine"].upper(), err=y1["sigma_errors"], rej=y1["rejected"]),
         T("res_yc1_l2", fp=y1["hard_fp"], b0=y1["b0_hard_fp"]), T("res_yc1_l3", t=", ".join(y1["ttp_rules"]))], T("nav_rules")),
    req(T("res_yc2"), T("res_yc2_big", tp=y2["both_tp"], n=y2["both_n"]),
        [T("res_yc2_l1", tp=y2["both_tp"], n=y2["both_n"], atp=y2["ai_tp"], an=y2["ai_n"]),
         T("res_yc2_l2", d1=h8["macro-F1 TTP T-novel"]["diff"], d2=h8["PR-AUC T-novel"]["diff"]),
         T("res_yc2_l3", f=y2["f3_macro"]["v"], a=y2["ai_macro"]["v"], k=y2["with_rule"], t=y2["n_alerts"])], T("res_tab_yc2")),
    req(T("res_yc3"), T("res_yc3_big", m=y3["macro"]["v"]),
        [T("res_yc3_l1", m=y3["macro"]["v"], b0=y3["b0_macro"]["v"]),
         T("res_yc3_l2", d=y3["holm"]["diff"], p=y3["holm"]["p_holm"], m0=y3["oof_m0"]["v"], m1=y3["oof_m1"]["v"]),
         T("res_yc3_l3", fp=y3["hard_fp"], b0=y3["b0_hard_fp"])], T("res_tab_yc3"))]) + "</div>", unsafe_allow_html=True)
c = st.columns([1, 1, 3])
if c[0].button(T("nav_rules"), icon=":material/rule:", width="stretch"): st.switch_page("pages/rules.py")
if c[1].button(T("nav_live"), icon=":material/sensors:", width="stretch"): st.switch_page("pages/live.py")

tabs = st.tabs([T("res_tab_wazuh"), T("res_tab_yc3"), T("res_tab_yc2"), T("e_tab_cmp"), T("res_tab_alerts"), T("res_tab_repro")], key="res_tab")
COLORS = {"B0": "#64748b", "RULES": "#a78bfa", "VTSEQ": "#3d8bfd", "F3B": "#22c55e"}

# ---------------- VT-Guard so voi Wazuh ----------------
with tabs[0]:
    b0 = cm["B0"]
    st.markdown(f'<div class="vtg-strip research">{esc(T("res_wz_blind", n=len(H["blind"]), t=", ".join(H["blind"]), f=b0["t_novel_f1"]["v"], fp=int(b0["t_hard_fp"]["v"])))}</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1.7, 1], gap="medium")
    with c1.container(border=True):
        sp = st.segmented_control(T("col_tap"), ["t_novel", "t_clean"], format_func=short_split, default="t_novel", key="wz_split", required=True)
        pt = H["per_ttp"] if sp == "t_novel" else D.per_ttp_f1(sp)
        ptitle(T("res_wz"), T("res_wz_h"))
        order = ["B0", "RULES", "VTSEQ", "F3B"]
        df = pd.DataFrame([{"ttp": f"{t} {T('ttp_vi_' + t)}", "m": T(f"m_{k}"), "k": k, "f1": pt[k][t]["f1"]} for t in D.TTPS for k in order])
        ch = alt.Chart(df).mark_bar(cornerRadiusEnd=2).encode(
            y=alt.Y("m:N", sort=[T(f"m_{k}") for k in order], title=None, axis=None), x=alt.X("f1:Q", title="F1", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("m:N", scale=alt.Scale(domain=[T(f"m_{k}") for k in order], range=[COLORS[k] for k in order]),
                            legend=alt.Legend(title=None, orient="top")),
            row=alt.Row("ttp:N", sort=[f"{t} {T('ttp_vi_' + t)}" for t in D.TTPS], title=None, header=alt.Header(labelAngle=0, labelAlign="left", labelColor="#c6d0e2")),
            tooltip=[alt.Tooltip("ttp:N", title="TTP"), alt.Tooltip("m:N", title=T("e_c_model")), alt.Tooltip("f1:Q", format=".3f")])
        st.altair_chart(ch.properties(height=58, width=400), width="content")
        st.dataframe(pd.DataFrame([{T("res_wz_col_ttp"): f"{t} \u00b7 {T('ttp_vi_' + t)}", T("res_wz_col_n"): pt["B0"][t]["n_pos"],
                                    **{T(f"m_{k}"): pt[k][t]["f1"] for k in order}} for t in D.TTPS]), hide_index=True, width="stretch",
                     column_config={T(f"m_{k}"): st.column_config.NumberColumn(T(f"m_{k}"), format="%.3f") for k in order})
        note(T("res_wz_note", n=pt["B0"]["T1003.003"]["n_pos"], s=short_split(sp)))
    with c2.container(border=True):
        ptitle(T("e_chart_fp"), T("e_chart_fp_h"))
        fd = pd.DataFrame([{"m": T(f"m_{r['key']}"), "fp": r["t_hard_fp"]["v"], "k": r["key"]} for r in cmp_])
        ch = alt.Chart(fd).mark_bar(height=20, cornerRadiusEnd=3).encode(
            y=alt.Y("m:N", sort=list(fd["m"]), title=None), x=alt.X("fp:Q", title=T("e_c_hard_fp")),
            color=alt.condition(alt.datum.k == "B0", alt.value("#f05252"), alt.value("#3d8bfd")), tooltip=["m:N", alt.Tooltip("fp:Q", format=".1f")])
        st.altair_chart((ch + ch.mark_text(align="left", dx=4, color="#c6d0e2").encode(text=alt.Text("fp:Q", format=".1f"))).properties(height=270), width="stretch")
        note(T("e_cmp_note"))

# ---------------- YC3 mo hinh chuoi ----------------
with tabs[1]:
    kpis([(T("e_k_macro").replace("F3-B", "VT-Seq-ens"), f"{y3['macro']['v']:.3f}", T("e_k_macro_s", lo=y3["macro"]["lo"], hi=y3["macro"]["hi"]), "blue"),
          ("OOF macro-F1 TTP", (f"{y3['oof_m0']['v']:.3f} \u2192 {y3['oof_m1']['v']:.3f}", ""), "M0a \u2192 M1 (attention)", "teal"),
          ("VT-Seq-ens \u2212 B3 (b)", f"{y3['holm']['diff']:+.3f}", f"p Holm {y3['holm']['p_holm']:.3f}", "green"),
          (T("e_k_fp").replace("F3-B", "VT-Seq-ens"), (f"{y3['hard_fp']:.0f}", " / 88"), f"B0 {y3['b0_hard_fp']:.0f} / 88", "amber")])
    with st.container(border=True):
        ptitle(T("e_chain"), T("e_chain_h"))
        labs = {"oof_macro_f1_ttp": "OOF macro-F1 TTP", "oof_pr_auc_bin": "OOF PR-AUC", "oof_fpr_hard_negative": "OOF FPR hard_neg",
                "test_t_novel_f1": "T-novel F1", "test_t_novel_pr_auc": "T-novel PR-AUC", "test_macro_f1_clean": "macro-F1 clean",
                "test_macro_f1_novel": "macro-F1 novel", "test_t1654_novel": "T1654 novel", "test_t_hard_fp": "T-hard FP/88"}
        st.dataframe(pd.DataFrame([{T("e_c_code"): r["code"], T("e_c_cfg"): r["desc"], "seed": r["n_seeds"],
                                    **{v: D.fmt(r[k], nd=1 if k == "test_t_hard_fp" else 3, pm=" \u00b1 ") for k, v in labs.items()}} for r in D.ablation_chain()]),
                     hide_index=True, width="stretch")
        note(T("e_chain_note") + " " + y3["deployed"])
    c1, c2 = st.columns(2, gap="medium")
    with c1.container(border=True):
        rs = [r for r in hr if r["family"] == 6]
        ptitle(T("e_holm6"), T("e_holm_h", n=len(rs)))
        st.dataframe(pd.DataFrame([{T("e_c_cmp"): r["cmp"].replace("VT-Seq-ens - ", ""), T("e_c_metric"): r["metric"],
                                    T("e_c_diff"): f"{r['diff']:+.3f} [{r['lo']:+.3f}; {r['hi']:+.3f}]", T("e_c_pholm"): r["p_holm"],
                                    T("e_c_concl"): T("e_sig") if r["sig"] else T("e_nsig")} for r in rs]).pipe(styled, {T("e_c_concl"): {T("e_sig"): "green", T("e_nsig"): "gray"}}),
                     hide_index=True, width="stretch", column_config={T("e_c_pholm"): st.column_config.NumberColumn(T("e_c_pholm"), format="%.3f")})
        note(T("e_holm6_note"))
    with c2.container(border=True):
        ptitle(T("e_feat"), T("e_feat_h"))
        fa = D.feature_ablation(); fams = list(dict.fromkeys(r["family"] for r in fa))
        st.dataframe(pd.DataFrame([{T("e_c_family"): f, **{f"({v}) macro-F1 novel": D.fmt(next(r for r in fa if r["family"] == f and r["variant"] == v)["macro_novel"], nd=2, sep="; ", pm=" \u00b1 ")
                                                          for v in ("a", "b", "c'")},
                                    **{f"({v}) FP T-hard": D.fmt(next(r for r in fa if r["family"] == f and r["variant"] == v)["t_hard_fp"], nd=1, pm=" \u00b1 ") for v in D.ABL_VARIANTS}}
                                   for f in fams]), hide_index=True, width="stretch")
        note(T("e_feat_note"))

# ---------------- YC2 hop nhat ----------------
with tabs[2]:
    kpis([(T("ov_m_both"), (f"{y2['both_tp']}", f" / {y2['both_n']}"), T("ov_eval_h"), "red"),
          (T("ov_m_ai"), (f"{y2['ai_tp']}", f" / {y2['ai_n']}"), T("ov_eval_h"), "amber"),
          ("F3-B \u2212 " + T("m_RULES"), f"{h8['macro-F1 TTP T-novel']['diff']:+.3f}", f"macro-F1 TTP T-novel \u00b7 p Holm {h8['macro-F1 TTP T-novel']['p_holm']:.3f}", "green"),
          ("F3-B PR-AUC T-novel", f"{y2['f3_prauc']['v']:.3f}", f"{T('m_RULES')} {y2['rules_prauc']['v']:.3f}", "teal"),
          (T("ov_m_rule"), (f"{y2['with_rule']}", f" / {y2['n_alerts']}"), T("ov_no_rule_only")[:60] + "\u2026", "violet")])
    c1, c2 = st.columns([1, 1.3], gap="medium")
    with c1.container(border=True):
        ptitle(T("ov_eval_title"), T("ov_eval_h"))
        pr = D.precision_by_source(); er = []
        for s in list(D.SPLITS) + ["gop"]:
            for src in ("both", "ai"):
                v = pr[s][src]
                if not v["n"]: continue
                er.append({T("ov_col_split"): T("split_tong") if s == "gop" else short_split(s), T("ov_col_src"): src_name(src),
                           T("ov_col_tpn"): f"{v['tp']}/{v['n']}", T("ov_col_prec"): v["precision"],
                           T("ov_col_ci"): f"[{v['wilson']['lo']:.3f}; {v['wilson']['hi']:.3f}]"})
        st.dataframe(pd.DataFrame(er), hide_index=True, width="stretch",
                     column_config={T("ov_col_prec"): st.column_config.ProgressColumn(T("ov_col_prec"), min_value=0.0, max_value=1.0, format="%.3f")})
        note(T("ov_eval_note"))
    with c2.container(border=True):
        rs = [r for r in hr if r["family"] == 8]
        ptitle(T("e_holm8"), T("e_holm_h", n=len(rs)))
        st.dataframe(pd.DataFrame([{T("e_c_cmp"): r["cmp"], T("e_c_metric"): r["metric"], T("e_c_diff"): f"{r['diff']:+.3f} [{r['lo']:+.3f}; {r['hi']:+.3f}]",
                                    T("e_c_pholm"): r["p_holm"], T("e_c_concl"): T("e_sig") if r["sig"] else T("e_nsig")} for r in rs]
                                  ).pipe(styled, {T("e_c_concl"): {T("e_sig"): "green", T("e_nsig"): "gray"}}),
                     hide_index=True, width="stretch", column_config={T("e_c_pholm"): st.column_config.NumberColumn(T("e_c_pholm"), format="%.3f")})
        note(T("e_holm8_note"))
    c1, c2 = st.columns(2, gap="medium")
    oof, test, chosen = D.fusion_tables()
    with c1.container(border=True):
        ptitle(T("e_fusion"), T("e_fusion_h"))
        st.dataframe(pd.DataFrame([{T("e_c_variant"): f"{r['variant']}: {r['strategy']}", "macro-F1 TTP": r["macro_f1_ttp"], "PR-AUC": r["pr_auc"],
                                    "FPR hard_neg": r["fpr_hn"], "Recall": r["recall"]} for r in oof]), hide_index=True, width="stretch",
                     column_config={k: st.column_config.NumberColumn(k, format="%.3f") for k in ("macro-F1 TTP", "PR-AUC", "FPR hard_neg", "Recall")})
        note(T("e_fusion_note", s=chosen["strategy"], v="B", b=chosen["beta"]))
    with c2.container(border=True):
        ptitle(T("e_fusion_test"), T("e_fusion_test_h"))
        st.dataframe(pd.DataFrame([{T("e_c_strategy"): r["strategy"], T("e_c_novel_f1"): D.fmt(r["t_novel_f1"], sep="; "),
                                    T("e_c_novel_prauc"): D.fmt(r["t_novel_pr_auc"], sep="; "), T("e_c_macro_novel"): D.fmt(r["macro_novel"], sep="; "),
                                    T("e_c_hard_fp"): f"{int(r['t_hard_fp']['v'])} / 88"} for r in test]), hide_index=True, width="stretch")
        note(T("ov_no_rule_only"))

# ---------------- so sanh mo hinh ----------------
with tabs[3]:
    with st.container(border=True):
        ptitle(T("e_cmp"), T("e_cmp_h"))
        cols = {"t_clean_f1": T("e_c_clean_f1"), "t_novel_f1": T("e_c_novel_f1"), "t_novel_pr_auc": T("e_c_novel_prauc"),
                "macro_clean": T("e_c_macro_clean"), "macro_novel": T("e_c_macro_novel")}
        tab = [{T("e_c_model"): T(f"m_{r['key']}"), T("e_c_src"): f"step{r['step']}_results.json \u00b7 {r['src']}",
                **{lab: D.fmt(r[k], sep="; ", pm=" \u00b1 ") for k, lab in cols.items()},
                T("e_c_hard_fp"): f"{D.fmt(r['t_hard_fp'], nd=1, pm=' \u00b1 ') if 'sd' in r['t_hard_fp'] else int(r['t_hard_fp']['v'])} / 88"} for r in cmp_]
        st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch")
        note(T("e_cmp_note"))
    with st.container(border=True):
        ptitle(T("e_chart_macro"), T("e_chart_macro_h"))
        cd = pd.DataFrame([{"m": T(f"m_{r['key']}"), "v": r["macro_novel"]["v"],
                            "lo": r["macro_novel"].get("lo", r["macro_novel"]["v"] - r["macro_novel"].get("sd", 0)),
                            "hi": r["macro_novel"].get("hi", r["macro_novel"]["v"] + r["macro_novel"].get("sd", 0)), "f3": r["key"] == "F3B"} for r in cmp_])
        order = list(cd["m"])
        bars = alt.Chart(cd).mark_bar(height=20, cornerRadiusEnd=3).encode(
            y=alt.Y("m:N", sort=order, title=None), x=alt.X("v:Q", title="macro-F1 TTP T-novel", scale=alt.Scale(domain=[0, 1])),
            color=alt.condition("datum.f3", alt.value("#22c55e"), alt.value("#3d8bfd")),
            tooltip=[alt.Tooltip("m:N", title=T("e_c_model")), alt.Tooltip("v:Q", format=".3f"), alt.Tooltip("lo:Q", format=".3f"), alt.Tooltip("hi:Q", format=".3f")])
        err = alt.Chart(cd).mark_rule(color="#f3f6fb", strokeWidth=1.5).encode(y=alt.Y("m:N", sort=order), x="lo:Q", x2="hi:Q")
        txt = alt.Chart(cd).mark_text(align="left", dx=6, color="#c6d0e2").encode(y=alt.Y("m:N", sort=order), x="hi:Q", text=alt.Text("v:Q", format=".3f"))
        st.altair_chart((bars + err + txt).properties(height=270), width="stretch")

# ---------------- canh bao tap kiem thu ----------------
with tabs[4]:
    al = cached_alerts(); lab = cached_labels(); rows = D.queue_rows(al, eval_mode=True, labels=lab)
    stt = D.results(8)["explanation"]["stats"]
    c1, c2 = st.columns([2.4, 1], gap="medium")
    with c1.container(border=True):
        ptitle(T("res_alerts"), T("res_alerts_h"))
        f1, f2, f3 = st.columns(3)
        sp = f1.multiselect(T("q_splits"), list(D.SPLITS), format_func=short_split, placeholder=T("q_all"), key="res_al_split")
        rs_ = f2.multiselect(T("col_ket_qua"), ["Dung", "Nham"], format_func=lambda v: T(f"res_{v}"), placeholder=T("q_all"), key="res_al_res")
        srt = f3.selectbox(T("q_sort"), list(D.SORTS), format_func=lambda k: T(f"sort_{k}"), key="res_al_sort")
        q = D.sort_queue([r for r in D.filter_queue(rows, splits=sp) if not rs_ or r["ket_qua"] in rs_], srt)
        df = pd.DataFrame(q)
        if len(df):
            out = df.copy(); out["uu_tien"] = out["uu_tien"].map(prio_name); out["nguon"] = out["nguon"].map(src_name)
            out["tap"] = out["tap"].map(short_split); out["ket_qua"] = out["ket_qua"].map(lambda v: T(f"res_{v}")); out["bat_dau"] = out["bat_dau"].map(ts)
            cols = ["ma", "ket_qua", "uu_tien", "diem", "host", "bat_dau", "ttps", "ttp_that", "luat", "nguon", "tap", "window_id"]
            cfg = {c_: st.column_config.Column(T(f"col_{c_}")) for c_ in cols}
            cfg |= {"ma": st.column_config.TextColumn(T("col_ma"), pinned=True, width="small"),
                    "diem": st.column_config.ProgressColumn(T("col_diem"), min_value=0.8, max_value=1.1, format="%.4f", width="small")}
            sel = st.dataframe(styled(out[cols], {"uu_tien": tone_prio(), "ket_qua": tone_res()}), hide_index=True, width="stretch", height=420,
                               column_config=cfg, on_select="rerun", selection_mode="single-row", key="res_alerts_table")
            pk = sel.selection.rows if sel is not None and hasattr(sel, "selection") else []
            if st.button(T("q_open"), type="primary", icon=":material/open_in_new:", disabled=not pk, key="res_open"): goto_alert(out.iloc[pk[0]]["ma"])
        else:
            st.info(T("q_empty"))
        note(T("res_alerts_note"))
    with c2.container(border=True):
        ptitle(T("ov_tpfp"), "step8_results.json")
        st.dataframe(pd.DataFrame([{T("ov_col_split"): short_split(s), T("ov_col_n"): stt[s]["alerts"]["n"], T("ov_col_tp"): stt[s]["tp"]["n"],
                                    T("ov_col_fp"): stt[s]["fp"]["n"], T("ov_col_missed"): stt[s]["positives_missed"]} for s in D.SPLITS]),
                     hide_index=True, width="stretch")
        note(T("ov_tpfp_note"))
        st.write("")
        ptitle(T("ov_by_split"), T("ov_by_split_h"))
        ov = D.overview_counts(al)
        st.dataframe(pd.DataFrame([{T("ov_col_split"): T("split_tong") if s == "tong" else short_split(s), T("ov_col_n"): ov[s]["n"],
                                    T("ov_col_rule"): ov[s]["with_rule"], T("ov_col_both"): ov[s]["decision_source"].get("both", 0),
                                    T("ov_col_ai"): ov[s]["decision_source"].get("ai", 0)} for s in list(D.SPLITS) + ["tong"]]), hide_index=True, width="stretch")
        note(T("ov_split_note"))

# ---------------- tai lap + tieu chi ----------------
with tabs[5]:
    vi = D.verify_info(); c1, c2, c3 = st.columns(3, gap="medium")
    with c1.container(border=True):
        ptitle(T("res_repro"), T("res_repro_h"))
        v = vi["verify"]
        if v:
            st.markdown(badge(v["ket_qua"], "green" if v["ket_qua"] == "DAT" else "red") + " " + esc(T("res_repro_v", r=v["generated"][:16].replace("T", " "), k=v["dat"], t=v["thoi_gian_s"])),
                        unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{"#": k, T("e_c_metric"): x["ten"], T("e_c_concl"): T("e_pass") if x["dat"] else T("e_fail")} for k, x in v["kiem"].items()]
                                      ).pipe(styled, {T("e_c_concl"): {T("e_pass"): "green", T("e_fail"): "red"}}), hide_index=True, width="stretch")
        else:
            st.info(T("res_repro_none"))
        st.code("docker run --rm --network none vtguard:step9 verify", language="bash")
    with c2.container(border=True):
        ptitle(T("res_image"), "docker/image_info.json")
        im = (vi["image"] or {}).get("linux/amd64")
        if im: st.markdown(esc(T("res_image_v", tag=im["image"], plat="linux/amd64", mb=im["bytes"] / 1e6, sha=im["sha256"][:16])))
        else: st.caption("-")
        note(T("lv_honest"))
    with c3.container(border=True):
        ptitle(T("res_drift"), T("res_drift_h"))
        try:
            dr = D.load_json("reports/step9/live/drift_report.json"); m = next(x for x in dr["che_do"] if x["tool_mode"] == dr.get("che_do_mac_dinh", "orchestrator"))
            a_, b_ = m["a_trung_cua_so_canh_bao"], m["b_canh_bao_sai_phan_lanh_tinh"]
            st.markdown(esc(T("res_drift_v", a=a_["offline_duoc_truc_tiep_phu"], b=a_["offline_cua_so_canh_bao"], c=a_["truc_tiep_giao_offline"], d=a_["truc_tiep_canh_bao"],
                              e=b_["truc_tiep_canh_bao_sai"], f=b_["truc_tiep_cua_so_lanh_tinh"], g=b_["offline_canh_bao_sai_cung_dot"], h=b_["offline_cua_so_lanh_tinh_cung_dot"])))
        except (OSError, StopIteration, KeyError):
            st.caption("-")
    cc = st.columns(3, gap="medium")
    for col, (step, items) in zip(cc, acc.items()):
        with col.container(border=True):
            ptitle(T("e_acc_step", s=step), T("e_acc_h", k=sum(i["pass"] for i in items), n=len(items)))
            for i in items:
                st.markdown(f'<div style="margin:0 0 9px">{badge(T("e_pass") if i["pass"] else T("e_fail"), "green" if i["pass"] else "red")} '
                            f'<b>{i["id"]}.</b> {esc(i["criterion"])}<div class="vtg-note">{esc(i["evidence"])}</div></div>', unsafe_allow_html=True)
