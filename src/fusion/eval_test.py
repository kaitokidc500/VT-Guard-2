#!/usr/bin/env python3
"""VT-Guard Buoc 8 moc 2 - cham fusion tren test MOT lan bang evaluate.py (cau hinh + tham so khoa o
reports/step8/final_fusion.json, commit 3fd9531 TRUOC khi cham test). Khong chon/chinh gi tren test.

Cau hinh: F0 chi-AI (nguong Buoc 6), F0' chi-AI nguong chon lai tren cung OOF (doi chung MO TA), F1 chi-luat (Buoc 7),
F2 OR (bien the B), F3-B (CHON: s = p + 0.1 r), F4-B (LR khoa). Kenh r_k bien the B: chi T1018 / T1654 / T1003.003.
Phat hien som: diem AI tren cua so cat (reports/step6/m3/early/vtseq_M3_ens.json) + luat tren cung cua so cat
(src/rules/apply.py) -> ket hop bang cung cong thuc.
Paired bootstrap (1000, seed 1337, cung mau cua so): F3-B vs F0 va vs F1 tren macro-F1 TTP T-novel, PR-AUC T-novel,
FPR T-hard -> Holm cho 6 so sanh; "khong kem" bao bang CI hieu so. F3-B vs F0' chi mo ta (ngoai ho Holm).
Chay: python src/fusion/eval_test.py
"""
import json, math, os, shutil, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../rules", "../baselines", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))
from evaluate import (check_dataset, load_all_meta, evaluate, render_markdown, write_preds, check_predictions, early_starts,
                      TTPS, SPLITS, TEST_SPLITS, EARLY_KS)                     # noqa: E402
from bootstrap import average_precision, SEED, N_BOOT                          # noqa: E402

S8 = os.path.join("reports", "step8")
CONFIGS = ["F0", "F0p", "F1", "F2", "F3B", "F4B"]
NAME = {"F0": "fusion_F0", "F0p": "fusion_F0p", "F1": "fusion_F1", "F2": "fusion_F2", "F3B": "fusion_F3B", "F4B": "fusion_F4B"}

def read(path, order):
    rows = {}
    for l in open(path, encoding="utf-8"):
        r = json.loads(l); rows[r["window_id"]] = r
    assert set(order) <= set(rows), path
    return np.array([rows[w]["p_malicious"] for w in order]), np.array([[rows[w]["p_ttp"][t] for t in TTPS] for w in order])

def sigm(z): return 1.0 / (1.0 + np.exp(-z))

def logit(x):
    x = np.clip(np.asarray(x, float), 1e-6, 1 - 1e-6); return np.log(x / (1 - x))

def build(cfg, FF, p, pk, rp, rpk):
    """-> (s, s_k, thr, thr_k) theo cau hinh khoa. rp/rpk: diem chi-luat (>= 0.5 la khop)."""
    C = FF["controls_locked_for_test"]; ch = FF["chosen"]; mask = np.array([t in ch["rule_ttp_channels"] for t in TTPS], float)
    r = (rp >= 0.5).astype(float); rk = (rpk >= 0.5).astype(float); rkB = rk * mask
    vec = lambda d: np.array([d[t] for t in TTPS], float)
    if cfg == "F0": return p, pk, C["F0"]["tau"], vec(C["F0"]["tau_k"])
    if cfg == "F0p": return p, pk, C["F0_prime"]["thr"], vec(C["F0_prime"]["thr_k"])
    if cfg == "F1": return rp, rpk, 0.5, np.full(len(TTPS), 0.5)
    if cfg == "F2": return np.maximum(p, r), np.maximum(pk, rkB), C["F2"]["tau"], vec(C["F2"]["tau_k"])
    if cfg == "F3B": b = ch["beta"]; return p + b * r, pk + b * rkB, ch["threshold_binary"], vec(ch["thresholds_ttp"])
    if cfg == "F4B":
        M = C["F4_B"]["models"]
        lr = lambda m, X: sigm(X @ np.array(m["coef"]) + m["intercept"])
        sb = lr(M["bin"], np.column_stack([logit(p), r, rkB]))
        sk = np.column_stack([lr(M[t], np.column_stack([logit(pk[:, j]), r, rkB])) for j, t in enumerate(TTPS)])
        return sb, sk, C["F4_B"]["thr"], np.array(C["F4_B"]["thr_k"], float)
    raise ValueError(cfg)

def macro_f1(yt, dk):
    f = []
    for j in range(yt.shape[1]):
        tp = int((dk[:, j] & yt[:, j]).sum()); fp = int((dk[:, j] & ~yt[:, j]).sum()); fn = int((~dk[:, j] & yt[:, j]).sum())
        if tp + fp + fn: f.append(2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f)) if f else np.nan

def paired(A, B, meta, n_boot=N_BOOT, seed=SEED):
    """A, B: {split: (s, s_k, thr, thr_k)}; hieu so A - B."""
    Wn, Wh = meta["t_novel"], meta["t_hard"]
    y = np.array([w["window_malicious"] for w in Wn], bool); yt = np.array([[t in w["window_ttps"] for t in TTPS] for w in Wn])
    sa, ska, ta, tka = A["t_novel"]; sb, skb, tb, tkb = B["t_novel"]
    da, db = ska >= tka, skb >= tkb
    ha = A["t_hard"][0] >= A["t_hard"][2]; hb = B["t_hard"][0] >= B["t_hard"][2]
    pt = {"macro_f1_ttp_t_novel": (macro_f1(yt, da), macro_f1(yt, db)), "pr_auc_t_novel": (average_precision(y, sa), average_precision(y, sb)),
          "fpr_t_hard": (float(ha.mean()), float(hb.mean()))}
    rng = np.random.default_rng(seed); st = {k: [] for k in pt}
    for _ in range(n_boot):
        i = rng.integers(0, len(Wn), len(Wn)); j = rng.integers(0, len(Wh), len(Wh))
        st["macro_f1_ttp_t_novel"].append(macro_f1(yt[i], da[i]) - macro_f1(yt[i], db[i]))
        st["pr_auc_t_novel"].append(average_precision(y[i], sa[i]) - average_precision(y[i], sb[i]) if y[i].any() else np.nan)
        st["fpr_t_hard"].append(ha[j].mean() - hb[j].mean())
    out = {}
    for k, v in st.items():
        v = np.array([x for x in v if np.isfinite(x)]); lo, hi = np.percentile(v, [2.5, 97.5])
        pval = float(min(1.0, max(2 * min((v <= 0).mean(), (v >= 0).mean()), 1.0 / len(v))))
        out[k] = {"a": round(pt[k][0], 4), "b": round(pt[k][1], 4), "diff": round(pt[k][0] - pt[k][1], 4), "lo": round(float(lo), 4), "hi": round(float(hi), 4), "p": round(pval, 4)}
    return out

def main(root="."):
    print("checksum dataset:", check_dataset(root))
    FF = json.load(open(os.path.join(root, S8, "final_fusion.json"), encoding="utf-8"))
    meta = load_all_meta(root)
    # dau vao: test = preds khoa Buoc 6/7; train = OOF (AI OOF + luat OOF)
    src = {s: (os.path.join(root, "reports", "preds", f"vtseq_M3_ens_{s}.jsonl"), os.path.join(root, "reports", "preds", f"rules_{s}.jsonl")) for s in TEST_SPLITS}
    src["train"] = (os.path.join(root, "reports", "preds", "vtseq_M3_ens_train.jsonl"), os.path.join(root, "reports", "preds", "rules_oof_train.jsonl"))
    IN = {s: (*read(a, [w["window_id"] for w in meta[s]]), *read(b, [w["window_id"] for w in meta[s]])) for s, (a, b) in src.items()}
    # phat hien som
    from apply import load_sigma, load_windows, score as rule_score
    rules = load_sigma(root); st = early_starts(root, meta)
    W = load_windows(root, [wid for s in st for wid in st[s]])
    ai_early = json.load(open(os.path.join(root, "reports", "step6", "m3", "early", "vtseq_M3_ens.json"), encoding="utf-8"))
    ER = {s: {k: {} for k in EARLY_KS} for s in st}
    for s, byw in st.items():
        for k in EARLY_KS:
            for wid, (i0, _) in byw.items():
                rp, rpt, _ = rule_score(rules, W[wid][i0:i0 + k]); ER[s][k][wid] = (ai_early[s][str(k)][wid], rp, np.array([rpt[t] for t in TTPS]))
    os.makedirs(os.path.join(root, S8, "eval"), exist_ok=True)
    built, results = {}, {}
    for cfg in CONFIGS:
        built[cfg] = {s: build(cfg, FF, *IN[s]) for s in SPLITS}
        thr = built[cfg]["t_novel"][2]; thr_k = built[cfg]["t_novel"][3]
        preds = {s: {w["window_id"]: {"p": float(built[cfg][s][0][i]), "p_ttp": {t: float(built[cfg][s][1][i, j]) for j, t in enumerate(TTPS)}}
                     for i, w in enumerate(meta[s])} for s in SPLITS}
        early = {}
        for s, byk in ER.items():
            early[s] = {}
            for k, d in byk.items():
                ids = list(d)
                p = np.array([d[w][0] for w in ids]); rp = np.array([d[w][1] for w in ids]); rpk = np.array([d[w][2] for w in ids])
                pk = np.zeros((len(ids), len(TTPS)))           # nhanh nhi phan khong dung p_k (F4 dung r, r_k)
                early[s][k] = dict(zip(ids, build(cfg, FF, p, pk, rp, rpk)[0].astype(float)))
        y = np.array([w["window_malicious"] for w in meta["train"]], bool); dtr = built[cfg]["train"][0] >= thr
        f1tr = 2 * (dtr & y).sum() / max(1, 2 * (dtr & y).sum() + (dtr & ~y).sum() + (~dtr & y).sum())
        th = {"binary": float(thr), "binary_train_oof_f1": float(f1tr), "ttp": dict(zip(TTPS, [float(x) for x in thr_k])),
              "ttp_train_oof_f1": {t: None for t in TTPS}, "locked": "reports/step8/final_fusion.json (commit 3fd9531)"}
        res = evaluate(NAME[cfg], meta, {s: preds[s] for s in TEST_SPLITS}, th, root=root, early=early)
        res.update(config=cfg, acceptance={"one_pred_per_window_no_leak": check_predictions(meta, {s: preds[s] for s in TEST_SPLITS})["ok"],
                                           "train_split": "OOF (AI OOF + luat OOF theo fold)"})
        for s in SPLITS: write_preds(root, NAME[cfg], s, meta[s], preds[s])
        with open(os.path.join(root, S8, "eval", f"{NAME[cfg]}.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, ensure_ascii=False, indent=1)
        with open(os.path.join(root, S8, "eval", f"{NAME[cfg]}.md"), "w", encoding="utf-8", newline="\n") as f: f.write(render_markdown(res))
        results[cfg] = res
        S = res["splits"]
        print(f"[{cfg}] T-clean F1 {S['t_clean']['tuned']['f1']['point']:.3f} | T-hard FP {S['t_hard']['tuned']['fp']} | T-novel F1 "
              f"{S['t_novel']['tuned']['f1']['point']:.3f} PR-AUC {S['t_novel']['pr_auc']['point']:.3f} | macro TTP novel {S['t_novel']['ttp_tuned']['macro_f1']['point']:.3f}", flush=True)
    for s in SPLITS:                                         # du doan cau hinh CHON -> reports/preds/fusion_<split>.jsonl
        shutil.copyfile(os.path.join(root, "reports", "preds", f"{NAME['F3B']}_{s}.jsonl"), os.path.join(root, "reports", "preds", f"fusion_{s}.jsonl"))
    # kiem: F0 == VT-Seq-ens Buoc 6, F1 == chi-luat Buoc 7
    ref6 = json.load(open(os.path.join(root, "reports", "step6", "eval", "vtseq_M3_ens.json"), encoding="utf-8"))
    ref7 = json.load(open(os.path.join(root, "reports", "step7", "eval", "rules.json"), encoding="utf-8"))
    same = lambda a, b: all(a["splits"][s]["tuned"][k] == b["splits"][s]["tuned"][k] for s in TEST_SPLITS for k in ("tp", "fp", "fn"))
    sanity = {"F0_equals_step6_vtseq_M3_ens": same(results["F0"], ref6), "F1_equals_step7_rules": same(results["F1"], ref7)}
    # paired bootstrap + Holm
    pb = {"F3B - F0": paired(built["F3B"], built["F0"], meta), "F3B - F1": paired(built["F3B"], built["F1"], meta)}
    desc = {"F3B - F0p (mo ta, ngoai Holm)": paired(built["F3B"], built["F0p"], meta)}
    fam = [(c, m, v["p"]) for c, d in pb.items() for m, v in d.items()]
    order = sorted(range(len(fam)), key=lambda i: fam[i][2]); run = 0.0; holm = {}
    for r_, i in enumerate(order):
        run = max(run, min(1.0, (len(fam) - r_) * fam[i][2])); holm[(fam[i][0], fam[i][1])] = run
    for c, d in pb.items():
        for m, v in d.items(): v["p_holm"] = round(holm[(c, m)], 4)
    with open(os.path.join(root, S8, "paired_bootstrap.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_boot": N_BOOT, "seed": SEED, "holm_family": pb, "descriptive": desc, "sanity": sanity}, f, indent=1)
    print("sanity:", sanity)
    return results, pb, desc, sanity

if __name__ == "__main__":
    main(".")
