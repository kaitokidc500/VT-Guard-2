"""Phan B - trang Luat Sigma tu sinh (YC1 cua de tai, docs/STEP9-BRIEF.md muc 3.5): 11 luat (RIPPER, chi Train), thong tin quy nap
(Train / OOF), TP / FP theo tap test (step7_results.json per_rule), provenance, cong chat luong, YAML + tai ve (tung luat / ca bo .zip),
canh bao F3-B tren tap test dan chieu luat."""
import io
import zipfile

import pandas as pd
import streamlit as st

import data as D
from common import T, badge, cached_alerts, esc, goto_alert, header, kpis, kv, note, ptitle, short_split, styled

ev = header("research", T("r_title"), T("r_intro"))
al = cached_alerts(); rows = D.rule_rows(al, eval_mode=ev); info = D.rule_engine_info()
n_bin = sum(r["dich"] == "bin" for r in rows)
kpis([(T("r_k_rules"), str(len(rows)), T("r_k_rules_s", b=n_bin, t=len(rows) - n_bin), "blue"),
      (T("r_k_ttp"), str(len({r["dich"] for r in rows if r["dich"] != "bin"})), ", ".join(sorted({r["dich"] for r in rows if r["dich"] != "bin"})), "violet"),
      (T("r_k_corr"), str(sum(r["loai"] == "correlation" for r in rows)), T("r_k_corr_s"), "teal"),
      (T("r_k_alerts"), (str(sum(bool(a["rule_ids"]) for a in al)), f" / {len(al)}"), T("r_k_alerts_s"), "green"),
      (T("r_k_rejected"), str(sum(info["rejected"].values())), ", ".join(f"{k}: {v}" for k, v in info["rejected"].items()), "gray"),
      (T("r_k_engine"), info["engine"]["chosen"].upper(), T("r_k_engine_s", m=info["engine"]["macro_f1_ttp_oof_by_engine"]["ripper"]["macro"]), "amber")])

with st.container(border=True):
    head = st.columns([3, 1])
    with head[0]: ptitle(T("r_table"), T("r_table_h"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for r in rows: z.writestr(f"{r['id']}.yml", D.sigma_text(r["id"]))
    head[1].download_button(T("r_download_all"), buf.getvalue(), file_name="vtguard_sigma_rules.zip", mime="application/zip",
                            icon=":material/folder_zip:", width="stretch")
    df = pd.DataFrame(rows)
    cols = ["id", "dich", "vi_tu", "loai", "muc", "train_ho_tro", "oof_precision", "oof_cua_so", "fold_lap_lai", "canh_bao"]
    if ev:
        for s in D.SPLITS:
            df[f"tpfp_{s}"] = [f"{tp}/{fp}" for tp, fp in zip(df[f"tp_{s}"], df[f"fp_{s}"])]
        cols += [f"tpfp_{s}" for s in D.SPLITS]
    else:
        cols += [f"khop_{s}" for s in D.SPLITS]
    cfg = {c: st.column_config.Column(T(f"r_col_{c}")) for c in ("id", "dich", "vi_tu", "loai", "muc", "train_ho_tro", "oof_cua_so", "fold_lap_lai", "canh_bao")}
    cfg |= {"id": st.column_config.TextColumn(T("r_col_id"), pinned=True), "vi_tu": st.column_config.TextColumn(T("r_col_vi_tu"), width="medium"),
            "oof_precision": st.column_config.NumberColumn(T("r_col_oof_precision"), format="%.2f"),
            "canh_bao": st.column_config.ProgressColumn(T("r_col_canh_bao"), min_value=0, max_value=int(df["canh_bao"].max()), format="%d")}
    for s in D.SPLITS:
        cfg[f"khop_{s}"] = st.column_config.NumberColumn(T("r_col_khop", s=short_split(s)), format="%d")
        cfg[f"tpfp_{s}"] = st.column_config.TextColumn(T("r_col_tpfp", s=short_split(s)))
    df["loai"] = df["loai"].map(lambda v: T(f"r_kind_{'corr' if v == 'correlation' else 'single'}"))
    st.dataframe(styled(df[cols], {"muc": {"high": "red", "medium": "amber"}}), hide_index=True, width="stretch", height=36 * (len(df) + 1) + 4, column_config=cfg)
    note(T("r_table_note_eval") if ev else T("r_table_note"))

ids = [r["id"] for r in rows]
c1, c2 = st.columns([1.35, 1], gap="medium")
with c1.container(border=True):
    ptitle(T("r_view"), T("r_view_h"))
    rid = st.selectbox(T("r_pick"), ids, key="rule_pick", format_func=lambda i: f"{i} \u00b7 {next(r['dich'] for r in rows if r['id'] == i)}")
    row = next(r for r in rows if r["id"] == rid); prov, meta = D.rule_provenance(rid); docs = D.sigma_docs(rid); top = docs[-1]
    t1, t2, t3 = st.tabs([T("r_tab_yaml"), T("r_tab_prov"), T("r_tab_alerts")])
    with t1:
        st.markdown(f'{badge(top.get("level", ""), "red" if top.get("level") == "high" else "amber")} {badge(T("r_kind_corr") if "correlation" in top else T("r_kind_single"), "teal" if "correlation" in top else "blue")} '
                    f'{"".join(badge(t, "violet") for t in top.get("tags", []))}', unsafe_allow_html=True)
        st.code(D.sigma_text(rid), language="yaml", height=420)
        st.download_button(T("r_download"), D.sigma_text(rid).encode("utf-8"), file_name=f"{rid}.yml", mime="application/x-yaml", icon=":material/download:")
    with t2:
        st.markdown(kv([(T("r_pred"), f'<span class="vtg-mono">{esc(" AND ".join(prov["predicates"]))}</span>'),
                        (T("r_semantics"), esc(prov["semantics"])), (T("r_target"), esc(prov["target"]) + (f" ({esc(D.MITRE[prov['target']][1])})" if prov["target"] in D.MITRE else "")),
                        (T("r_source"), esc(meta["source"])), (T("r_engine"), esc(meta["engine"]["desc"])),
                        (T("r_train"), esc(T("r_train_v", n=prov["train"]["support"], tp=prov["train"]["tp"], fp=prov["train"]["fp"]))),
                        (T("r_oof"), esc(T("r_oof_v", p=prov["oof"]["precision"], n=prov["oof"]["tp"] + prov["oof"]["fp"]))),
                        (T("r_folds"), esc(f"{len(prov['oof']['folds_rediscovered'])}/5 (fold {', '.join(str(f) for f in prov['oof']['folds_rediscovered'])})")),
                        (T("r_support_win"), esc(T("r_support_win_v", n=len(prov["support_windows"]), s=len({w.split(':')[0] for w in prov["support_windows"]})))),
                        (T("r_approved"), esc(f"{meta['approved']} (commit {info['approved_commit']})"))]), unsafe_allow_html=True)
        st.write("")
        ptitle(T("r_gates"), T("r_gates_h"))
        st.dataframe(pd.DataFrame([{T("r_gate"): k, T("r_gate_desc"): v, T("r_gate_rej"): meta["n_rejected_by_gate"].get(k, 0)} for k, v in meta["gates"].items()]),
                     hide_index=True, width="stretch")
    with t3:
        rel = sorted([a for a in al if any(r["id"] == rid for r in a["rule_ids"])], key=lambda a: a["code"])
        if rel:
            rd = pd.DataFrame([{T("col_ma"): a["code"], T("col_host"): a["host"], T("col_bat_dau"): a["t0"][:19].replace("T", " "),
                                T("col_diem"): a["score"], T("col_ttps"): ", ".join(a["ttps"]), T("col_su_co"): a["incident"]} for a in rel])
            sel = st.dataframe(rd, hide_index=True, width="stretch", height=300, on_select="rerun", selection_mode="single-row", key=f"rule_alerts_{rid}",
                               column_config={T("col_diem"): st.column_config.NumberColumn(T("col_diem"), format="%.4f")})
            pr = sel.selection.rows if sel is not None and hasattr(sel, "selection") else []
            if st.button(T("q_open"), type="primary", icon=":material/open_in_new:", disabled=not pr, key="rule_open"): goto_alert(rd.iloc[pr[0]][T("col_ma")])
        else:
            st.info(T("r_no_alerts"))
        note(T("r_alerts_note"))

with c2.container(border=True):
    ptitle(T("r_split_stats"), T("r_split_stats_h"))
    sd = pd.DataFrame([{T("col_tap"): short_split(s), T("r_col_khop_plain"): row[f"khop_{s}"],
                        **({"TP": row[f"tp_{s}"], "FP": row[f"fp_{s}"]} if ev else {}),
                        T("r_col_canh_bao"): sum(1 for a in al if a["split"] == s and any(r["id"] == rid for r in a["rule_ids"]))} for s in D.SPLITS])
    st.dataframe(sd, hide_index=True, width="stretch")
    note(T("r_split_note"))
    st.write("")
    ptitle(T("r_cov"), T("r_cov_h"))
    st.markdown(f'<div class="vtg-strip eval" style="margin:2px 0 8px">{esc(T("r_cov_gap", t=", ".join(meta["ttp_without_rule"]["ttps"])))}</div>', unsafe_allow_html=True)
    with st.expander(T("r_cov_raw"), icon=":material/notes:"): st.caption(meta["ttp_without_rule"]["note"])
    st.write("")
    ptitle(T("r_sigma"), T("r_sigma_h"))
    sg = info["sigma"]
    st.markdown(kv([(T("r_sigma_tool"), esc(sg["tool"])),
                    (T("r_sigma_val"), badge(T("r_sigma_val_v", f=sg["files"], d=sg["docs"], e=sg["errors"], i=sg["issues"]), "green" if not sg["errors"] else "red")),
                    (T("r_sigma_gen"), esc(T("r_sigma_gen_v") if sg["generate_false"] else "-")),
                    (T("r_sigma_eq"), badge(T("r_sigma_eq_v", n=sg["n_equiv"], m=sg["train_mismatch"], t=sg["test_mismatch"]),
                                            "green" if not sg["train_mismatch"] + sg["test_mismatch"] else "red"))]), unsafe_allow_html=True)
    with st.expander(T("r_dev"), icon=":material/info:"):
        for d in info["deviations"]: st.markdown(f"**{d['id']}.** {d['what']}  \n<span class='vtg-muted'>{esc(d['why'])}</span>", unsafe_allow_html=True)
