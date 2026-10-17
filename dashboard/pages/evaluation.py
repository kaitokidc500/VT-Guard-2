"""Trang Danh gia (CHI che do danh gia): bang so sanh mo hinh tren test, chuoi ablation (Buoc 5 / 6 / 8), paired bootstrap + Holm,
tieu chi chap nhan. Moi so lieu doc tu reports/step{5,6,7,8}_results.json, khong tinh lai."""
import altair as alt
import pandas as pd
import streamlit as st

import data as D
from common import T, badge, esc, header, kpis, lock_panel, note, ptitle, styled

ev = header(T("navsec_eval"), T("e_title"), T("e_intro"))
if not ev:
    lock_panel(); st.stop()

cmp_ = D.model_comparison(); f3 = next(r for r in cmp_ if r["key"] == "F3B"); hr = D.holm_rows(); acc = D.acceptance()
kpis([(T("e_k_macro"), f"{f3['macro_novel']['v']:.3f}", T("e_k_macro_s", lo=f3["macro_novel"]["lo"], hi=f3["macro_novel"]["hi"]), "blue"),
      (T("e_k_prauc"), f"{f3['t_novel_pr_auc']['v']:.3f}", T("e_k_prauc_s", lo=f3["t_novel_pr_auc"]["lo"], hi=f3["t_novel_pr_auc"]["hi"]), "teal"),
      (T("e_k_fp"), (f"{f3['t_hard_fp']['v']:.0f}", " / 88"), T("e_k_fp_s"), "amber"),
      (T("e_k_sig"), (str(sum(r["sig"] for r in hr)), f" / {len(hr)}"), T("e_k_sig_s"), "violet"),
      (T("e_k_acc"), (str(sum(c["pass"] for v in acc.values() for c in v)), f" / {sum(len(v) for v in acc.values())}"), T("e_k_acc_s"), "green")])

tabs = st.tabs([T("e_tab_cmp"), T("e_tab_abl"), T("e_tab_holm"), T("e_tab_acc")], key="eval_tab")

with tabs[0]:
    with st.container(border=True):
        ptitle(T("e_cmp"), T("e_cmp_h"))
        cols = {"t_clean_f1": T("e_c_clean_f1"), "t_novel_f1": T("e_c_novel_f1"), "t_novel_pr_auc": T("e_c_novel_prauc"),
                "macro_clean": T("e_c_macro_clean"), "macro_novel": T("e_c_macro_novel")}
        tab = [{T("e_c_model"): T(f"m_{r['key']}"), T("e_c_src"): f"step{r['step']}_results.json \u00b7 {r['src']}",
                **{lab: D.fmt(r[k], sep="; ", pm=" \u00b1 ") for k, lab in cols.items()},
                T("e_c_hard_fp"): f"{D.fmt(r['t_hard_fp'], nd=1, pm=' \u00b1 ') if 'sd' in r['t_hard_fp'] else int(r['t_hard_fp']['v'])} / 88"} for r in cmp_]
        st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch")
        note(T("e_cmp_note"))
    c1, c2 = st.columns([1.6, 1], gap="medium")
    with c1.container(border=True):
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
    with c2.container(border=True):
        ptitle(T("e_chart_fp"), T("e_chart_fp_h"))
        fd = pd.DataFrame([{"m": T(f"m_{r['key']}"), "fp": r["t_hard_fp"]["v"]} for r in cmp_])
        ch = alt.Chart(fd).mark_bar(height=20, cornerRadiusEnd=3, color="#f5a524").encode(
            y=alt.Y("m:N", sort=order, title=None), x=alt.X("fp:Q", title=T("e_c_hard_fp")), tooltip=["m:N", alt.Tooltip("fp:Q", format=".1f")])
        st.altair_chart((ch + ch.mark_text(align="left", dx=4, color="#c6d0e2").encode(text=alt.Text("fp:Q", format=".1f"))).properties(height=270), width="stretch")

with tabs[1]:
    with st.container(border=True):
        ptitle(T("e_chain"), T("e_chain_h"))
        labs = {"oof_macro_f1_ttp": "OOF macro-F1 TTP", "oof_pr_auc_bin": "OOF PR-AUC", "oof_fpr_hard_negative": "OOF FPR hard_neg",
                "test_t_novel_f1": "T-novel F1", "test_t_novel_pr_auc": "T-novel PR-AUC", "test_macro_f1_clean": "macro-F1 clean",
                "test_macro_f1_novel": "macro-F1 novel", "test_t1654_novel": "T1654 novel", "test_t_hard_fp": "T-hard FP/88"}
        st.dataframe(pd.DataFrame([{T("e_c_code"): r["code"], T("e_c_cfg"): r["desc"], "seed": r["n_seeds"],
                                    **{v: D.fmt(r[k], nd=1 if k == "test_t_hard_fp" else 3, pm=" \u00b1 ") for k, v in labs.items()}} for r in D.ablation_chain()]),
                     hide_index=True, width="stretch")
        note(T("e_chain_note"))
    c1, c2 = st.columns(2, gap="medium")
    with c1.container(border=True):
        ptitle(T("e_feat"), T("e_feat_h"))
        fa = D.feature_ablation(); fams = list(dict.fromkeys(r["family"] for r in fa))
        st.dataframe(pd.DataFrame([{T("e_c_family"): f, **{f"({v}) macro-F1 novel": D.fmt(next(r for r in fa if r["family"] == f and r["variant"] == v)["macro_novel"], nd=2, sep="; ", pm=" \u00b1 ")
                                                          for v in ("a", "b", "c'")},
                                    **{f"({v}) FP T-hard": D.fmt(next(r for r in fa if r["family"] == f and r["variant"] == v)["t_hard_fp"], nd=1, pm=" \u00b1 ") for v in D.ABL_VARIANTS}}
                                   for f in fams]), hide_index=True, width="stretch")
        note(T("e_feat_note"))
    with c2.container(border=True):
        ptitle(T("e_fusion"), T("e_fusion_h"))
        oof, test, chosen = D.fusion_tables()
        st.dataframe(pd.DataFrame([{T("e_c_variant"): f"{r['variant']}: {r['strategy']}", "macro-F1 TTP": r["macro_f1_ttp"], "PR-AUC": r["pr_auc"],
                                    "FPR hard_neg": r["fpr_hn"], "Recall": r["recall"]} for r in oof]), hide_index=True, width="stretch",
                     column_config={k: st.column_config.NumberColumn(k, format="%.3f") for k in ("macro-F1 TTP", "PR-AUC", "FPR hard_neg", "Recall")})
        note(T("e_fusion_note", s=chosen["strategy"], v="B", b=chosen["beta"]))
    with st.container(border=True):
        ptitle(T("e_fusion_test"), T("e_fusion_test_h"))
        st.dataframe(pd.DataFrame([{T("e_c_strategy"): r["strategy"], T("e_c_clean_f1"): D.fmt(r["t_clean_f1"], sep="; "), T("e_c_novel_f1"): D.fmt(r["t_novel_f1"], sep="; "),
                                    T("e_c_novel_prauc"): D.fmt(r["t_novel_pr_auc"], sep="; "), T("e_c_macro_clean"): D.fmt(r["macro_clean"], sep="; "),
                                    T("e_c_macro_novel"): D.fmt(r["macro_novel"], sep="; "), T("e_c_hard_fp"): f"{int(r['t_hard_fp']['v'])} / 88"} for r in test]),
                     hide_index=True, width="stretch")

with tabs[2]:
    for fam in (6, 8):
        with st.container(border=True):
            rs = [r for r in hr if r["family"] == fam]
            ptitle(T(f"e_holm{fam}"), T("e_holm_h", n=len(rs)))
            st.dataframe(pd.DataFrame([{T("e_c_cmp"): r["cmp"], T("e_c_metric"): r["metric"],
                                        T("e_c_diff"): f"{r['diff']:+.3f} [{r['lo']:+.3f}; {r['hi']:+.3f}]", "p": r["p"], T("e_c_pholm"): r["p_holm"],
                                        T("e_c_concl"): T("e_sig") if r["sig"] else T("e_nsig")} for r in rs]).pipe(styled, {T("e_c_concl"): {T("e_sig"): "green", T("e_nsig"): "gray"}}),
                         hide_index=True, width="stretch",
                         column_config={"p": st.column_config.NumberColumn("p", format="%.3f"), T("e_c_pholm"): st.column_config.NumberColumn(T("e_c_pholm"), format="%.3f")})
            note(T(f"e_holm{fam}_note"))

with tabs[3]:
    c = st.columns(3, gap="medium")
    for col, (step, items) in zip(c, acc.items()):
        with col.container(border=True):
            ptitle(T("e_acc_step", s=step), T("e_acc_h", k=sum(i["pass"] for i in items), n=len(items)))
            for i in items:
                st.markdown(f'<div style="margin:0 0 9px">{badge(T("e_pass") if i["pass"] else T("e_fail"), "green" if i["pass"] else "red")} '
                            f'<b>{i["id"]}.</b> {esc(i["criterion"])}<div class="vtg-note">{esc(i["evidence"])}</div></div>', unsafe_allow_html=True)
