#!/usr/bin/env python3
"""VT-Guard Buoc 7 - tong hop reports/step7_report.md + reports/step7_results.json (brief muc 7) + kiem tieu chi muc 8.
Chi doc ket qua da sinh; chay lai src/rules/test_induce.py lam bang chung. Khong chinh luat.
Chay: python src/rules/step7_report.py
"""
import glob, json, os, subprocess, sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines"): sys.path.insert(0, os.path.join(HERE, d))
from summary import tables, load                               # noqa: E402
from evaluate import check_dataset, TTPS, SPLITS                # noqa: E402
import predicates as Pd                                         # noqa: E402

S7 = os.path.join("reports", "step7")
APPROVED_COMMIT = "6b56a7a"          # commit moc 1: 11 luat duoc nguoi dung duyet

def J(*p): return json.load(open(os.path.join(*p), encoding="utf-8"))

def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True)

def acceptance(P, r, V, oof):
    rows = []
    t = subprocess.run([sys.executable, os.path.join(HERE, "test_induce.py")], capture_output=True, text=True)
    res = {l[7:].split(" - ")[0].strip(): l.startswith("[PASS]") for l in t.stdout.splitlines() if l.startswith("[PASS]") or l.startswith("[FAIL]")}
    last = next((l for l in t.stdout.splitlines() if l.startswith("KET QUA")), "")
    pick = lambda pre: all(v for k, v in res.items() if k.startswith(pre)) and any(k.startswith(pre) for k in res)
    ds = check_dataset(".")
    unchanged = git("diff", "--quiet", APPROVED_COMMIT, "--", "reports/step7/rules_provenance.json", "src/rules/induce.py", "src/rules/predicates.py").returncode == 0
    ok1 = all(ds.values()) and pick("1") and unchanged
    rows.append((1, "Checksum dataset-v1.2 khop; luat chi quy nap tu Train; test chi de do", ok1,
                 f"check_dataset {all(ds.values())}; test 1a-1c (split test chi bam sha, windows.jsonl chi parse dong Train) {pick('1')}; "
                 f"luat + code quy nap khong doi tu commit duyet {APPROVED_COMMIT}: {unchanged}; nguong chi-luat co dinh 0.5 dat truoc test"))
    viol = [x["id"] for x in P["rules"] for a in x["atoms"] if Pd.forbidden_reason((a[0], tuple(a[1]) if a[0] == "imgtok" else a[1]))]
    full = all(x["support_windows"] and x["oof"] and x["source"]["origin_rules"] and x["related_attention_seeds"] is not None for x in P["rules"])
    ok2 = full and not viol and pick("3e") and pick("5")
    rows.append((2, "Moi luat co provenance day du va KHONG chua vi tu cam (assert tu dong, 0 vi pham)", ok2,
                 f"provenance day du {full}; vi pham danh sach cam {len(viol)}; test 3e (S1-S5 + S4-auto, 0 vi pham) {pick('3e')}; test 5 {pick('5')}"))
    sig_ok = all(not x["errors"] and not x["validator_issues"] for x in V["files"].values())
    eq_ok = all(v["train_mismatch"] == 0 and v["train_support_equal_provenance"] for v in r["sigma_equivalence"].values())
    ok3 = sig_ok and eq_ok and pick("4")
    rows.append((3, "Sigma hop le cu phap; matcher noi bo == dieu kien luat/engine tren Train", ok3,
                 f"{V['tool']}: 11/11 file 0 loi 0 canh bao {sig_ok}; matcher doc YAML Sigma == vi tu luat tren Train (0 lech, support trung) {eq_ok}; "
                 f"test 4a-4c (matcher == RIPPER, ruleset doc lai == wittgenstein.predict) {pick('4')}"))
    have = all(s in r["splits"] for s in ("t_clean", "t_hard", "t_novel"))
    rows.append((4, "Bang chi-luat tren ca 3 tap test + so voi B0 + so voi AI", have, "muc 3-5 bao cao nay (B0, B1 TF-IDF (b), B2 (a), VT-Seq-ens)"))
    files = [os.path.join("reports", "preds", f"rules_{s}.jsonl") for s in SPLITS] + [os.path.join("reports", "preds", "rules_oof_train.jsonl")]
    rows.append((5, "reports/preds/rules_<split>.jsonl san cho Buoc 8", all(os.path.exists(f) for f in files),
                 "rules_{train,t_clean,t_hard,t_novel}.jsonl + rules_oof_train.jsonl (OOF theo fold; rules_train la in-sample)"))
    g = P["n_rejected_by_gate"]
    rows.append((6, "Bao so luat loai theo tung cong, gom cong vi tu cam", "G1" in g and g["G1"] > 0, f"{g}; atom bi chan o tang dac trung {P['features']['n_atoms_blocked_forbidden']}"))
    return rows, last

def main():
    tz = timezone(timedelta(hours=7))
    P = J(S7, "rules_provenance.json"); r = load(".", "rules", ())[0]; per = J(S7, "per_rule.json"); V = J(S7, "sigma_validation.json")
    oof = J(S7, "rules_oof.json"); b0 = load(".", "b0_wazuh", ())[0]
    acc, test_line = acceptance(P, r, V, oof)
    S = r["splits"]
    gen = datetime.now(tz).replace(microsecond=0).isoformat()
    L = ["# VT-Guard - Bao cao Buoc 7: Auto Rule Engine (luat tu sinh -> Sigma)", "",
         f"Sinh tu dong boi `src/rules/step7_report.py` luc {gen}. So lieu: `reports/step7_results.json`; chi tiet: `reports/step7/` "
         "(m1_rules.md, rules_provenance.json, m2_eval.md, per_rule.json, sigma_validation.json, rules_oof.json, eval/rules.json); "
         "Sigma: `rules/sigma/*.yml`; du doan cho Buoc 8: `reports/preds/rules_*.jsonl`.", "",
         "## 0. Tom tat", "",
         f"- **11 luat** quy nap tu dong CHI tu Train (RIPPER, dataset-v1.2), moi luat co provenance va file Sigma hop le (pySigma). "
         f"Nhanh chi-luat: **T-hard {S['t_hard']['tuned']['fp']}/88 FP** (B0 17/88), T-clean F1 {S['t_clean']['tuned']['f1']['point']:.3f}, "
         f"T-novel F1 {S['t_novel']['tuned']['f1']['point']:.3f} (recall {S['t_novel']['tuned']['recall']['point']:.3f}); kem AI ve recall va da nhan "
         f"(macro-F1 TTP T-novel {S['t_novel']['ttp_tuned']['macro_f1']['point']:.2f} vs VT-Seq-ens 0.82) - nhu brief du kien; gia tri: minh bach + FPR thap.",
         "- B0 (luat Wazuh) mu hoan toan 4 TTP (T1016, T1018, T1654, T1003.003); luat tu sinh phu 3 trong so do: T1018, T1654, T1003.003. "
         "T1016 va T1087.002 khong co luat theo TTP (phien mixed) "
         "-> hai TTP nay dua vao AI.",
         "- Luat KHONG duoc chinh sau khi cham test (luat + code quy nap khong doi tu commit duyet " + APPROVED_COMMIT + ").", "",
         "## 1. Phuong phap va sai khac so voi brief", "",
         "Atom = 'cua so co >= 1 event thoa ...' tren telemetry quan sat duoc (image, parent, event_id, token lenh norm_cmd, image + token "
         "cung event). Hai luot: khong rang buoc (moi atom - de do cong vi tu cam) va rang buoc (bo atom cam). Engine chon bang macro-F1 TTP "
         "OOF (CV 5 fold theo nhom): " + "; ".join(f"{e} {v['macro']}" for e, v in P["engine"]["macro_f1_ttp_oof_by_engine"].items()) +
         f" -> **{P['engine']['chosen']}**. Luat = literal co mat cua tung luat RIPPER (rut gon); OOF = luat duoc quy nap lai tren 4/5 "
         "Train va do tren 1/5 con lai. Cong: G0 khong literal co mat, G1 vi tu cam, G2 Sigma, G3 support >= 10 + precision OOF >= 0.9 tren "
         ">= 10 cua so OOF, G4 khu trung.", "", "**Sai khac so voi brief (ly do):**", ""]
    for d in P["deviations_from_brief"]: L.append(f"{d['id']}. **{d['what']}** - {d['why']}.")
    L += ["", "## 2. Danh sach 11 luat va provenance tom tat", "",
          "| id | Muc tieu | Vi tu | Support Train (TP/FP) | Prec OOF (TP/FP) | Fold tai lap | Phien Train khop | Luat RIPPER goc | Hat giong attention | Sigma |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for x in P["rules"]:
        sd = "; ".join(f"{k}: " + ", ".join(f"{t} {v['lift']}" for t, v in d.items() if v["lift"] >= 5)
                       for k, d in x["related_attention_seeds"].items() if any(v["lift"] >= 5 for v in d.values()))
        L.append(f"| {x['id']} | {x['target']} | " + " AND ".join(f"`{p}`" for p in x["predicates"]) + f" | {x['train']['support']} ({x['train']['tp']}/{x['train']['fp']}) | "
                 f"{x['oof']['precision']:.2f} ({x['oof']['tp']}/{x['oof']['fp']}) | {len(x['oof']['folds_rediscovered'])}/5 | {len(x['support_sessions'])} | "
                 f"{len(x['source']['origin_rules'])} ({x['source']['pass']}) | {sd or '-'} | `rules/sigma/{x['id']}.yml` |")
    L += ["", f"Provenance day du (cua so / phien Train khop, luat RIPPER goc voi moi literal ke ca vang mat, engine, tham so, seed): "
          "`reports/step7/rules_provenance.json`. Moi file Sigma co custom field `vtguard_provenance` tro ve day.", "",
          "## 3. Luat bi loai theo cong", "", "| Cong | So luat | Mo ta |", "|---|---|---|"]
    for gk, d in P["gates"].items(): L.append(f"| {gk} | {P['n_rejected_by_gate'].get(gk, 0)} | {d} |")
    L += ["", f"Them: {P['features']['n_atoms_blocked_forbidden']}/{P['features']['n_atoms_all']} atom bi chan o tang dac trung cua luot rang buoc "
          f"({', '.join(f'{k}: {v}' for k, v in P['features']['blocked_by_reason'].items() if not k.startswith('S4-auto'))}; "
          f"S4-auto: {sum(v for k, v in P['features']['blocked_by_reason'].items() if k.startswith('S4-auto'))}). "
          "18 luat cua luot khong rang buoc bi cong G1 loai, vd `image=cmd.exe` (S2), `event_id=40961` (S3), `event_id=103` ESENT (S4), "
          "`svchost & dsmsvc` (S4-auto, precision Train 1.00 cho T1003 nhung 0% trong cay tien trinh). Danh sach: `reports/step7/m1_rules.md`.", "",
          "## 4. Sigma", "",
          f"- 11 file: 10 luat don + 1 correlation `temporal` (VTR-T1018-02: `nltest.exe` va `%USERDNSDOMAIN%` o hai event khac nhau, Train "
          "cach nhau <= 0.07 s; timespan 1m, group-by Computer). logsource `process_creation` (moi token cua luat chi khop Sysmon 1 / "
          "Security 4688 tren Train); token -> `CommandLine|re` co bien token (khong khop `System32`), image -> `Image|endswith`.",
          "- Correlation dat `generate: false` (spec Sigma correlation): hai luat con KHONG sinh truy van / canh bao rieng "
          "(pySigma: output cua luat con = False).",
          f"- Validate: {V['tool']} -> 0 loi, 0 canh bao validator o ca 11 file.",
          "- Matcher noi bo `src/rules/apply.py` doc YAML Sigma (khong doc provenance): == vi tu luat tren Train 0 lech o 11/11 luat "
          "(tap cua so khop trung provenance); chan doan tren 3 tap test: 0 lech. Log Wazuh giu nhay escape `\\\"`, regex chap nhan lam bien.", "",
          "## 5. Chi-luat canh B0 / B1 TF-IDF (b) / B2 (a) / VT-Seq-ens", "",
          "Nguong co dinh 0.5 dat truoc (nhi phan = co luat khop; da nhan = hop TTP cua luat theo TTP). Diem = max precision OOF cua luat khop.", ""]
    L.append(tables(".", ["b0_wazuh", "b1_tfidf_b", "b2_lgbm_a", "vtseq_M3_ens", "rules"], (), (), (1337, 7, 42, 2024, 99)))
    L += ["## 6. TP / FP theo tung luat", "", "| Luat | Muc tieu | Vi tu | Train (in-sample) TP/FP | T-clean TP/FP | T-hard FP/88 | T-novel TP/FP |", "|---|---|---|---|---|---|---|"]
    pred = {x["id"]: " AND ".join(f"`{p}`" for p in x["predicates"]) for x in P["rules"]}
    for k, v in per.items():
        L.append(f"| {k} | {v['target']} | {pred[k]} | {v['train']['tp']}/{v['train']['fp']} | {v['t_clean']['tp']}/{v['t_clean']['fp']} | {v['t_hard']['fp']} | {v['t_novel']['tp']}/{v['t_novel']['fp']} |")
    L += ["", "## 7. So voi B0 (luat Wazuh co san)", "", "| TTP | B0 F1 T-clean / T-novel | Chi-luat F1 T-clean / T-novel | Luat theo TTP | B0 mu? |", "|---|---|---|---|---|"]
    by_t = {}
    for x in P["rules"]: by_t.setdefault(x["target"], []).append(x["id"])
    vs_b0 = {}
    for t in TTPS:
        g = lambda m, sp: m["splits"][sp]["ttp_tuned"]["per_ttp"][t]["f1"]["point"]
        blind = g(b0, "t_clean") == 0 and g(b0, "t_novel") == 0
        vs_b0[t] = {"b0": [g(b0, "t_clean"), g(b0, "t_novel")], "rules": [g(r, "t_clean"), g(r, "t_novel")], "b0_blind": blind, "rules_ids": by_t.get(t, [])}
        L.append(f"| {t} | {g(b0, 't_clean'):.2f} / {g(b0, 't_novel'):.2f} | {g(r, 't_clean'):.2f} / {g(r, 't_novel'):.2f} | {', '.join(by_t.get(t, [])) or '- (dua vao AI)'} | {'CO' if blind else 'khong'} |")
    L += ["", "B0 mu hoan toan 4 TTP (F1 = 0: T1016, T1018, T1654, T1003.003); luat tu sinh phu **T1018, T1654, T1003.003** (3/4). "
          "T1016 khong nhanh nao phu bang luat (dua vao AI). B0 tot hon o T1087.002 (F1 0.58 / 0.59), noi luat tu sinh khong co luat theo "
          "TTP. Nhi phan: chi-luat 0/88 FP tren T-hard so voi 17/88 cua B0.", "",
          "## 8. Du doan OOF cho Buoc 8", "",
          f"- `reports/preds/rules_train.jsonl` la **IN-SAMPLE** (11 luat quy nap tu toan Train). **Buoc 8 CHI duoc dung "
          f"`reports/preds/rules_oof_train.jsonl` de hoc fusion.**",
          "- OOF: voi moi fold, chay LAI quy trinh moc 1 chi tren 4/5 Train (tu vung, danh sach chan S1-S5 + S4-auto tinh tren 4/5 Train, "
          "RIPPER 2 luot, cong G0-G2, G4) va ap len 1/5 con lai. Trong fold khong co OOF long nen G3 xap xi bang support >= 10 + precision >= "
          "0.9 tren 4/5 Train (khong co cong >= 10 cua so OOF) -> bo luat fold de dai hon bo luat cuoi (vd co luat T1016).",
          f"- Ket qua OOF (nguong 0.5): nhi phan precision {oof['binary_at_0.5']['precision']}, recall {oof['binary_at_0.5']['recall']}, "
          f"F1 {oof['binary_at_0.5']['f1']}; F1 TTP {oof['ttp_f1_at_0.5']} (macro {oof['macro_f1_ttp']}). So luat moi fold: "
          f"{[f['n_rules'] for f in oof['folds']]}; trung voi 11 luat cuoi: {[f['n_final_rules_present'] for f in oof['folds']]}.", "",
          "## 9. Han che", "",
          f"- **KHONG tuyen bo tong quat hoa sang ntds2v.** VTR-T1003003-01 / VTR-BIN-02 (`cmd~'create'`) bat 6/6 cua so T-novel cua ntds2v "
          "(bien the `vssadmin create shadow`) chi nho token chung `create` - trung khop, khong phai luat duoc thiet ke cho bien the nay.",
          "- **Token chung co rui ro FP ngoai lab:** `create` (vd `schtasks /create`, `sc create`) va `system` (VTR-T1654-01, tu bo loc "
          "`*SYSTEM*` cua get-eventlog). Trong lab 0/88 FP tren T-hard, nhung khong bao dam o moi truong khac.",
          f"- **VTR-T1654-01 gan nham nhan TTP** T1654 cho {per['VTR-T1654-01']['t_novel']['fp']} cua so T-novel (cua so doc hai, khong mang "
          "T1654) - ghi lai, khong chinh luat.",
          "- **Khong co luat theo TTP cho T1016 va T1087.002** (phien mixed lam token cua TTP khac xuat hien; cac luat chinh xac khong qua "
          "cong); hai TTP nay dua vao AI (VT-Seq-ens). T1087.002 chi duoc phu o muc nhi phan (VTR-BIN-04 `.findall`, VTR-BIN-05).",
          "- **Luat quy nap tu 2 host / 1 domain** (DC01 + WIN10-01, CORP.VTLAB.TEST); coverage gap da biet (dataset card muc 9); T1003.003 "
          "test nho (6 phien T-novel).",
          "- Chi-luat kem AI ve recall va phat hien som (T-novel k=4: 0.70 vs VT-Seq-ens 1.00) - binh thuong voi luat don gian.",
          "- Correlation VTR-T1018-02: matcher danh gia o muc cua so (timespan khong mo phong); timespan 1m chon tu khoang cach tren Train.",
          "- G3 trong OOF fold la xap xi (muc 8).", "",
          "## 10. Tieu chi chap nhan Buoc 7 (brief muc 8)", "", "| # | Tieu chi | Ket qua | Bang chung |", "|---|---|---|---|"]
    for i, c, ok, e in acc: L.append(f"| {i} | {c} | {'DAT' if ok else 'KHONG DAT'} | {e} |")
    L += ["", f"**Tong: {sum(1 for a in acc if a[2])}/{len(acc)} dat.** Unit test: {test_line.replace('KET QUA: ', '')}", ""]
    with open(os.path.join("reports", "step7_report.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    res = {"generated": gen, "dataset_version": "v1.2", "approved_rules_commit": APPROVED_COMMIT, "engine": P["engine"],
           "deviations_from_brief": P["deviations_from_brief"], "rules": [{k: x[k] for k in ("id", "target", "predicates", "train", "oof", "support_sessions")} for x in P["rules"]],
           "n_rejected_by_gate": P["n_rejected_by_gate"], "features": P["features"],
           "sigma": {"validation": V, "generate_false_on_correlation": True, "equivalence": r["sigma_equivalence"]},
           "rules_only": {"t_clean_f1": S["t_clean"]["tuned"]["f1"], "t_hard_fp": S["t_hard"]["tuned"]["fp"], "t_novel_f1": S["t_novel"]["tuned"]["f1"],
                          "t_novel_recall": S["t_novel"]["tuned"]["recall"], "macro_f1_ttp": {s: S[s]["ttp_tuned"]["macro_f1"] for s in ("t_clean", "t_novel")},
                          "t1003_sessions_t_novel": S["t_novel"]["tuned"]["ntds_session_recall"]["binary"]["detected"]},
           "per_rule": per, "vs_b0": vs_b0, "oof_for_step8": {k: oof[k] for k in ("file", "binary_at_0.5", "ttp_f1_at_0.5", "macro_f1_ttp", "note")},
           "acceptance": [{"id": i, "criterion": c, "pass": bool(ok), "evidence": e} for i, c, ok, e in acc]}
    with open(os.path.join("reports", "step7_results.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, indent=1)
    print("\n".join(f"#{i} {'DAT' if ok else 'KHONG DAT'}: {c}" for i, c, ok, e in acc)); print(test_line)

if __name__ == "__main__":
    main()
