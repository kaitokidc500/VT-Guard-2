#!/usr/bin/env python3
"""VT-Guard Buoc 7 moc 2 - bang chi-luat canh B0 / B1 / B2 / VT-Seq-ens, FP/TP tung luat, so voi B0 -> reports/step7/m2_eval.md.
Chi doc ket qua da sinh (reports/step7/eval/rules.json, per_rule.json, sigma_validation.json, step5/6 eval). Khong chinh luat.
Chay: python src/rules/m2_report.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines"): sys.path.insert(0, os.path.join(HERE, d))
from summary import tables, load          # noqa: E402
from evaluate import TTPS                 # noqa: E402

S7 = os.path.join("reports", "step7")
MODELS = ["b0_wazuh", "b1_tfidf_b", "b2_lgbm_a", "vtseq_M3_ens", "rules"]

def J(*p): return json.load(open(os.path.join(*p), encoding="utf-8"))

def main():
    R = load(".", "rules", ()); r = R[0]; per = J(S7, "per_rule.json"); V = J(S7, "sigma_validation.json"); P = J(S7, "rules_provenance.json")
    eq = r["sigma_equivalence"]
    L = ["# VT-Guard Buoc 7 moc 2 - Sigma + bo phat hien chi-luat tren 3 tap test", "",
         "Luat: 11 luat da duyet (RIPPER tren Train, `reports/step7/rules_provenance.json`), KHONG chinh theo test. "
         "Nguong co dinh 0.5 dat truoc (nhi phan = co luat khop; da nhan = hop TTP cua luat theo TTP khop). "
         "Diem p = max precision OOF cua luat khop (cho Buoc 8). Du doan Train la IN-SAMPLE.", "",
         "## 1. Sigma", "",
         f"- 11 file `rules/sigma/<id>.yml` (10 luat don + 1 correlation `temporal` cho VTR-T1018-02 gom 2 luat con), "
         f"logsource `process_creation` (Sysmon 1 / Security 4688), token -> `CommandLine|re` co bien token, image -> `Image|endswith`; "
         f"custom field `vtguard_provenance` tro ve provenance.",
         f"- Validate: **{V['tool']}** -> " + ("0 loi, 0 canh bao validator o ca 11 file" if all(not x["errors"] and not x["validator_issues"] for x in V["files"].values())
                                               else str({k: x for k, x in V["files"].items() if x["errors"] or x["validator_issues"]})) + ".",
         f"- Matcher noi bo doc YAML Sigma (`src/rules/apply.py`) == vi tu luat tren Train: "
         f"{'0 lech o 11/11 luat, tap cua so khop trung provenance' if all(v['train_mismatch'] == 0 and v['train_support_equal_provenance'] for v in eq.values()) else eq}. "
         "(Chan doan them tren 3 tap test: 0 lech.) Ghi chu: log Wazuh giu dau nhay escape `\\\"`; regex token chap nhan `\\\"` lam bien phai "
         "(phat hien do kiem tra tren Train lech o token `controllers`).", "",
         "## 2. Chi-luat canh B0 / B1 TF-IDF (b) / B2 (a) / VT-Seq-ens", ""]
    L.append(tables(".", MODELS, (), (), (1337, 7, 42, 2024, 99)))
    L += ["## 3. TP / FP theo tung luat (TP = cua so mang dung muc tieu cua luat; luat nhi phan: cua so doc hai)", "",
          "| Luat | Muc tieu | Vi tu | Train TP/FP (in-sample) | T-clean TP/FP | T-hard FP/88 (chu ky) | T-novel TP/FP |", "|---|---|---|---|---|---|---|"]
    pred = {x["id"]: " AND ".join(f"`{p}`" for p in x["predicates"]) for x in P["rules"]}
    for k, v in per.items():
        sig = ", ".join(f"{a}: {b}" for a, b in v["t_hard_fp_by_signature"].items()) or "-"
        L.append(f"| {k} | {v['target']} | {pred[k]} | {v['train']['tp']}/{v['train']['fp']} | {v['t_clean']['tp']}/{v['t_clean']['fp']} | "
                 f"{v['t_hard']['fp']} ({sig}) | {v['t_novel']['tp']}/{v['t_novel']['fp']} |")
    b0 = load(".", "b0_wazuh", ())[0]
    L += ["", "## 4. So voi B0 (luat Wazuh co san) - F1 / recall theo TTP", "",
          "| TTP | B0 F1 T-clean | Chi-luat F1 T-clean (recall) | B0 F1 T-novel | Chi-luat F1 T-novel (recall) | Luat theo TTP | B0 mu? |", "|---|---|---|---|---|---|---|"]
    rules_by_t = {}
    for x in P["rules"]: rules_by_t.setdefault(x["target"], []).append(x["id"])
    for t in TTPS:
        g = lambda m, sp, k: m["splits"][sp]["ttp_tuned"]["per_ttp"][t][k]["point"]
        blind = g(b0, "t_clean", "f1") == 0 and g(b0, "t_novel", "f1") == 0
        L.append(f"| {t} | {g(b0, 't_clean', 'f1'):.2f} | {g(r, 't_clean', 'f1'):.2f} ({g(r, 't_clean', 'recall'):.2f}) | {g(b0, 't_novel', 'f1'):.2f} | "
                 f"{g(r, 't_novel', 'f1'):.2f} ({g(r, 't_novel', 'recall'):.2f}) | {', '.join(rules_by_t.get(t, [])) or '- (khong co)'} | {'CO' if blind else 'khong'} |")
    S = r["splits"]
    L += ["", "**Tom tat:**",
          f"- Chi-luat: T-hard **{S['t_hard']['tuned']['fp']}/88 FP** (B0 17/88); T-clean F1 {S['t_clean']['tuned']['f1']['point']:.3f}, T-novel F1 "
          f"{S['t_novel']['tuned']['f1']['point']:.3f} (recall {S['t_novel']['tuned']['recall']['point']:.3f}); T1003.003 phien T-novel "
          f"{S['t_novel']['tuned']['ntds_session_recall']['binary']['detected']}/6 nhi phan, {S['t_novel']['tuned']['ntds_session_recall']['ttp_label']['detected']}/6 nhan TTP.",
          "- B0 mu T1016 / T1018 / T1654 / T1003.003 (F1 = 0) -> luat tu sinh co luat theo TTP cho T1018, T1654, T1003.003; T1016 va T1087.002 "
          "chi phu o muc nhi phan (khong luat theo TTP qua cong - phien mixed).",
          "", "**Han che (ghi lai, KHONG chinh luat):**",
          f"- **VTR-T1654-01 (`cmd~'system'`) khop nham {per['VTR-T1654-01']['t_novel']['fp']} cua so T-novel** (DINH CHINH Buoc 8: ban truoc ghi "
          "sai la ca hai deu doc hai): 1 cua so LANH TINH (`auditpol /get /subcategory:\"System Integrity\"`, event nen trong phien attack) - "
          "day la FP nhi phan duy nhat cua chi-luat tren T-novel (FPR 1/95) - va 1 cua so doc hai khong mang T1654. Token chung `system` "
          "(tu bo loc `*SYSTEM*` cua get-eventlog) khop ca lenh quan tri. Ghi lai, khong chinh luat.",
          f"- VTR-T1003003-01 / VTR-BIN-02 (`cmd~'create'`) khop ca bien the vssadmin `create shadow` cua ntds2v ({per['VTR-T1003003-01']['t_novel']['tp']} cua so T-novel) - "
          "nho token chung chung, khong phai luat duoc thiet ke cho bien the nay; ngoai lab co the khop `schtasks /create`, `sc create`.",
          "- Luat quy nap tu 2 host / 1 domain; coverage gap da biet (dataset card muc 9); T1003.003 test nho (6 phien).",
          "- Du doan Train cua chi-luat la in-sample: Buoc 8 khong duoc dung lam OOF.", ""]
    with open(os.path.join(S7, "m2_eval.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    print("\n".join(L))

if __name__ == "__main__":
    main()
