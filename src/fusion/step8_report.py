#!/usr/bin/env python3
"""VT-Guard Buoc 8 - tong hop reports/step8_report.md + reports/step8_results.json (brief muc 8) + kiem tieu chi muc 9.
Chi doc ket qua da sinh (m1_oof.json, final_fusion.json, eval/*.json, paired_bootstrap.json, alerts_<split>.jsonl,
m3_explain.json); chay lai src/fusion/test_fuse.py lam bang chung. Khong chinh gi theo test.
Chay: python src/fusion/step8_report.py
"""
import json, os, subprocess, sys
from collections import Counter
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines"): sys.path.insert(0, os.path.join(HERE, d))
from summary import tables                                       # noqa: E402
from evaluate import check_dataset, load_all_meta, TEST_SPLITS, SPLITS, TTPS   # noqa: E402
from bootstrap import wilson                                     # noqa: E402

S8 = os.path.join("reports", "step8")
LOCK_COMMIT, TEST_COMMIT = "3fd9531", "bdf2adc"
ALERT_KEYS = {"window_id", "host", "t0", "t1", "score", "decision_source", "ttps", "rule_ids", "attention_top5", "threshold", "fusion_config"}

def J(*p): return json.load(open(os.path.join(*p), encoding="utf-8"))

def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True)

def fmt_m(m):
    return (f"{m['macro_f1_ttp']:.3f} | " + " | ".join(f"{m['f1_ttp'][t]:.3f}" for t in TTPS) + f" | {m['pr_auc']:.3f} | {m['fpr_hard_negative']:.3f} | {m['recall']:.3f}")

def precision_by_source(meta):
    lab = {w["window_id"]: bool(w["window_malicious"]) for s in TEST_SPLITS for w in meta[s]}
    out = {}
    for s in TEST_SPLITS + ["gop"]:
        A = [json.loads(l) for sp in (TEST_SPLITS if s == "gop" else [s]) for l in open(os.path.join(S8, f"alerts_{sp}.jsonl"), encoding="utf-8")]
        out[s] = {}
        for src in ("both", "ai", "rule"):
            a = [x for x in A if x["decision_source"] == src]; tp = sum(lab[x["window_id"]] for x in a)
            out[s][src] = {"n": len(a), "tp": tp, "precision": round(tp / len(a), 4) if a else None, "wilson": wilson(tp, len(a)) if a else None}
    return out

def acceptance(meta):
    rows = []
    t = subprocess.run([sys.executable, os.path.join(HERE, "test_fuse.py")], capture_output=True, text=True)
    res = {l[7:].split(" - ")[0].strip(): l.startswith("[PASS]") for l in t.stdout.splitlines() if l.startswith(("[PASS]", "[FAIL]"))}
    last = next((l for l in t.stdout.splitlines() if l.startswith("KET QUA")), "")
    pick = lambda pre: any(k.startswith(pre) for k in res) and all(v for k, v in res.items() if k.startswith(pre))
    ds = check_dataset(".")
    rows.append((1, "Checksum dataset khop; fusion hoc/chon chi tren OOF; khong dung rules_train.jsonl", all(ds.values()) and pick("1") and pick("2") and pick("3"),
                 f"check_dataset {all(ds.values())}; test_fuse 1a-1c (khong doc rules_train / preds test) {pick('1')}; OOF AI = TB 5 seed {pick('2')}; F4 CV long {pick('3')}"))
    files_lock = git("ls-tree", "-r", "--name-only", LOCK_COMMIT, "reports").stdout.split()
    has_lock = "reports/step8/final_fusion.json" in files_lock
    no_test = not any(f.startswith("reports/step8/eval") or f.startswith("reports/preds/fusion") for f in files_lock)
    anc = git("merge-base", "--is-ancestor", LOCK_COMMIT, TEST_COMMIT).returncode == 0
    same = git("diff", "--quiet", LOCK_COMMIT, "--", "reports/step8/final_fusion.json").returncode == 0
    rows.append((2, "final_fusion.json commit truoc khi chay test", has_lock and no_test and anc and same,
                 f"commit {LOCK_COMMIT} co final_fusion.json {has_lock}, chua co ket qua test {no_test}, la to tien cua commit ket qua test {TEST_COMMIT} {anc}; "
                 f"final_fusion.json khong doi tu luc khoa {same}"))
    ev = all(os.path.exists(os.path.join(S8, "eval", f"fusion_{c}.json")) for c in ("F0", "F0p", "F1", "F2", "F3B", "F4B"))
    pb = J(S8, "paired_bootstrap.json"); holm6 = sum(len(d) for d in pb["holm_family"].values()) == 6 and all("p_holm" in v for d in pb["holm_family"].values() for v in d.values())
    rows.append((3, "Bang test du F0-F4; paired bootstrap + Holm", ev and holm6, f"eval F0, F0', F1, F2, F3-B, F4-B {ev}; Holm 6 so sanh {holm6}"))
    A = [json.loads(l) for s in TEST_SPLITS for l in open(os.path.join(S8, f"alerts_{s}.jsonl"), encoding="utf-8")]
    schema = all(ALERT_KEYS <= set(a) and all({"id", "sigma_file", "provenance"} <= set(r) for r in a["rule_ids"]) and len(a["attention_top5"]) == 5 for a in A)
    share = sum(bool(a["rule_ids"]) for a in A) / len(A)
    rows.append((4, "alerts_<split>.jsonl du schema; co ti le canh bao duoc luat giai thich", schema, f"{len(A)} canh bao, du truong muc 6 {schema}; co luat {share:.0%}"))
    M3 = J(S8, "m3_explain.json")
    zero = all(c["decision_mismatch_binary"] == 0 and c["decision_mismatch_ttp"] == 0 for c in M3["check"].values())
    rows.append((5, "infer.py trung ket qua cham (0 lech) va co do tre", zero and "batch1" in M3["latency"] and "batch32" in M3["latency"],
                 f"0 lech quyet dinh tren 3 tap {zero}; do tre batch 1 {M3['latency']['batch1']['total']['mean_ms']} ms, batch 32 {M3['latency']['batch32']['total']['mean_ms']} ms / cua so"))
    pf = [os.path.join("reports", "preds", f"fusion_{s}.jsonl") for s in SPLITS]
    k0 = set(json.loads(open(pf[2]).readline())); k5 = set(json.loads(open(os.path.join("reports", "preds", "b2_lgbm_a_t_novel.jsonl")).readline()))
    rows.append((6, "reports/preds/fusion_<split>.jsonl cung dinh dang chung", all(os.path.exists(f) for f in pf) and k0 == k5,
                 "fusion_{train (OOF), t_clean, t_hard, t_novel}.jsonl; khoa ban ghi trung Buoc 5"))
    return rows, last

def main():
    tz = timezone(timedelta(hours=7)); gen = datetime.now(tz).replace(microsecond=0).isoformat()
    meta = load_all_meta(".")
    FF = J(S8, "final_fusion.json"); M1 = J(S8, "m1_oof.json"); pb = J(S8, "paired_bootstrap.json"); M3 = J(S8, "m3_explain.json")
    E = {c: J(S8, "eval", f"fusion_{c}.json") for c in ("F0", "F0p", "F1", "F2", "F3B", "F4B")}
    prec = precision_by_source(meta)
    acc, test_line = acceptance(meta)
    ch = FF["chosen"]; S3, S0, S1 = E["F3B"]["splits"], E["F0"]["splits"], E["F1"]["splits"]
    hf = pb["holm_family"]
    L = ["# VT-Guard - Bao cao Buoc 8: Hybrid Fusion (AI + luat tu sinh)", "",
         f"Sinh tu dong boi `src/fusion/step8_report.py` luc {gen}. So lieu: `reports/step8_results.json`; chi tiet: `reports/step8/` "
         "(m1_oof.md, final_fusion.json, m2_test.md, m3_explain.md, eval/, alerts_<split>.jsonl); du doan: `reports/preds/fusion_<split>.jsonl`.", "",
         "## 0. Tom tat", "",
         f"- **Cau hinh trien khai: F3-B** - `s = p + 0.1 r`, `s_k = p_k + 0.1 r_k` (r_k chi cho {', '.join(ch['rule_ttp_channels'])}), nguong nhi phan "
         f"{ch['threshold_binary']:.4f} (FPR <= 1% am OOF). Chon CHI tren OOF Train va KHOA o commit `{LOCK_COMMIT}` truoc khi cham test.",
         "- **Luat la kenh XAC NHAN / tang diem** (beta = 0.1), khong phai kenh tu canh bao: tren test KHONG co canh bao nao chi do luat. "
         "F2 (OR) cho phep luat tu canh bao nhung thua F3 tren OOF (PR-AUC, muc 1).",
         f"- **Yeu cau (2) cua mon hoc:** F3-B **hon chi-luat co y nghia sau Holm** (macro-F1 TTP T-novel {hf['F3B - F1']['macro_f1_ttp_t_novel']['diff']:+.3f}, "
         f"PR-AUC T-novel {hf['F3B - F1']['pr_auc_t_novel']['diff']:+.3f}, p Holm {hf['F3B - F1']['macro_f1_ttp_t_novel']['p_holm']:.3f}); **khong kem chi-AI** "
         "(can duoi CI hieu so >= 0 o ca 3 chi so, bien 0) nhung **khong hon co y nghia**. F0' = F0 nen moi khac biet F3-B vs chi-AI la do luat.",
         f"- **Gia tri chinh = giai thich + phan loai muc tin cay canh bao:** 75% canh bao co luat Sigma giai thich; canh bao co luat xac nhan "
         f"(`both`) dung {prec['gop']['both']['tp']}/{prec['gop']['both']['n']}, canh bao chi-AI dung {prec['gop']['ai']['tp']}/{prec['gop']['ai']['n']} (mo ta, mau nho).", "",
         "## 1. OOF F2-F4 va ly do chon (muc 4)", "",
         "Nguon OOF: AI `reports/preds/vtseq_M3_ens_train.jsonl` (trung binh OOF 5 seed M3, Buoc 6), luat `reports/preds/rules_oof_train.jsonl` "
         "(luat quy nap lai trong tung fold, Buoc 7); KHONG dung `rules_train.jsonl` (in-sample). F3: beta trong {0.1, 0.2, 0.3}; F4: LR 7 dac trung, "
         "diem OOF bang CV long theo nhom phien. Tieu chi: macro-F1 TTP OOF -> PR-AUC OOF -> FPR hard_negative OOF; ngang nhau (|chenh| <= DLC "
         "bootstrap hieu so) -> it tham so hon.", "",
         "| Bien the / cau hinh | macro-F1 TTP | " + " | ".join(TTPS) + " | PR-AUC | FPR hard_neg | Recall |", "|---|---|" + "---|" * (len(TTPS) + 3)]
    for v in ("A", "B"):
        for st in ("F0", "F1", "F2", "F3", "F4"):
            L.append(f"| {v}: {st} | {fmt_m(M1['variants'][v]['oof'][st]['metrics'])} |")
    L += ["", "- Bien the A (moi kenh r_k, dinh nghia brief) chon F3 (macro-F1 0.847) nho kenh T1016 - kenh nay chi co trong bo luat FOLD, "
          "bo luat cuoi KHONG co luat T1016.",
          f"- **Bien the B (khoa):** {FF['deviation_from_brief']['what']}. Ly do (su kien cau truc chi tu Train): {FF['deviation_from_brief']['reason']}",
          "- B: macro-F1 F2 / F3 / F4 ngang nhau (chenh <= 0.005, DLC ~0.011); PR-AUC F3 > F2 (0.997 vs 0.982) va > F4 (sit sao) -> F3, "
          "beta 0.1 (ba beta cho ket qua OOF giong nhau). Do nhay khi thay luat fold bang luat cuoi chi la MO TA (in-sample), khong dung de chon.", "",
          "## 2. Test F0-F4 canh B0 / B1 / B2", "",
          "F0 chi-AI (VT-Seq-ens, nguong Buoc 6); F0' chi-AI nguong chon lai tren cung OOF (doi chung mo ta); F1 chi-luat (Buoc 7); F2 OR; "
          "**F3-B chon**; F4-B stacking. Kiem: F0 trung VT-Seq-ens Buoc 6, F1 trung chi-luat Buoc 7.", ""]
    L.append(tables(".", ["b0_wazuh", "b1_tfidf_b", "b2_lgbm_a", "fusion_F0", "fusion_F0p", "fusion_F1", "fusion_F2", "fusion_F3B", "fusion_F4B"], (), (), ()))
    L += ["## 3. Paired bootstrap + Holm (6 so sanh)", "",
          "1000 lan, seed 1337, cung mau cua so; 'hon' chi khi p Holm < 0.05; 'khong kem' = can duoi CI 95% cua hieu so >= 0 (FPR: can tren <= 0).", "",
          "| So sanh | Chi so | Hieu [CI 95%] | p | p Holm | Ket luan |", "|---|---|---|---|---|---|"]
    MET = {"macro_f1_ttp_t_novel": "macro-F1 TTP T-novel", "pr_auc_t_novel": "PR-AUC T-novel", "fpr_t_hard": "FPR T-hard"}
    for c, d in hf.items():
        for m, v in d.items():
            good = v["diff"] > 0 if m != "fpr_t_hard" else v["diff"] < 0
            noninf = (v["lo"] >= 0) if m != "fpr_t_hard" else (v["hi"] <= 0)
            concl = ("hon" if good else "kem") if v["p_holm"] < 0.05 else ("khong khac; khong kem (bien 0)" if noninf else "khong khac")
            L.append(f"| {c.replace('F3B', 'F3-B')} | {MET[m]} | {v['diff']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}] | {v['p']:.3f} | {v['p_holm']:.3f} | {concl} |")
    L += ["", "- **F0' trung F0 tren moi chi so test** -> khac biet F3-B vs F0 hoan toan do luat: xep hang nhi phan (PR-AUC T-novel 0.986 -> 0.998) "
          "va T1018 (T-novel 0.83 -> 0.85, T-clean 0.71 -> 0.74). Khong co y nghia sau Holm.",
          "- **Muc giam FPR thay o OOF khong lap lai tren test:** tren OOF F3 co FPR hard_negative 0.028 so voi 0.037 cua F0, nhung nguong F3 "
          "(0.869166) gan trung tau F0 (0.8691656) - do hoa diem tai nguong (lam tron 6 chu so), khong phai do luat; tren test cung 1/88.", "",
          "## 4. Giai thich canh bao (muc 6) va pipeline (muc 7)", "",
          "| Tap | Canh bao | Co >= 1 luat | TP (co luat) | FP (co luat) | decision_source | Luat khop nhung khong canh bao |", "|---|---|---|---|---|---|---|"]
    for s, st in M3["stats"].items():
        a = st["alerts"]
        L.append(f"| {s} | {a['n']} | {a['with_rule']} ({(a['share_with_rule'] or 0):.0%}) | {st['tp']['n']} ({st['tp']['with_rule']}) | {st['fp']['n']} ({st['fp']['with_rule']}) | "
                 f"{a['decision_source']} | {st['rule_match_not_alerted']} |")
    L += ["", "**Precision theo decision_source (KET QUA MO TA, so mau nho; CI Wilson 95%)**", "",
          "| Tap | `both` (AI + luat xac nhan): TP/n, precision [Wilson] | `ai` (chi AI): TP/n, precision [Wilson] | `rule` (chi luat) |", "|---|---|---|---|"]
    for s in TEST_SPLITS + ["gop"]:
        c = lambda src: (f"{prec[s][src]['tp']}/{prec[s][src]['n']} = {prec[s][src]['precision']:.3f} [{prec[s][src]['wilson']['lo']:.3f}, {prec[s][src]['wilson']['hi']:.3f}]"
                         if prec[s][src]["n"] else "-")
        L.append(f"| {'gop 3 tap' if s == 'gop' else s} | {c('both')} | {c('ai')} | {c('rule')} |")
    L += ["", "**Ham y van hanh:** canh bao co luat Sigma xac nhan (`both`) dung 76/76 tren test -> uu tien xu ly; canh bao chi-AI (`ai`) dung "
          f"{prec['gop']['ai']['tp']}/{prec['gop']['ai']['n']} - ca 5 canh bao nham deu thuoc nhom nay -> can nguoi phan tich xem lai (top-5 attention di kem). "
          f"CI Wilson cua hai nhom khong chong nhau ([{prec['gop']['both']['wilson']['lo']:.3f}, {prec['gop']['both']['wilson']['hi']:.3f}] vs "
          f"[{prec['gop']['ai']['wilson']['lo']:.3f}, {prec['gop']['ai']['wilson']['hi']:.3f}]), nhung day van la MO TA tren 101 canh bao (5 nham), "
          "khong phai kiem dinh dat truoc; nhom `both` gom cac cua so co lenh tan cong ro (de hon) nen khong suy ra quan he nhan qua.", "",
          "**Vi du (chon tat dinh, chi tiet + top-5 attention: `reports/step8/m3_explain.md`):**", ""]
    ex = M3["examples"]
    for e in ex["rule_match_not_alerted"]:
        L.append(f"- **AI chan luat khop nham:** `{e['window_id']}` (T-novel, LANH TINH) - luat `{e['rule_ids'][0]['id']}` (`cmd~'system'`) khop lenh "
                 f"`auditpol /get /subcategory:\"System Integrity\"`; p_ai {e['p_ai']:.3f} + 0.1 = {e['score']:.3f} < nguong {e['threshold']:.3f} -> khong canh bao.")
    for e in ex["t_hard_fp"]:
        L.append(f"- **Canh bao nham tren T-hard (chi AI, khong luat xac nhan):** `{e['window_id']}` (kich ban quan tri batch07) - p {e['p_ai']:.3f}, TTP {e['ttps']}; "
                 "top-5 attention: " + "; ".join(f"`{(t['cmd_canon'] or t['image_name'])[:45]}` ({t['alpha']:.2f})" for t in e["attention_top5"][:4]) +
                 ". Lenh quan tri trung lenh kham pha T1016; khong luat nao xac nhan -> nhom `ai`, can xem lai.")
    for k, lab in (("both", "AI + luat"), ("ai", "chi AI")):
        e = ex[k]
        L.append(f"- **{lab}:** `{e['window_id']}` ({e['split']}, doc hai {e['label_ttps']}) - score {e['score']:.3f}, luat: "
                 f"{', '.join(r['id'] for r in e['rule_ids']) or 'khong'}; attention cao nhat `{(e['attention_top5'][0]['cmd_canon'] or '')[:60]}`.")
    L.append("- **Chi do luat:** khong co tren test.")
    lat = M3["latency"]
    L += ["", f"**Pipeline `src/pipeline/infer.py`** (featurize vocab dong bang -> ONNX VT-Seq-ens -> Sigma -> F3-B): trung `fusion_<split>.jsonl` "
          f"0 lech quyet dinh tren 3 tap (diem lech <= 6e-7). Do tre host CPU ({lat['host']['cpu']}, onnxruntime 1 thread), ms/cua so:", "",
          "| Buoc | batch 1 TB | batch 1 p95 | batch 32 TB | batch 32 p95 |", "|---|---|---|---|---|"]
    for k in ("total", "featurize", "onnx", "sigma", "fusion"):
        L.append(f"| {k} | {lat['batch1'][k]['mean_ms']:.2f} | {lat['batch1'][k]['p95_ms']:.2f} | {lat['batch32'][k]['mean_ms']:.2f} | {lat['batch32'][k]['p95_ms']:.2f} |")
    L += ["", "## 5. Thao luan trung thuc", "",
          "- **Fusion giup o dau:** (i) phan loai muc tin cay canh bao - nhom co luat xac nhan khong co canh bao nham tren test; (ii) moi canh bao "
          "co giai thich: 75% co luat Sigma (kem provenance ve cua so/phien Train), 100% co top-5 event attention; (iii) xep hang nhi phan tot hon "
          "(PR-AUC 0.986 -> 0.998) va T1018 nhinh hon - nho, khong co y nghia sau Holm; (iv) AI chan duoc luat khop nham (auditpol).",
          "- **Fusion KHONG giup o dau:** khong tang recall (chi-AI da bat 96/96 cua so duong test), khong giam FPR T-hard (van 1/88, cung cua so "
          "voi chi-AI), khong co canh bao chi-do-luat, khong cai thien T1016 / T1087.002 (khong co luat theo TTP). Ve diem so, F3-B chi 'khong kem' "
          "chi-AI.",
          "- Vi vay gia tri cua Buoc 8 nam o **giai thich duoc va xuat xu cua luat** cung voi phan loai muc tin cay canh bao, KHONG nam o diem so.", "",
          "## 6. Han che", "",
          "- **Luat fold de dai hon luat cuoi** (khong co OOF long trong fold): fusion hoc tren OOF co the tin luat khac luc test. Da xu ly bang "
          "bien the B (chi kenh luat theo TTP co trong bo luat cuoi); tham so con lai (beta, nguong) van hoc tren luat fold.",
          "- **Muc giam FPR o OOF khong lap lai tren test** (hieu ung hoa nguong) - khong tuyen bo F3-B giam FPR.",
          "- **T1003.003 test nho** (6 phien T-novel, 12 cua so T-clean); **2 host / 1 domain** (DC01 + WIN10-01, CORP.VTLAB.TEST).",
          "- Precision theo decision_source la mo ta tren 101 canh bao (5 nham): CI Wilson rong, chua kiem dinh.",
          "- Ke thua: crop do dai chua vung o tung seed (Buoc 6), token chung `create` / `system` cua luat va VTR-T1654-01 khop 1 cua so lanh "
          "tinh (Buoc 7, da dinh chinh), coverage gap va loi trung PID (dataset card muc 9), hat giong luat co canh bao scaffold (Buoc 6).", "",
          "## 7. Tieu chi chap nhan Buoc 8 (brief muc 9)", "", "| # | Tieu chi | Ket qua | Bang chung |", "|---|---|---|---|"]
    for i, c, ok, e in acc: L.append(f"| {i} | {c} | {'DAT' if ok else 'KHONG DAT'} | {e} |")
    L += ["", f"**Tong: {sum(1 for a in acc if a[2])}/{len(acc)} dat.** Unit test: {test_line.replace('KET QUA: ', '')}", ""]
    with open(os.path.join("reports", "step8_report.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    res = {"generated": gen, "dataset_version": "v1.2", "lock_commit": LOCK_COMMIT, "test_results_commit": TEST_COMMIT, "final_fusion": FF,
           "oof": {v: {st: M1["variants"][v]["oof"][st]["metrics"] for st in ("F0", "F1", "F2", "F3", "F4")} for v in ("A", "B")},
           "test": {c: {s: {"f1": E[c]["splits"][s]["tuned"]["f1"], "fp": E[c]["splits"][s]["tuned"]["fp"], "pr_auc": E[c]["splits"][s].get("pr_auc"),
                            "macro_f1_ttp": E[c]["splits"][s].get("ttp_tuned", {}).get("macro_f1")} for s in TEST_SPLITS} for c in E},
           "paired_bootstrap_holm": hf, "descriptive_vs_F0prime": pb["descriptive"], "explanation": {"stats": M3["stats"], "precision_by_source": prec},
           "pipeline": {"check": M3["check"], "latency": M3["latency"]},
           "acceptance": [{"id": i, "criterion": c, "pass": bool(ok), "evidence": e} for i, c, ok, e in acc]}
    with open(os.path.join("reports", "step8_results.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, indent=1)
    print("\n".join(f"#{i} {'DAT' if ok else 'KHONG DAT'}: {c}" for i, c, ok, e in acc)); print(test_line)
    print("precision gop:", {k: (v["tp"], v["n"], v["wilson"]) for k, v in prec["gop"].items()})

if __name__ == "__main__":
    main()
