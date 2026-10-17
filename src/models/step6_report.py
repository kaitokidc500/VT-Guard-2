#!/usr/bin/env python3
"""VT-Guard Buoc 6 - tong hop reports/step6_report.md + reports/step6_results.json (brief muc 8) + kiem tieu chi muc 9.
Chi doc ket qua da sinh (m2_oof.json, eval/*.json, paired_bootstrap.json, faithfulness.json, rule_seeds_train.json,
onnx_report.json, final_config.json); khong huan luyen / khong cham lai.
Chay: python src/models/step6_report.py
"""
import glob, json, os, subprocess, sys
from datetime import datetime, timezone, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines"): sys.path.insert(0, os.path.join(HERE, d))
from summary import tables, load                     # noqa: E402
from step6_eval import holm_family                   # noqa: E402
from evaluate import check_dataset, check_model_sources, TTPS, SPLITS   # noqa: E402

ROOT = "."
S6 = os.path.join("reports", "step6")
SEEDS = (1337, 7, 42, 2024, 99)
CHAIN = [("M0a", "b3_gru_a", "B3 (a): GRU last-state, don nhiem (Buoc 5)"), ("M0b", "b3_gru_b", "B3 (b): nhu M0a, bo image/parent"),
         ("M1", "vtseq_M1", "+ attention pooling (don nhiem)"), ("M2", "vtseq_M2", "+ da nhiem"), ("M3", "vtseq_M3", "+ crop U[4,n] moi lop = VT-Seq"),
         ("M4", "vtseq_M4", "+ name dropout 0.5"), ("M4b", "vtseq_M4b", "M3 + bo han image/parent")]

def J(*p): return json.load(open(os.path.join(*p), encoding="utf-8"))

def ms(v, d=3):
    v = np.array([x for x in v if x is not None], float)
    return f"{v.mean():.{d}f} +- {v.std(ddof=1) if len(v) > 1 else 0:.{d}f}"

def msd(v):
    v = np.array(v, float); return [round(float(v.mean()), 4), round(float(v.std(ddof=1)) if len(v) > 1 else 0.0, 4)]

def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)

def test_metrics(rs):
    S = lambda r, sp: r["splits"][sp]
    f = {"t_clean_f1": [S(r, "t_clean")["tuned"]["f1"]["point"] for r in rs], "t_novel_f1": [S(r, "t_novel")["tuned"]["f1"]["point"] for r in rs],
         "t_novel_pr_auc": [S(r, "t_novel")["pr_auc"]["point"] for r in rs],
         "macro_f1_clean": [S(r, "t_clean")["ttp_tuned"]["macro_f1"]["point"] for r in rs],
         "macro_f1_novel": [S(r, "t_novel")["ttp_tuned"]["macro_f1"]["point"] for r in rs],
         "t1654_novel": [S(r, "t_novel")["ttp_tuned"]["per_ttp"]["T1654"]["f1"]["point"] for r in rs],
         "t_hard_fp": [S(r, "t_hard")["tuned"]["fp"] for r in rs],
         "spearman_t_hard": [S(r, "t_hard")["spearman_score_len_neg"]["point"] for r in rs],
         "spearman_t_novel": [S(r, "t_novel")["spearman_score_len_neg"]["point"] for r in rs],
         "t1003_sess_bin": [S(r, "t_novel")["tuned"]["ntds_session_recall"]["binary"]["detected"] for r in rs],
         "t1003_sess_ttp": [S(r, "t_novel")["tuned"]["ntds_session_recall"]["ttp_label"]["detected"] for r in rs],
         "threshold_bin": [r["thresholds"]["binary"] for r in rs]}
    return f

def acceptance():
    rows = []
    ds = check_dataset(ROOT); src = check_model_sources(ROOT)
    ri = J(S6, "m3", "run_info.json"); ref = J("reports", "dataset_stats.json")["files_sha256"]
    t = subprocess.run([sys.executable, os.path.join(HERE, "test_vtseq.py")], capture_output=True, text=True)
    last = [l for l in t.stdout.splitlines() if l.startswith("KET QUA")]
    ok1 = all(ds.values()) and not src and all(ref[k] == v for k, v in ri["dataset_sha256"].items()) and t.returncode == 0
    rows.append((1, "Checksum dataset-v1.2 khop (host + Colab); acceptance #2 (truong cam) dat cho VT-Seq", ok1,
                 f"check_dataset {all(ds.values())}; check_model_sources {src or 'sach'}; sha Colab khop; unit test " + (last[0].split("|")[0].replace("KET QUA: ", "").strip() if last else str(t.returncode))))
    fc = J(S6, "final_config.json")
    anc = git("merge-base", "--is-ancestor", "3ebc94b", ri["commit"]).returncode == 0
    lock_files = git("ls-tree", "-r", "--name-only", "3ebc94b", "reports/step6").stdout.split()
    no_test_before = not any("/eval/" in f or "/m3/" in f or "paired" in f for f in lock_files)
    sel_ok = all(J(S6, "m3", "sel", f"vtseq_M3_s{sd}.json")["binary"] == v["threshold_binary_fpr1pct"] for sd, v in fc["per_seed"].items())
    rows.append((2, "Cau hinh, nguong, lambda, p_bin vs p_bin' chon tren Train OOF; test chay mot lan", anc and no_test_before and sel_ok,
                 "khoa o commit 3ebc94b (final_config.json) TRUOC moi ket qua test, la to tien cua commit Colab "
                 f"{ri['commit'][:8]}: {anc}; khong co file test nao o 3ebc94b: {no_test_before}; nguong M3 trung ban khoa: {sel_ok}; "
                 "lambda = 1 co dinh (brief), khong chon. Ghi chu: lan chay Colab dau dung giua chung o M3c (loi kiem nguong), "
                 "khong cham/xem du doan nao; chay lai cung cau hinh khoa."))
    n = {c: len(glob.glob(os.path.join(S6, "eval", f"vtseq_{c}_s*.json"))) for c in ("M1", "M2", "M3", "M4", "M4b", "M3c", "M3cp")}
    ens = [os.path.exists(os.path.join(S6, "eval", f"vtseq_{e}_ens.json")) for e in ("M3", "M4b")]
    rows.append((3, ">= 5 seed; trung binh +- do lech chuan; co VT-Seq-ens", all(v >= 5 for v in n.values()) and all(ens),
                 f"so seed {n}; ens M3/M4b {ens}"))
    rows.append((4, "Du chuoi ablation M0->M4(b) va ablation dac trung (a)(b)(c)(c')", all(v >= 5 for v in n.values()),
                 "M0 = B3 (Buoc 5), M1-M4b; (a) = M3, (b) = M4b, (c) = M3c (chi bao T-hard), (c') = M3cp"))
    pb = J(S6, "paired_bootstrap.json")
    rows.append((5, "Paired bootstrap cho moi tuyen bo 'hon baseline'", len(pb["results"]) >= 9 and all("p_value" in v for r in pb["results"].values() for v in r.values()),
                 "1000 lan, cung mau cua so; p-value hai phia + Holm cho 9 so sanh; chi tuyen bo 'hon' khi p Holm < 0.05"))
    F = J(S6, "faithfulness.json")
    rows.append((6, "Faithfulness attention co so lieu", len(F["models"]) == 6, "ens + 5 seed, k = 1/3/5, CI bootstrap"))
    O = J(S6, "onnx_report.json")
    rows.append((7, "ONNX parity < 1e-4; co do tre CPU", all(m["parity_ok_1e-4"] and m["latency_onnxruntime_cpu_1thread"] for m in O["models"].values()),
                 "; ".join(f"{k}: max {max(m['parity_max_abs_diff'].values()):.1e}, b1 {m['latency_onnxruntime_cpu_1thread']['batch1_ms_per_window']['mean']} ms" for k, m in O["models"].items())))
    pm = sorted({os.path.basename(p).rsplit("_", 1)[0].replace("_t", "") for p in glob.glob(os.path.join("reports", "preds", "vtseq*_t_hard.jsonl"))})
    miss = [p for p in glob.glob(os.path.join("reports", "preds", "vtseq*_t_hard.jsonl"))
            if not all(os.path.exists(p.replace("_t_hard.jsonl", f"_{s}.jsonl")) for s in SPLITS)]
    k0 = set(json.loads(open(glob.glob(os.path.join("reports", "preds", "vtseq_M3_ens_t_novel.jsonl"))[0]).readline()))
    k5 = set(json.loads(open(os.path.join("reports", "preds", "b2_lgbm_a_t_novel.jsonl")).readline()))
    npred = len(glob.glob(os.path.join("reports", "preds", "vtseq*_t_hard.jsonl")))
    rows.append((8, "reports/preds/vtseq*_<split>.jsonl (cung dinh dang Buoc 5) cho Buoc 8", not miss and k0 == k5 and npred >= 37,
                 f"{npred} mo hinh x 4 tap, thieu {len(miss)}; khoa ban ghi trung Buoc 5: {k0 == k5}"))
    return rows

def build():
    tz = timezone(timedelta(hours=7))
    fc = J(S6, "final_config.json"); ri = J(S6, "m3", "run_info.json"); m2 = J(S6, "m2_oof.json")
    pb = J(S6, "paired_bootstrap.json"); fam = holm_family(pb["results"])
    F = J(S6, "faithfulness.json"); RS = J(S6, "rule_seeds_train.json"); O = J(S6, "onnx_report.json")
    chain = {}
    for code, m, desc in CHAIN:
        rs = load(ROOT, m, SEEDS)
        chain[code] = {"model": m, "desc": desc, "n_seeds": len(rs), "test": {k: msd(v) for k, v in test_metrics(rs).items()},
                       "oof": {k: [round(x, 4) for x in m2["agg_mean_sd"][code][k]] for k in ("macro_f1_ttp", "pr_auc_bin", "fpr_hard_negative", "spearman_len_neg", "thr_bin")}}
    fin = {m: test_metrics(load(ROOT, m, SEEDS)) for m in ("vtseq_M3_ens", "vtseq_M4b_ens", "b1_tfidf_b", "b2_lgbm_a", "b2_lgbm_b")}
    acc = acceptance()
    # ---------------- results.json ----------------
    res = {"generated": datetime.now(tz).replace(microsecond=0).isoformat(), "dataset_version": "v1.2",
           "deployed_model": "VT-Seq-ens = trung binh xac suat 5 seed M3 (reports/step6/final_config.json)",
           "environment": {"oof_and_test_training": f"Colab CUDA, torch {ri['torch']}, commit {ri['commit']}",
                           "scoring": "host, src/eval/evaluate.py", "rule_seeds_and_onnx": "host CPU",
                           "host_refit_folds_oof_corr_vs_colab": RS["oof_score_corr_host_vs_colab"],
                           "notebook": "notebooks/step6_vtseq_colab.ipynb (tai lap)", "final_config_commit": "3ebc94b"},
           "chain": chain, "final": {k: {kk: msd(vv) for kk, vv in v.items()} for k, v in fin.items()},
           "holm": fam, "paired_bootstrap_file": "reports/step6/paired_bootstrap.json",
           "faithfulness": {m: {k: {x: F["models"][m][k][x] for x in ("p_bin", "p_ttp_true")} for k in ("1", "3", "5")} for m in F["models"]},
           "onnx": {k: {"parity_max_abs_diff": v["parity_max_abs_diff"], "latency": v["latency_onnxruntime_cpu_1thread"], "sha256": v.get("sha256")} for k, v in O["models"].items()},
           "acceptance": [{"id": i, "criterion": c, "pass": bool(ok), "evidence": e} for i, c, ok, e in acc]}
    with open(os.path.join("reports", "step6_results.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, indent=1)
    # ---------------- report.md ----------------
    C = lambda code, k, d=3: f"{chain[code]['test'][k][0]:.{d}f} +- {chain[code]['test'][k][1]:.{d}f}"
    O_ = lambda code, k, d=3: f"{chain[code]['oof'][k][0]:.{d}f} +- {chain[code]['oof'][k][1]:.{d}f}"
    hb3 = next(f for f in fam if f["baseline"].startswith("B3") and f["metric"].startswith("macro"))
    hb1 = next(f for f in fam if f["baseline"].startswith("B1") and f["metric"].startswith("macro"))
    hb2 = next(f for f in fam if f["baseline"].startswith("B2") and f["metric"].startswith("macro"))
    ens = fin["vtseq_M3_ens"]
    L = ["# VT-Guard - Bao cao Buoc 6: VT-Seq (GRU-Attention da nhiem) tren dataset-v1.2", "",
         f"Sinh tu dong boi `src/models/step6_report.py` luc {res['generated']}. So lieu: `reports/step6_results.json`; chi tiet: "
         "`reports/step6/` (m2_oof.md, m3_test.md, m3_summary.md, m4_explain.md, eval/*.json); du doan cho Buoc 8: `reports/preds/vtseq*`.", "",
         "## 0. Tom tat va moi truong", "",
         "- **Mo hinh trien khai: VT-Seq-ens** = trung binh xac suat 5 seed (1337, 7, 42, 2024, 99) cua cau hinh **M3** "
         "(embedding event + GRU 1 lop hidden 96 + attention pooling + da nhiem bin/TTP + crop do dai U[4,n]); nguong nhi phan "
         "FPR <= 1% tren OOF Train trung binh; p_bin' = max(p_bin, max p_ttp). Seed le KHONG duoc dung de trien khai (khong on dinh "
         "voi T1003.003, muc 6).",
         f"- **Moi truong:** moc 2 (OOF chuoi ablation) va moc 3 (fit cuoi + du doan test MOT lan) huan luyen tren **Colab CUDA** "
         f"(torch {ri['torch']}, commit `{ri['commit'][:8]}`) bang `notebooks/step6_vtseq_colab.ipynb` (di kem de tai lap); cham diem "
         "bang `src/eval/evaluate.py` tren host. Hat giong luat (attention OOF) va ONNX chay tren **host CPU**; 25 mo hinh fold huan "
         f"luyen lai tren host co diem OOF tuong quan {min(RS['oof_score_corr_host_vs_colab'].values()):.3f}-"
         f"{max(RS['oof_score_corr_host_vs_colab'].values()):.3f} voi Colab.",
         "- **Khoa truoc test:** cau hinh M3, nguong, p_bin/p_bin', so epoch cuoi ghi o `reports/step6/final_config.json` (commit 3ebc94b) "
         "truoc khi co bat ky du doan test nao. Quy tac 4.3 cho M3/M4/M4b ngang nhau; pha hoa bang do on dinh nguong OOF (them sau "
         "khi xem OOF, van chi dua tren Train).", "",
         "## 1. Ket luan chinh", "",
         f"1. **Sau hieu chinh Holm (9 so sanh), VT-Seq-ens hon B3 (GRU thuan, cung ho) o macro-F1 TTP T-novel**: hieu "
         f"{hb3['diff']:+.3f} [CI {hb3['lo']:+.3f}, {hb3['hi']:+.3f}], p Holm {hb3['p_holm']:.3f} (B3 lay seed bao thu nhat).",
         "2. **Chuoi ablation M0 -> M4(b): attention pooling la nguon cai thien chinh.** OOF macro-F1 TTP "
         f"{O_('M0a', 'macro_f1_ttp')} (M0a) -> {O_('M1', 'macro_f1_ttp')} (M1); tren test T1654 T-novel {C('M0a', 't1654_novel', 2)} -> "
         f"{C('M1', 't1654_novel', 2)} (moi seed M1 0.61-0.82 > moi seed B3 0.44-0.53). Macro-F1 test cua M1 {C('M1', 'macro_f1_novel', 2)} "
         "dao dong vi T1003.003 chi 6 cua so; M2-M3 on dinh hon. Da nhiem / crop / name dropout / bo ten cong cu: thay doi nho, trong "
         "do lech chuan giua seed (mo ta trung binh +- do lech chuan, khong them kiem dinh).",
         f"3. **So voi B1 TF-IDF (b) va B2 (a): KHONG khac biet co y nghia sau Holm** (macro-F1 TTP T-novel: vs B1 {hb1['diff']:+.3f}, "
         f"p {hb1['p']:.3f} -> p Holm {hb1['p_holm']:.3f}; vs B2 {hb2['diff']:+.3f}, p Holm {hb2['p_holm']:.3f}; PR-AUC va FPR T-hard "
         "deu khong khac). Nhi phan va FPR T-hard da gan tran o baseline nhu brief du doan; VT-Seq khong kem B1 o day. "
         "**Khong tuyen bo VT-Seq tot hon moi baseline.**",
         "4. **Uu the con lai cua VT-Seq (mo ta, khong phai kiem dinh 'hon'):**",
         f"   - T1654 (TTP kho nhat): VT-Seq-ens {ens['t1654_novel'][0]:.2f} vs B2 (a) {fin['b2_lgbm_a']['t1654_novel'][0]:.2f}, "
         f"B1 (b) {fin['b1_tfidf_b']['t1654_novel'][0]:.2f}, B3 0.46-0.50.",
         f"   - Ben khi bo ten cong cu: VT-Seq-ens (M4b) macro-F1 TTP T-novel {fin['vtseq_M4b_ens']['macro_f1_novel'][0]:.2f}, T-hard FP "
         f"{fin['vtseq_M4b_ens']['t_hard_fp'][0]:.0f}/88 vs B2 (b) {fin['b2_lgbm_b']['macro_f1_novel'][0]:.2f}, "
         f"{fin['b2_lgbm_b']['t_hard_fp'][0]:.0f}/88.",
         f"   - Trung lap do dai (ens): Spearman diem~n_events am T-hard {ens['spearman_t_hard'][0]:+.2f}, T-novel "
         f"{ens['spearman_t_novel'][0]:+.2f} (B1 TF-IDF (b) +0.78 / +0.68) - xem han che ve crop.",
         "   - Nguong on dinh: do lech chuan nguong nhi phan OOF cua M3 0.060 (nho nhat trong M1-M4b); so voi B3 Buoc 5 (max-F1: "
         "0.51-0.90 o B3 (b)). Luu y: khi ap CUNG quy tac FPR <= 1%, nguong B3 cung on dinh (0.018 / 0.043) -> cai thien nay den tu "
         "QUY TAC NGUONG, khong tu kien truc.",
         "   - Attention trung thuc (faithfulness dat o moi k cho ens, muc 7) va xuat ONNX: ens 5 mang ~1.4 ms/cua so (1 thread CPU).", "",
         "## 2. Chuoi ablation M0 -> M4(b) (OOF Train va test; trung binh +- do lech chuan qua seed)", "",
         "| Ma | Cau hinh | seed | OOF macro-F1 TTP | OOF PR-AUC | OOF FPR hard_neg | OOF nguong bin | Test T-novel F1 | Test T-novel PR-AUC | "
         "Test macro-F1 clean / novel | Test T1654 novel | T-hard FP/88 | Spearman T-hard / T-novel | T1003 phien bin / TTP |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for code, m, desc in CHAIN:
        L.append(f"| {code} | {desc} | {chain[code]['n_seeds']} | {O_(code, 'macro_f1_ttp')} | {O_(code, 'pr_auc_bin')} | {O_(code, 'fpr_hard_negative')} | "
                 f"{O_(code, 'thr_bin')} | {C(code, 't_novel_f1')} | {C(code, 't_novel_pr_auc')} | {C(code, 'macro_f1_clean', 2)} / {C(code, 'macro_f1_novel', 2)} | "
                 f"{C(code, 't1654_novel', 2)} | {C(code, 't_hard_fp', 1)} | {C(code, 'spearman_t_hard', 2)} / {C(code, 'spearman_t_novel', 2)} | "
                 f"{C(code, 't1003_sess_bin', 1)} / {C(code, 't1003_sess_ttp', 1)} |")
    L += ["", "M0 (B3) 3 seed, tran 60 epoch; M1-M4b 5 seed, tran 100, patience 10, 0/150 fold cham tran. OOF M0 tinh lai bang cung quy "
          "tac nguong 4.3 tu OOF Buoc 5. Bang OOF day du + epoch tung fold: `reports/step6/m2_oof.md`.", "",
          "## 3. VT-Seq cuoi + VT-Seq-ens canh B0 / B1 / B2 / B3 (cot giong Buoc 5)", ""]
    L.append(tables(ROOT, ["b0_wazuh", "b1_tfidf_b", "b1_raw_b", "b2_lgbm_a", "b2_lgbm_b", "b3_gru_a", "b3_gru_b", "vtseq_M3", "vtseq_M3_ens",
                           "vtseq_M4b", "vtseq_M4b_ens", "vtseq_M3cp", "vtseq_M3c"], (), ["vtseq_M3c"], SEEDS))
    L += ["vtseq_M3 = VT-Seq (a); vtseq_M4b = (b) bo ten cong cu; vtseq_M3c = (c) chi cay tien trinh (ro nhan theo cau truc, CHI bao "
          "T-hard); vtseq_M3cp = (c') che event nen mot-phia. (c') ~ (a): khong song nho event nen mot-phia.", "",
          "## 4. Paired bootstrap so voi baseline + Holm", "",
          "1000 lan, seed 1337, cung mau cua so cho hai mo hinh; p-value hai phia tu phan bo bootstrap; Holm tren ho 9 so sanh cua "
          "mo hinh trien khai (VT-Seq-ens M3 vs B1 TF-IDF (b) / B2 (a) / B3 (b) x 3 chi so; B3 lay seed co p lon nhat).", "",
          "| Baseline | Chi so | Hieu [CI 95%] | p | p Holm | Ket luan (alpha 0.05 sau Holm) |", "|---|---|---|---|---|---|"]
    for f_ in fam:
        good = (f_["diff"] > 0) if not f_["metric"].startswith("FPR") else (f_["diff"] < 0)
        concl = ("VT-Seq-ens hon" if good else "VT-Seq-ens kem") if f_["p_holm"] < 0.05 else "khong khac co y nghia"
        L.append(f"| {f_['baseline']} | {f_['metric']} | {f_['diff']:+.3f} [{f_['lo']:+.3f}, {f_['hi']:+.3f}] | {f_['p']:.3f} | {f_['p_holm']:.3f} | {concl} |")
    L += ["", "So sanh tham khao (M4b-ens, tung seed B3; CHUA hieu chinh so sanh boi): `reports/step6/m3_test.md`.", "",
          "## 5. On dinh giua seed", "",
          "| Mo hinh | Quy tac nguong | Nguong nhi phan (tung seed / TB +- DLC) | macro-F1 TTP T-novel | T1003 phien T-novel bin / TTP |", "|---|---|---|---|---|"]
    for lab, m, rule in (("B3 (a)", "b3_gru_a", "max-F1 OOF (Buoc 5)"), ("B3 (b)", "b3_gru_b", "max-F1 OOF (Buoc 5)"), ("VT-Seq M3", "vtseq_M3", "FPR <= 1% OOF")):
        t = test_metrics(load(ROOT, m, SEEDS))
        L.append(f"| {lab} | {rule} | {', '.join(f'{x:.3f}' for x in t['threshold_bin'])} ({ms(t['threshold_bin'])}) | {ms(t['macro_f1_novel'])} | "
                 f"{t['t1003_sess_bin']} / {t['t1003_sess_ttp']} |")
    L += [f"| B3 (a) / (b) | FPR <= 1% OOF (tinh lai, chi OOF) | {O_('M0a', 'thr_bin')} / {O_('M0b', 'thr_bin')} | - | - |",
          f"| VT-Seq-ens (M3) | FPR <= 1% OOF trung binh | {J(S6, 'm3', 'sel', 'vtseq_M3_ens.json')['binary']:.3f} | {ens['macro_f1_novel'][0]:.3f} | "
          f"{ens['t1003_sess_bin'][0]:.0f} / {ens['t1003_sess_ttp'][0]:.0f} |", "",
          "Macro-F1 TTP T-novel: VT-Seq M3 cao hon B3 o moi seed (0.79-0.82 vs 0.73-0.78) voi do lech chuan tuong duong; T1003 theo "
          "phien van dao dong theo seed o ca hai ho; VT-Seq-ens xoa dao dong nay (6/6). Nguong: xem muc 1.4 (on dinh nho quy tac FPR <= 1%).", "",
          "## 6. Han che", "",
          "- **Kiem soat do dai (crop) chua vung.** M2 -> M3: Spearman trung binh T-hard +0.32 -> +0.11, T-novel +0.29 -> +0.14, nhung "
          "chu yeu nho seed 7 (-0.44 / -0.61); trung vi chi +0.40 -> +0.29 va +0.40 -> +0.33; 3/5 seed M3 van > +0.2 tren T-novel. "
          "VT-Seq-ens dat |rho| <= 0.2 mot phan do triet tieu tuong quan trai dau giua seed.",
          "- **Seed le khong on dinh voi T1003.003** (M3 seed 42 bat 5/6 phien; seed 7 4/6 o nhan TTP; M4b va M3cp seed 99 bo sot 0/6) "
          "-> trien khai bang ens (6/6).",
          "- **T1003.003 test nho:** 6 phien / 6 cua so T-novel (12 cua so T-clean); F1 cua so bao hoa, bao theo phien.",
          "- **Hat giong luat (Train, attention OOF) co 4 canh bao** (`reports/step6/m4_explain.md`): (1) `\\windows\\temp\\ntds_t0` = duong "
          "dan ART chua ma ky thuat; (2) `cmd.exe` / `cmd /c` dung dau moi TTP (ART chay qua cmd, bat doi xung da biet); (3) attention "
          "dung chung cho moi TTP (phien mixed lam lan token) va T1003.003 co 34% top-5 la event NEN (ESENT 216/103, vssvc); "
          "(4) T1087.002: `powershell.exe` (lift ~81) + EID 40961/4104 la dau vet bo sinh (`<launcher>`->powershell.exe) - luat phai "
          "dua tren lenh that (`net user /domain`, `adsisearcher`, `objectcategory`).",
          "- **Ablation (c)** dung mat na cay tien trinh = co che gan nhan -> chi bao T-hard.",
          "- Dataset: cac han che cua `reports/dataset_card.md` muc 9 van ap dung (coverage route/netstat/Domain Admins chi o phia am, "
          "loi trung PID 23 event).", "",
          "## 7. Giai thich bang attention (dau vao Buoc 7)", "",
          f"Faithfulness (cua so duong duoc ens phat hien: {F['n_windows_detected']['t_clean']} T-clean + {F['n_windows_detected']['t_novel']} "
          "T-novel): xoa top-k theo alpha vs xoa k event ngau nhien (10 lan, cung k).", "",
          "| Mo hinh | k | p_bin: giam top-k / ngau nhien / hieu [CI] | p_ttp dung TTP: hieu [CI] |", "|---|---|---|---|"]
    for m in F["models"]:
        for k in ("1", "3", "5"):
            r = F["models"][m][k]
            L.append(f"| {m} | {k} | {r['p_bin']['drop_topk']:.3f} / {r['p_bin']['drop_random']:.3f} / {r['p_bin']['diff']:+.3f} "
                     f"[{r['p_bin']['lo']:+.3f}, {r['p_bin']['hi']:+.3f}]{'' if r['p_bin']['faithful'] else ' KHONG dat'} | "
                     f"{r['p_ttp_true']['diff']:+.3f} [{r['p_ttp_true']['lo']:+.3f}, {r['p_ttp_true']['hi']:+.3f}]{'' if r['p_ttp_true']['faithful'] else ' KHONG dat'} |")
    L += ["", "Ens dat o moi k; trong 30 o cua seed le chi seed 7 k=1 p_bin co CI chua 0. Hat giong theo TTP (CHI Train, attention OOF; "
          "bang day du + canh bao: `reports/step6/m4_explain.md`, `reports/step6/rule_seeds_train.json`):", ""]
    for t, v in RS["ttp"].items():
        top = sorted([x for c in ("image_name", "cmd_token") for x in v[c] if x["share_pos_windows"] >= 0.2], key=lambda x: -x["lift"])[:4]
        L.append(f"- {t} ({v['n_windows']} cua so; top-5 event nen {v['top5_origin_share'].get('bg', 0):.0%}): "
                 + "; ".join(f"`{x['value']}` lift {x['lift']}" for x in top))
    L += ["", "## 8. ONNX", "", "| Mo hinh | max abs diff p_bin / p_ttp / alpha (toan T-novel) | batch 1 ms/cua so TB / p95 | batch 32 ms/cua so TB / p95 | sha256 |",
          "|---|---|---|---|---|"]
    for k, v in O["models"].items():
        mx = v["parity_max_abs_diff"]; a = v["latency_onnxruntime_cpu_1thread"]
        L.append(f"| {k} ({v['n_nets']} mang) | {mx['p_bin']:.1e} / {mx['p_ttp']:.1e} / {mx['alpha']:.1e} | {a['batch1_ms_per_window']['mean']:.2f} / "
                 f"{a['batch1_ms_per_window']['p95']:.2f} | {a['batch32_ms_per_window']['mean']:.2f} / {a['batch32_ms_per_window']['p95']:.2f} | `{v.get('sha256', '')[:16]}` |")
    L += ["", f"Opset 17, truc dong batch + time, dau ra p_bin / p_ttp / alpha; onnxruntime {O['host']['onnxruntime']}, CPU 1 thread tren host. "
          "File .onnx va checkpoint .pt khong vao git (.gitignore); sha256 o `reports/step6/onnx_report.json`, `checkpoints_sha256.json`.", "",
          "## 9. Tieu chi chap nhan Buoc 6 (brief muc 9)", "", "| # | Tieu chi | Ket qua | Bang chung |", "|---|---|---|---|"]
    for i, c, ok, e in acc: L.append(f"| {i} | {c} | {'DAT' if ok else 'KHONG DAT'} | {e} |")
    L += ["", f"**Tong: {sum(1 for r in acc if r[2])}/{len(acc)} dat.**", ""]
    with open(os.path.join("reports", "step6_report.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    print("\n".join(f"#{i} {'DAT' if ok else 'KHONG DAT'}: {c}" for i, c, ok, e in acc))

if __name__ == "__main__":
    build()
