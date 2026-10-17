#!/usr/bin/env python3
"""VT-Guard Buoc 6 - KHOA cau hinh VT-Seq cuoi TRUOC khi cham test (brief 4.3, tieu chi chap nhan #2).
Doc OOF moc 2 (reports/step6/m2/logs, Train) -> reports/step6/final_config.json. Khong doc tap test.
Chay: python src/models/step6_lock.py
"""
import json, os, subprocess, sys
from dataclasses import asdict
from datetime import datetime, timezone, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vtseq as V   # noqa: E402

FINAL = "M3"

def main(root="."):
    cfg = V.PRESETS[FINAL]
    per_seed = {}
    for sd in V.SEEDS:
        lg = json.load(open(os.path.join(root, "reports", "step6", "m2", "logs", f"{FINAL}_s{sd}.json"), encoding="utf-8"))
        assert lg["config"] == asdict(cfg), "cau hinh trong log OOF khac PRESETS"
        sel = lg["selection"]
        per_seed[str(sd)] = {"final_epochs": lg["final_epochs"], "binary_score": sel["binary_score"],
                             "threshold_binary_fpr1pct": sel["binary"], "threshold_binary_max_f1_ref": sel["binary_max_f1"],
                             "threshold_ttp": sel["ttp"], "oof": lg["oof"],
                             "best_epoch_per_fold": [f["joint"]["best_epoch"] for f in lg["folds"]]}
    thr = [v["threshold_binary_fpr1pct"] for v in per_seed.values()]
    m2 = json.load(open(os.path.join(root, "reports", "step6", "m2_oof.json"), encoding="utf-8"))
    head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = {
        "locked_at": datetime.now(timezone(timedelta(hours=7))).replace(microsecond=0).isoformat(),
        "locked_from_commit": head, "dataset_version": "v1.2",
        "final_model": "VT-Seq = " + FINAL, "config": asdict(cfg), "seeds": list(V.SEEDS),
        "selection_rule": {
            "criteria_4_3": ["macro-F1 TTP OOF", "PR-AUC nhi phan OOF", "FPR OOF tren cua so hard_negative"],
            "tie": "ngang nhau neu |chenh trung binh| <= do lech chuan gop qua seed sqrt((sd1^2+sd2^2)/2)",
            "result_4_3": "M3, M4, M4b ngang nhau o ca 3 tieu chi (reports/step6/m2_oof.md)",
            "tie_break": "do on dinh nguong nhi phan giua seed (do lech chuan nguong OOF thap nhat): "
                         "M3 0.060, M4 0.135, M4b 0.249 -> M3",
            "note": "tieu chi pha hoa (do on dinh nguong) THEM SAU KHI xem OOF moc 2, van CHI dua tren Train (OOF); "
                    "khong dung ket qua test nao (ke ca test Buoc 5)."},
        "threshold_rule": {"binary": "FPR <= 1% tren cua so am OOF (moi seed rieng)", "binary_reference": "max-F1 OOF",
                           "ttp": "max-F1 OOF theo tung TTP (moi seed rieng)",
                           "binary_score": "p_bin hay p_bin' = max(p_bin, max_k p_ttp) chon theo PR-AUC OOF (moi seed rieng)"},
        "final_fit": "fit lai toan Train, so epoch = trung vi epoch tot nhat 5 fold (moi seed rieng)",
        "per_seed": per_seed,
        "threshold_binary_mean_sd": [float(np.mean(thr)), float(np.std(thr, ddof=1))],
        "oof_mean_sd_candidates": {c: m2["agg_mean_sd"][c] for c in ("M3", "M4", "M4b")},
        "ensemble": "VT-Seq-ens = trung binh xac suat (p_bin, p_ttp) 5 seed M3; nguong + p_bin/p_bin' chon lai tren OOF trung binh",
        "test_runs_once": True}
    p = os.path.join(root, "reports", "step6", "final_config.json")
    with open(p, "w", encoding="utf-8", newline="\n") as f: json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ("final_model", "seeds", "threshold_binary_mean_sd")}),
          {s: (v["final_epochs"], v["binary_score"], round(v["threshold_binary_fpr1pct"], 3)) for s, v in per_seed.items()})

if __name__ == "__main__":
    main(".")
