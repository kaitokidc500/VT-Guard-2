#!/usr/bin/env python3
"""VT-Guard Buoc 6 moc 2 - bang OOF chuoi ablation M0 -> M4(b) + de xuat cau hinh cuoi theo quy tac 4.3 (CHI OOF).

M1..M4b: doc reports/step6/m2/{logs,oof} - giai nen file step6_m2_<commit>.zip tai tu Colab (notebook muc 7)
vao reports/step6/m2/ (zip chua san oof/, logs/, run_info.json). M0 = B3 (Buoc 5): OOF Train da luu o reports/preds/b3_gru_<ab>_s<seed>_train.jsonl
(3 seed), ap CUNG quy tac chon nguong 4.3 (vtseq.choose_on_oof) de so cong bang.
Chi so (trung binh +- do lech chuan qua seed): macro-F1 TTP + F1 tung TTP (nguong max-F1 OOF theo TTP), PR-AUC nhi phan,
FPR tren cua so hard_negative va moi cua so am OOF (nguong FPR<=1%), recall, Spearman(diem, n_events) tren cua so am OOF
(evaluate.oof_length_spearman), nguong nhi phan, lua chon p_bin / p_bin'. Moi fold: epoch tot nhat / epoch dung.
Quy tac 4.3 (thu tu): (1) macro-F1 TTP, (2) PR-AUC, (3) FPR hard_negative (thap hon tot hon). Hai cau hinh coi la
NGANG nhau o mot tieu chi neu |chenh trung binh| <= do lech chuan gop qua seed sqrt((sd1^2+sd2^2)/2) -> xet tieu chi ke.
Ung vien cau hinh cuoi: M3, M4, M4b (brief 5.1).
Chay: python src/models/step6_m2_table.py
"""
import json, math, os, sys
from datetime import datetime, timezone, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval"))
import vtseq as V                                           # noqa: E402
from evaluate import load_meta, oof_length_spearman, TTPS   # noqa: E402

CONFIGS = ["M1", "M2", "M3", "M4", "M4b"]
CANDIDATES = ["M3", "M4", "M4b"]
B3_SEEDS = (1337, 7, 42)
DESC = {"M0a": "B3 (a): GRU last-state, don nhiem, crop B3 (Buoc 5)", "M0b": "B3 (b): nhu M0a, bo image/parent (Buoc 5)",
        "M1": "+ attention pooling (don nhiem)", "M2": "+ da nhiem", "M3": "+ crop U[4,n] moi lop",
        "M4": "+ name dropout p=0.5", "M4b": "M3 + bo han image/parent"}

def read_oof(path, order):
    r = {json.loads(l)["window_id"]: json.loads(l) for l in open(path, encoding="utf-8")}
    P_bin = np.array([r[w]["p_malicious"] for w in order]); P_ttp = np.array([[r[w]["p_ttp"][t] for t in TTPS] for w in order])
    return P_bin, P_ttp

def run_metrics(ws, meta, hn, P_bin, P_ttp, sel):
    summ = V.oof_summary(ws, P_bin, P_ttp, sel, hn)
    s = P_bin if sel["binary_score"] == "p_bin" else np.maximum(P_bin, P_ttp.max(1))
    sp = oof_length_spearman(meta, {w["window_id"]: float(s[i]) for i, w in enumerate(meta)})
    return {**summ, "spearman_len_neg": sp["point"], "spearman_ci": [sp["lo"], sp["hi"]], "thr_bin": sel["binary"],
            "binary_score": sel["binary_score"]}

def ms(v, d=3):
    v = np.array([x for x in v if x is not None], float)
    return f"{v.mean():.{d}f} +- {v.std(ddof=1) if len(v) > 1 else 0:.{d}f}"

def mean_sd(v):
    v = np.array(v, float); return float(v.mean()), float(v.std(ddof=1)) if len(v) > 1 else 0.0

def main(root="."):
    meta = load_meta(root, "train"); order = [w["window_id"] for w in meta]
    ws = V.load_split(root, "train"); assert [w.wid for w in ws] == order
    hn = np.array([w["window_class"] == "hard_negative" for w in meta])
    out_dir = os.path.join(root, "reports", "step6", "m2")
    runs = {}
    for ab in ("a", "b"):                                    # M0 = B3
        k = f"M0{ab}"; runs[k] = []
        for sd in B3_SEEDS:
            P_bin, P_ttp = read_oof(os.path.join(root, "reports", "preds", f"b3_gru_{ab}_s{sd}_train.jsonl"), order)
            sel = V.choose_on_oof(ws, P_bin, P_ttp, V.Config())
            r5 = json.load(open(os.path.join(root, "reports", "step5", f"b3_gru_{ab}_s{sd}.json"), encoding="utf-8"))
            folds = [{h: {"best_epoch": r5["train_log"][h]["best_epoch_per_fold"][i], "stop_epoch": None} for h in ("bin", "ttp")} for i in range(5)]
            runs[k].append({"seed": sd, "m": run_metrics(ws, meta, hn, P_bin, P_ttp, sel), "folds": folds, "cap": 60,
                            "n_hit_ceiling": sum(e >= 60 for h in ("bin", "ttp") for e in r5["train_log"][h]["best_epoch_per_fold"])})
    for c in CONFIGS:
        runs[c] = []
        for sd in V.SEEDS:
            lp = os.path.join(out_dir, "logs", f"{c}_s{sd}.json")
            if not os.path.exists(lp): continue
            rec = json.load(open(lp, encoding="utf-8"))
            P_bin, P_ttp = read_oof(os.path.join(out_dir, "oof", f"{c}_s{sd}.jsonl"), order)
            runs[c].append({"seed": sd, "m": run_metrics(ws, meta, hn, P_bin, P_ttp, rec["selection"]), "folds": rec["folds"],
                            "cap": rec["config"]["max_epochs"], "n_hit_ceiling": rec["n_hit_ceiling"],
                            "n_stop_at_cap": sum(v["stop_epoch"] >= rec["config"]["max_epochs"] for f in rec["folds"] for v in f.values()),
                            "minutes": rec["minutes"]})
    keys = [k for k in ["M0a", "M0b"] + CONFIGS if runs.get(k)]
    # ---- bang 1 ----
    L = ["# VT-Guard Buoc 6 moc 2 - chuoi ablation kien truc: CHI OOF tren Train", "",
         f"Sinh boi `src/models/step6_m2_table.py` luc {datetime.now(timezone(timedelta(hours=7))).replace(microsecond=0).isoformat()}. "
         "Huan luyen tren Colab bang `notebooks/step6_vtseq_colab.ipynb` (chi goi `vtseq.run_oof_experiment`, clone theo commit); "
         "bang dung tren host tu ket qua tai ve. "
         "KHONG doc / du doan tap test o moc nay.", "",
         "CV 5 fold theo nhom chong thoi gian (`evaluate.cv_folds`), Train 483 cua so (165 duong, 59 hard_negative). "
         "Nguong nhi phan: FPR <= 1% tren cua so am OOF; nguong TTP: max-F1 OOF theo TTP; p_bin hay p_bin' = max(p_bin, max p_ttp) "
         "chon theo PR-AUC OOF. M0 = B3 Buoc 5 (3 seed, tran 60 epoch), tinh lai bang CUNG quy tac. Cac cau hinh khac 5 seed "
         "(1337, 7, 42, 2024, 99), tran 100 epoch, patience 10. Gia tri: trung binh +- do lech chuan (ddof=1) qua seed.", "",
         "**(1) Bang OOF**", "",
         "| Cau hinh | Thay doi | seed | macro-F1 TTP | " + " | ".join(TTPS) + " | PR-AUC bin | FPR hard_neg | FPR am | Recall | Spearman(diem, do dai) am | Nguong bin | p_bin / p_bin' |",
         "|---|---|---|---|" + "---|" * len(TTPS) + "---|---|---|---|---|---|---|"]
    agg = {}
    for k in keys:
        R = [r["m"] for r in runs[k]]
        col = lambda f: [r[f] for r in R]
        agg[k] = {f: mean_sd(col(f)) for f in ("macro_f1_ttp", "pr_auc_bin", "fpr_hard_negative", "fpr_neg", "recall", "spearman_len_neg", "thr_bin")}
        agg[k].update({f"f1_{t}": mean_sd([r["f1_ttp"][t] for r in R]) for t in TTPS})
        ch = [r["binary_score"] for r in R]
        L.append(f"| {k} | {DESC[k]} | {len(R)} | {ms(col('macro_f1_ttp'))} | " + " | ".join(ms([r['f1_ttp'][t] for r in R]) for t in TTPS)
                 + f" | {ms(col('pr_auc_bin'))} | {ms(col('fpr_hard_negative'))} | {ms(col('fpr_neg'))} | {ms(col('recall'))} | "
                 f"{ms(col('spearman_len_neg'), 2)} | {ms(col('thr_bin'))} | {ch.count('p_bin')} / {ch.count('p_bin_max')} |")
    # ---- bang 2: epoch ----
    L += ["", "**(2) Epoch moi fold** - `tot nhat/dung` (M0: chi co epoch tot nhat; dau bin|ttp). Tran: M0 60, M1-M4b 100.", "",
          "| Cau hinh | seed | fold 1 | fold 2 | fold 3 | fold 4 | fold 5 | fold cham tran (epoch tot nhat = tran) | fold chay toi tran |", "|---|---|---|---|---|---|---|---|---|"]
    for k in keys:
        for r in runs[k]:
            cells = []
            for f in r["folds"]:
                cells.append(" ; ".join(f"{h}:{v['best_epoch']}" + (f"/{v['stop_epoch']}" if v.get("stop_epoch") is not None else "") for h, v in f.items())
                             if len(f) > 1 else "/".join(str(v[x]) for v in f.values() for x in ("best_epoch", "stop_epoch")))
            L.append(f"| {k} | {r['seed']} | " + " | ".join(cells) + f" | {r['n_hit_ceiling']} | {r.get('n_stop_at_cap', '-')} |")
    tot = {k: (sum(r["n_hit_ceiling"] for r in runs[k]), sum(len(r["folds"]) * len(r["folds"][0]) for r in runs[k])) for k in keys}
    L += ["", "Tong fold cham tran: " + ", ".join(f"{k} {a}/{b}" for k, (a, b) in tot.items()) + "."]
    # ---- de xuat theo 4.3 ----
    def tie(a, b, f):
        (m1, s1), (m2, s2) = agg[a][f], agg[b][f]
        return abs(m1 - m2) <= math.sqrt((s1 ** 2 + s2 ** 2) / 2)
    cands = [c for c in CANDIDATES if c in agg]
    steps = []
    pool = cands
    for f, better in (("macro_f1_ttp", max), ("pr_auc_bin", max), ("fpr_hard_negative", min)) if pool else ():
        best = better(pool, key=lambda c: agg[c][f][0])
        keep = [c for c in pool if c == best or tie(c, best, f)]
        steps.append((f, best, keep)); pool = keep
        if len(pool) == 1: break
    L += ["", "**(3) De xuat cau hinh cuoi theo quy tac 4.3 (chi OOF)**", "",
          f"Ung vien: {', '.join(cands)}. Nguong ngang nhau: |chenh trung binh| <= do lech chuan gop qua seed.", ""]
    for f, best, keep in steps:
        L.append(f"- Tieu chi `{f}`: tot nhat {best} ({agg[best][f][0]:.4f}); ngang nhau voi no: {', '.join(keep)} -> "
                 + ("con lai " + ", ".join(keep) if len(keep) > 1 else f"chon **{keep[0]}**"))
    final = pool[0] if len(pool) == 1 else None
    if not pool: L.append("- Chua co ket qua ung vien.")
    if final is None and pool: L.append(f"- Van ngang nhau sau ca 3 tieu chi: {', '.join(pool)} (can quyet dinh them).")
    L.append("")
    os.makedirs(os.path.join(root, "reports", "step6"), exist_ok=True)
    with open(os.path.join(root, "reports", "step6", "m2_oof.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L) + "\n")
    with open(os.path.join(root, "reports", "step6", "m2_oof.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"agg_mean_sd": agg, "runs": {k: [{**r, "folds": r["folds"]} for r in v] for k, v in runs.items() if v},
                   "rule_steps": steps, "proposed": final, "candidates": cands}, f, indent=1)
    print("\n".join(L))

if __name__ == "__main__":
    main(".")
