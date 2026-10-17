#!/usr/bin/env python3
"""VT-Guard Buoc 8 - KHOA cau hinh fusion TRUOC khi cham test -> reports/step8/final_fusion.json (brief muc 4).
Chi dung OOF Train (fuse.load_oof) + bo luat cuoi (Train). Cung khoa tham so cac doi chung se chay tren test
(F0', F2, F4-B) de khong co gi duoc chon sau khi thay test. Chay: python src/fusion/lock.py
"""
import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval"): sys.path.insert(0, os.path.join(HERE, d))
import fuse as F                                        # noqa: E402
from evaluate import cv_folds, TTPS                     # noqa: E402
from bootstrap import best_f1_threshold                 # noqa: E402

def main(root="."):
    D0 = F.load_oof(root); folds = cv_folds(D0["meta"], root=root)
    keep = F.final_rule_ttps(root)
    D = F.mask_rule_channels(D0, keep)
    out, sel = F.select(D, folds)
    outA, selA = F.select(D0, folds)
    assert sel["chosen"] == "F3" and out["F3"]["params"]["beta"] == 0.1, (sel["chosen"], out["F3"]["params"])
    # F0' (doi chung MO TA): chi-AI, nguong chon lai tren CUNG OOF: nhi phan FPR <= 1%, TTP max-F1
    f0p = {"thr": F.threshold_at_fpr(D["y"], D["p"]), "thr_k": [best_f1_threshold(D["yk"][:, j], D["pk"][:, j])[0] for j in range(len(TTPS))]}
    head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    pj = lambda st: F.params_json(st, out[st]["params"])
    res = {
        "locked_at": datetime.now(timezone(timedelta(hours=7))).replace(microsecond=0).isoformat(), "locked_from_commit": head,
        "dataset_version": "v1.2",
        "chosen": {"strategy": "F3", "variant": "B", "formula": "s = p + beta*r ; s_k = p_k + beta*r_k (r_k = 0 cho TTP ngoai rule_ttp_channels)",
                   "beta": out["F3"]["params"]["beta"], "threshold_binary": float(out["F3"]["params"]["thr"]),
                   "threshold_rule_binary": "FPR <= 1% tren cua so am OOF", "thresholds_ttp": dict(zip(TTPS, [float(x) for x in out["F3"]["params"]["thr_k"]])),
                   "threshold_rule_ttp": "max-F1 OOF theo TTP (nhu Buoc 6)", "rule_ttp_channels": keep,
                   "r_definition": "r = 1 neu co luat khop (p_malicious chi-luat >= 0.5, nhu Buoc 7); r_k = 1 neu luat theo TTP k khop",
                   "p_definition": f"p = diem nhi phan AI VT-Seq-ens ({D0['ai_binary_score']}), p_k = xac suat TTP AI"},
        "sources_oof": {"ai": F.AI_OOF.replace(os.sep, "/"), "rules": F.RULES_OOF.replace(os.sep, "/"), "ai_locked_thresholds": F.AI_SEL.replace(os.sep, "/"),
                        "not_used": F.RULES_INSAMPLE.replace(os.sep, "/") + " (in-sample; khong dung de hoc/chon)"},
        "sources_test": {"ai": "reports/preds/vtseq_M3_ens_<split>.jsonl", "rules": "reports/preds/rules_<split>.jsonl"},
        "deviation_from_brief": {
            "what": f"kenh luat theo TTP (r_k) CHI cho {keep}; brief muc 3 dinh nghia da nhan dung moi r_k",
            "reason": "su kien cau truc CHI dua tren Train: bo luat cuoi (quy nap tu toan bo Train, Buoc 7) chi co luat theo TTP cho "
                      f"{keep}. Luc chay test r_k cua T1016 va T1087.002 luon = 0, nen tren OOF cung phai = 0 de dac trung fusion "
                      "giong luc trien khai. Khong dung so lieu do nhay (in-sample, chi mo ta) lam can cu.",
            "note_variant_A": "bien the A (moi kenh r_k) cung chon F3 va co macro-F1 TTP OOF cao hon (0.847 vs 0.835), nhung phan "
                              "loi do kenh T1016 - kenh nay chi ton tai trong bo luat FOLD (de dai hon), KHONG ton tai trong bo luat cuoi."},
        "selection_variant_B": {"criteria": ["macro-F1 TTP OOF", "PR-AUC nhi phan OOF", "FPR OOF hard_negative"],
                                "tie": "|chenh| <= do lech chuan bootstrap cua hieu so (1000, seed 1337) -> it tham so hon (F2 < F3 < F4)",
                                "steps": sel["steps"], "chosen": sel["chosen"], "beta_grid_note": "beta 0.1 / 0.2 / 0.3 cho ket qua OOF giong nhau -> beta nho nhat",
                                "oof_metrics": {st: out[st]["m"] for st in ("F0", "F1", "F2", "F3", "F4")}},
        "variant_A_oof_for_reference": {"chosen": selA["chosen"], "macro_f1_ttp": {st: outA[st]["m"]["macro_f1_ttp"] for st in F.ORDER}},
        "controls_locked_for_test": {
            "F0": {"desc": "chi-AI, nguong khoa Buoc 6", "tau": D0["tau"], "tau_k": dict(zip(TTPS, [float(x) for x in D0["tau_k"]]))},
            "F0_prime": {"desc": "chi-AI, nguong chon lai tren CUNG OOF (FPR <= 1% nhi phan, max-F1 TTP) - doi chung MO TA, khong vao ho Holm",
                         "thr": f0p["thr"], "thr_k": dict(zip(TTPS, [float(x) for x in f0p["thr_k"]]))},
            "F1": {"desc": "chi-luat Buoc 7 (nguong 0.5)"},
            "F2": {"desc": "OR, bien the B", "tau": D0["tau"], "tau_k": dict(zip(TTPS, [float(x) for x in D0["tau_k"]]))},
            "F4_B": {"desc": "stacking LR bien the B, fit toan OOF; nguong tren diem OOF long", **pj("F4")}},
        "test_runs_once": True, "seed": 1337}
    os.makedirs(os.path.join(root, "reports", "step8"), exist_ok=True)
    with open(os.path.join(root, "reports", "step8", "final_fusion.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, indent=1)
    print(json.dumps(res["chosen"], indent=1)); print("F0' thr", round(f0p["thr"], 4), "| F0 tau", round(D0["tau"], 4))

if __name__ == "__main__":
    main(".")
