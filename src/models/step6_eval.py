#!/usr/bin/env python3
"""VT-Guard Buoc 6 moc 3 - cham ket qua Colab (reports/step6/m3) bang src/eval/evaluate.py tren host.

1. Kiem: commit Colab, sha256 dataset + aux, nguong M3 trung reports/step6/final_config.json.
2. Chep du doan reports/step6/m3/reports/preds/*.jsonl -> reports/preds/ (dinh dang Buoc 5, dung cho Buoc 8).
3. Moi mo hinh (vtseq_<cfg>_s<seed>, vtseq_<cfg>_ens): evaluate() voi nguong da khoa tu OOF (sel/<model>.json) +
   diem phat hien som (early/<model>.json) -> reports/step6/eval/<model>.json + .md. Khong chon lai gi tren test.
4. Paired bootstrap (1000 lan, seed 1337, cung chi so mau cua so cho hai mo hinh): VT-Seq-ens (M3) - baseline cho
   macro-F1 TTP T-novel, PR-AUC T-novel (mau tren T-novel), FPR T-hard (mau tren T-hard). Baseline: B1 TF-IDF (b),
   B2 (a), B3 (b) tung seed (B3 khong co ens). Chi tuyen bo "hon" khi CI 95% khong chua 0.
Chay: python src/models/step6_eval.py
"""
import glob, hashlib, json, os, shutil, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval"))
from evaluate import (check_dataset, load_all_meta, load_preds, evaluate, render_markdown, check_predictions,
                      TTPS, TEST_SPLITS)                       # noqa: E402
from bootstrap import average_precision, SEED, N_BOOT          # noqa: E402

M3 = os.path.join("reports", "step6", "m3")

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def verify(root):
    ri = json.load(open(os.path.join(root, M3, "run_info.json"), encoding="utf-8"))
    ds = json.load(open(os.path.join(root, "reports", "dataset_stats.json"), encoding="utf-8"))["files_sha256"]
    man = json.load(open(os.path.join(root, "reports", "step6", "aux_manifest.json"), encoding="utf-8"))
    assert all(ds[k] == v for k, v in ri["dataset_sha256"].items()), "sha256 dataset Colab khac host"
    assert ri["aux_sha256"] == man["sha256"], "aux khac"
    fc = json.load(open(os.path.join(root, "reports", "step6", "final_config.json"), encoding="utf-8"))
    for sd, v in fc["per_seed"].items():
        s = json.load(open(os.path.join(root, M3, "sel", f"vtseq_M3_s{sd}.json"), encoding="utf-8"))
        assert (s["binary"], s["binary_score"], s["ttp"], s["final_epochs"]) == (
            v["threshold_binary_fpr1pct"], v["binary_score"], v["threshold_ttp"], v["final_epochs"]), f"M3 s{sd} khac ban khoa"
    return ri

def score_all(root, meta):
    os.makedirs(os.path.join(root, "reports", "step6", "eval"), exist_ok=True)
    for f in sorted(glob.glob(os.path.join(root, M3, "reports", "preds", "*.jsonl"))):
        shutil.copyfile(f, os.path.join(root, "reports", "preds", os.path.basename(f)))
    models = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(root, M3, "sel", "*.json")))
    out = {}
    for m in models:
        sel = json.load(open(os.path.join(root, M3, "sel", f"{m}.json"), encoding="utf-8"))
        er = json.load(open(os.path.join(root, M3, "early", f"{m}.json"), encoding="utf-8"))
        early = {s: {int(k): v for k, v in byk.items()} for s, byk in er.items()}
        preds = {s: load_preds(root, m, s) for s in TEST_SPLITS}
        tr = load_preds(root, m, "train")                    # OOF (diem nhi phan da chon)
        y = np.array([w["window_malicious"] for w in meta["train"]], bool); sc = np.array([tr[w["window_id"]]["p"] for w in meta["train"]])
        pr = sc >= sel["binary"]; tp = int((pr & y).sum()); f1_oof = 2 * tp / (2 * tp + int((pr & ~y).sum()) + int((~pr & y).sum()))
        thr = {"binary": sel["binary"], "binary_train_oof_f1": f1_oof, "binary_rule": sel["binary_rule"],
               "ttp": sel["ttp"], "ttp_train_oof_f1": sel["ttp_train_oof_f1"]}
        res = evaluate(m, meta, preds, thr, root=root, early=early)
        res.update(selection=sel, acceptance={"one_pred_per_window_no_leak": check_predictions(meta, preds)["ok"],
                                              "thresholds_from": "Train OOF (reports/step6/m3/sel), khoa truoc test"})
        with open(os.path.join(root, "reports", "step6", "eval", f"{m}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        with open(os.path.join(root, "reports", "step6", "eval", f"{m}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(render_markdown(res))
        out[m] = res
        print(f"[{m}] T-clean F1 {res['splits']['t_clean']['tuned']['f1']['point']:.3f} | T-hard FP {res['splits']['t_hard']['tuned']['fp']} | "
              f"T-novel F1 {res['splits']['t_novel']['tuned']['f1']['point']:.3f} | kiem tra {res['acceptance']['one_pred_per_window_no_leak']}", flush=True)
    return out

# ---------------- paired bootstrap ----------------
def thresholds_of(root, m):
    p6 = os.path.join(root, M3, "sel", f"{m}.json")
    if os.path.exists(p6):
        s = json.load(open(p6, encoding="utf-8")); return s["binary"], s["ttp"]
    r = json.load(open(os.path.join(root, "reports", "step5", f"{m}.json"), encoding="utf-8"))
    return r["thresholds"]["binary"], r["thresholds"]["ttp"]

def arrays(root, m, split, meta):
    P = load_preds(root, m, split); W = meta[split]
    y = np.array([w["window_malicious"] for w in W], bool)
    yt = np.array([[t in w["window_ttps"] for t in TTPS] for w in W], bool)
    s = np.array([P[w["window_id"]]["p"] for w in W], float)
    st = np.array([[P[w["window_id"]]["p_ttp"][t] for t in TTPS] for w in W], float)
    return y, yt, s, st

def macro_f1(yt, pt):
    f = []
    for j in range(yt.shape[1]):
        tp = int((pt[:, j] & yt[:, j]).sum()); fp = int((pt[:, j] & ~yt[:, j]).sum()); fn = int((~pt[:, j] & yt[:, j]).sum())
        if tp + fp + fn: f.append(2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f)) if f else np.nan

def paired(root, a, b, meta, n_boot=N_BOOT, seed=SEED):
    """Hieu so a - b, cung mau cua so. Tra {metric: {diff, lo, hi, a, b}}."""
    ta, tta = thresholds_of(root, a); tb, ttb = thresholds_of(root, b)
    y, yt, sa, sta = arrays(root, a, "t_novel", meta); _, _, sb, stb = arrays(root, b, "t_novel", meta)
    pa = sta >= np.array([tta[t] for t in TTPS]); pb = stb >= np.array([ttb[t] for t in TTPS])
    yh, _, ha, _ = arrays(root, a, "t_hard", meta); _, _, hb, _ = arrays(root, b, "t_hard", meta)
    assert not yh.any()
    fa, fb = ha >= ta, hb >= tb
    rng = np.random.default_rng(seed); n, nh = len(y), len(yh)
    stats = {"macro_f1_ttp_t_novel": [], "pr_auc_t_novel": [], "fpr_t_hard": []}
    for _ in range(n_boot):
        i = rng.integers(0, n, n); j = rng.integers(0, nh, nh)
        stats["macro_f1_ttp_t_novel"].append(macro_f1(yt[i], pa[i]) - macro_f1(yt[i], pb[i]))
        stats["pr_auc_t_novel"].append(average_precision(y[i], sa[i]) - average_precision(y[i], sb[i]) if y[i].any() else np.nan)
        stats["fpr_t_hard"].append(fa[j].mean() - fb[j].mean())
    point = {"macro_f1_ttp_t_novel": (macro_f1(yt, pa), macro_f1(yt, pb)), "pr_auc_t_novel": (average_precision(y, sa), average_precision(y, sb)),
             "fpr_t_hard": (fa.mean(), fb.mean())}
    out = {}
    for k, v in stats.items():
        v = np.array([x for x in v if np.isfinite(x)])
        lo, hi = np.percentile(v, [2.5, 97.5])
        pval = float(min(1.0, max(2 * min((v <= 0).mean(), (v >= 0).mean()), 1.0 / len(v))))   # hai phia, tu phan bo bootstrap
        out[k] = {"p_value": round(pval, 4), "a": round(point[k][0], 4), "b": round(point[k][1], 4), "diff": round(point[k][0] - point[k][1], 4),
                  "lo": round(float(lo), 4), "hi": round(float(hi), 4), "n_valid": int(len(v)),
                  "verdict": "a hon" if (lo > 0 if k != "fpr_t_hard" else hi < 0) else ("a kem" if (hi < 0 if k != "fpr_t_hard" else lo > 0) else "khong khac co y nghia")}
    return out

def main(root="."):
    print("checksum dataset:", check_dataset(root))
    ri = verify(root); print("Colab commit", ri["commit"][:8], "| khoa tu", ri["final_config_locked_from"][:8], "| nguong M3 trung final_config")
    meta = load_all_meta(root)
    if "--bootstrap-only" not in sys.argv: score_all(root, meta)
    base = ["b1_tfidf_b", "b2_lgbm_a", "b3_gru_b_s1337", "b3_gru_b_s7", "b3_gru_b_s42"]
    pb = {}
    for ens in ("vtseq_M3_ens", "vtseq_M4b_ens"):
        for b in base:
            pb[f"{ens} - {b}"] = paired(root, ens, b, meta)
    ck = {os.path.basename(p): sha(p) for p in sorted(glob.glob(os.path.join(root, M3, "ckpt", "*.pt")))}
    with open(os.path.join(root, "reports", "step6", "paired_bootstrap.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_boot": N_BOOT, "seed": SEED, "unit": "cua so (T-novel cho macro-F1/PR-AUC, T-hard cho FPR)", "results": pb}, f, indent=1)
    with open(os.path.join(root, "reports", "step6", "checkpoints_sha256.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"location": "reports/step6/m3/ckpt (khong vao git, *.pt trong .gitignore); ban goc: Drive step6_m3_" + ri["commit"][:8] + ".zip",
                   "colab_commit": ri["commit"], "sha256": ck}, f, indent=1)
    for k, v in pb.items():
        print(k, {m: (x["diff"], x["lo"], x["hi"], x["verdict"]) for m, x in v.items()})

def holm_family(pb):
    """9 so sanh VT-Seq-ens (M3) vs B1 TF-IDF (b) / B2 (a) / B3 (b) x 3 chi so; B3 lay seed co p lon nhat; Holm."""
    fam = []
    for bname, keys in (("B1 TF-IDF (b)", ["b1_tfidf_b"]), ("B2 (a)", ["b2_lgbm_a"]), ("B3 (b) (3 seed, p lon nhat)", [f"b3_gru_b_s{x}" for x in (1337, 7, 42)])):
        for m, mn in (("macro_f1_ttp_t_novel", "macro-F1 TTP T-novel"), ("pr_auc_t_novel", "PR-AUC T-novel"), ("fpr_t_hard", "FPR T-hard")):
            rs = [pb[f"vtseq_M3_ens - {k}"][m] for k in keys]
            worst = max(rs, key=lambda r: r["p_value"])
            fam.append({"baseline": bname, "metric": mn, "diff": worst["diff"], "lo": worst["lo"], "hi": worst["hi"], "p": worst["p_value"]})
    order = sorted(range(len(fam)), key=lambda i: fam[i]["p"]); m_ = len(fam); run = 0.0
    for r_, i in enumerate(order):
        run = max(run, min(1.0, (m_ - r_) * fam[i]["p"])); fam[i]["p_holm"] = run
    return fam

def report(root="."):
    """reports/step6/m3_test.md: paired bootstrap + Spearman tung seed M2 vs M3 + T1003 tung seed; bang day du o m3_summary.md."""
    E = os.path.join(root, "reports", "step6", "eval")
    pb = json.load(open(os.path.join(root, "reports", "step6", "paired_bootstrap.json"), encoding="utf-8"))["results"]
    L = ["# VT-Guard Buoc 6 moc 3 - VT-Seq tren test (cham bang evaluate.py tren host)", "",
         "Huan luyen chinh tren Colab (CUDA) bang `notebooks/step6_vtseq_colab.ipynb` (commit 44f8948), cau hinh KHOA truoc test "
         "(`reports/step6/final_config.json`: VT-Seq = M3). Test chay MOT lan; nguong, p_bin/p_bin', so epoch lay tu OOF Train. "
         "Bang day du (bang chinh, T-hard theo chu ky / cmd / do dai, F1 theo TTP, phat hien som) o `reports/step6/m3_summary.md`.", "",
         "**Paired bootstrap** (1000 lan, seed 1337, cung mau cua so; hieu so = VT-Seq-ens - baseline; FPR: am = tot hon). "
         "Chi tuyen bo 'hon' khi CI 95% khong chua 0.", "",
         "| So sanh | macro-F1 TTP T-novel: a / b / hieu [CI] | PR-AUC T-novel: a / b / hieu [CI] | FPR T-hard: a / b / hieu [CI] |", "|---|---|---|---|"]
    for k, v in pb.items():
        c = lambda m: f"{v[m]['a']:.3f} / {v[m]['b']:.3f} / **{v[m]['diff']:+.3f}** [{v[m]['lo']:+.3f}, {v[m]['hi']:+.3f}] {v[m]['verdict']}"
        L.append(f"| {k} | {c('macro_f1_ttp_t_novel')} | {c('pr_auc_t_novel')} | {c('fpr_t_hard')} |")
    # Holm cho ho 9 so sanh cua mo hinh trien khai (VT-Seq-ens M3): 3 baseline x 3 chi so; B3 (b) co 3 seed ->
    # lay p-value LON NHAT trong 3 seed (bao thu) va hieu so nho nhat theo huong co loi.
    fam = holm_family(pb)
    L += ["", "**Hieu chinh so sanh boi (Holm, 9 so sanh: VT-Seq-ens M3 vs 3 baseline x 3 chi so).** p-value hai phia tu phan bo "
          "bootstrap (san 1/1000). B3 (b): lay seed co p lon nhat (bao thu). Cac dong khac (M4b-ens, tung seed B3) o bang tren la "
          "tham khao, CHUA hieu chinh so sanh boi.", "",
          "| Baseline | Chi so | Hieu (VT-Seq-ens - baseline) [CI 95%] | p | p Holm | Ket luan sau Holm (alpha 0.05) |", "|---|---|---|---|---|---|"]
    for f_ in fam:
        good = (f_["diff"] > 0) if not f_["metric"].startswith("FPR") else (f_["diff"] < 0)
        concl = ("VT-Seq-ens hon" if good else "VT-Seq-ens kem") if f_["p_holm"] < 0.05 else "khong khac co y nghia"
        L.append(f"| {f_['baseline']} | {f_['metric']} | {f_['diff']:+.3f} [{f_['lo']:+.3f}, {f_['hi']:+.3f}] | {f_['p']:.3f} | {f_['p_holm']:.3f} | {concl} |")
    L += ["", "**Ghi chu**", "",
          "- **Mo hinh trien khai = VT-Seq-ens (M3, trung binh xac suat 5 seed)**, nguong chon tren OOF trung binh. Seed le KHONG on dinh "
          "voi T1003.003 (bang cuoi: M3 seed 42 bat 5/6 phien, seed 7 chi 4/6 o nhan TTP; M4b va M3cp seed 99 bo sot 0/6), ens bat 6/6.",
          "- **Crop do dai (M2 -> M3), trung thuc:** Spearman trung binh giam (T-hard +0.32 -> +0.11, T-novel +0.29 -> +0.14) CHU YEU nho "
          "seed 7 (-0.44 / -0.61); trung vi chi giam nhe (+0.40 -> +0.29, +0.40 -> +0.33) va 3/5 seed M3 van > +0.2 tren T-novel (+0.35, +0.33, +0.43). "
          "VT-Seq-ens dat |rho| <= 0.2 (T-hard +0.01, T-novel +0.12) mot phan do TRIET TIEU tuong quan trai dau giua cac seed, khong "
          "chung minh tung mo hinh trung lap voi do dai. Kiem soat do dai van la han che mo.", ""]
    L += ["", "**Spearman(diem, n_events) tren cua so am - tung seed (hieu qua crop: M2 -> M3)**", "",
          "| Cau hinh | " + " | ".join(f"s{sd}" for sd in (1337, 7, 42, 2024, 99)) + " | trung binh | trung vi |", "|---|---|---|---|---|---|---|---|"]
    for c in ("M2", "M3", "M4", "M4b"):
        for sp, nm in (("t_hard", "T-hard"), ("t_novel", "T-novel")):
            v = [json.load(open(os.path.join(E, f"vtseq_{c}_s{sd}.json"), encoding="utf-8"))["splits"][sp]["spearman_score_len_neg"]["point"] for sd in (1337, 7, 42, 2024, 99)]
            L.append(f"| {c} {nm} | " + " | ".join(f"{x:+.2f}" for x in v) + f" | {np.mean(v):+.2f} +- {np.std(v, ddof=1):.2f} | {np.median(v):+.2f} |")
    for e in ("vtseq_M3_ens", "vtseq_M4b_ens"):
        r = json.load(open(os.path.join(E, f"{e}.json"), encoding="utf-8"))
        L.append(f"| {e} | T-hard {r['splits']['t_hard']['spearman_score_len_neg']['point']:+.2f}, T-novel {r['splits']['t_novel']['spearman_score_len_neg']['point']:+.2f} | | | | | | |")
    L += ["", "**T1003.003 theo phien T-novel tung seed** (nhi phan / nhan TTP, cua 6)", "",
          "| Cau hinh | " + " | ".join(f"s{sd}" for sd in (1337, 7, 42, 2024, 99)) + " |", "|---|---|---|---|---|---|"]
    for c in ("M1", "M2", "M3", "M4", "M4b", "M3cp"):
        cells = []
        for sd in (1337, 7, 42, 2024, 99):
            n = json.load(open(os.path.join(E, f"vtseq_{c}_s{sd}.json"), encoding="utf-8"))["splits"]["t_novel"]["tuned"]["ntds_session_recall"]
            cells.append(f"{n['binary']['detected']} / {n['ttp_label']['detected']}")
        L.append(f"| {c} | " + " | ".join(cells) + " |")
    L.append("")
    with open(os.path.join(root, "reports", "step6", "m3_test.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    print("\n".join(L))

if __name__ == "__main__":
    if "--report-only" not in sys.argv: main(".")
    report(".")
