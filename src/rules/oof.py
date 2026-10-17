#!/usr/bin/env python3
"""VT-Guard Buoc 7 moc 3 - du doan OOF cua bo phat hien chi-luat tren Train (cho Buoc 8 hoc fusion).

reports/preds/rules_train.jsonl la IN-SAMPLE (luat quy nap tu toan Train) -> Buoc 8 KHONG duoc dung de hoc fusion.
File nay: reports/preds/rules_oof_train.jsonl. Voi moi fold k (evaluate.cv_folds, cung 5 fold theo nhom nhu moc 1), chay LAI
quy trinh moc 1 CHI tren 4/5 Train cua fold do:
  tu vung atom (>= 3 phien), danh sach chan S1-S5 + S4-auto (own-share tinh tren cua so duong cua 4/5 Train), 2 luot
  (khong rang buoc / rang buoc), RIPPER (engine da chon o moc 1) cho nhi phan + 5 TTP, luat = literal co mat rut gon,
  cong G0 / G1 / G2 nhu moc 1; G3' = support >= 10 va precision >= 0.9 tren 4/5 Train (khong co OOF long trong fold - xap xi
  G3); G4 khu trung Jaccard >= 0.8.
-> ap len 1/5 con lai: p_malicious = max precision (4/5 Train) cua luat khop, p_ttp[T] tuong tu cho luat theo TTP T.
Hat giong attention chi dung de sap xep cot (pha hoa), nhu moc 1.
Chay: python src/rules/oof.py
"""
import json, os, sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))
import induce as I                                                   # noqa: E402
import predicates as Pd                                              # noqa: E402
from evaluate import write_preds, cv_folds, TTPS                     # noqa: E402

def fold_rules(meta_a, ev_a, og_a, seeds):
    Y = I.labels(meta_a)
    atoms_all, wa = I.build_vocab(meta_a, ev_a, seeds)
    X_all = I.matrix(wa, atoms_all)
    share = I.own_shares(meta_a, ev_a, og_a, Y, atoms_all)
    why = lambda a: Pd.forbidden_reason(a) or I.bg_reason(a, share)
    atoms_c = [a for a in atoms_all if not why(a)]
    X_c = I.matrix(wa, atoms_c)
    cands = {}
    for X, atoms in ((X_all, atoms_all), (X_c, atoms_c)):
        for tg in I.TARGETS:
            rs, _ = I.fit_rules("ripper", X, Y[tg], atoms)
            for r in rs:
                k = I.rule_key(tg, r["literals"])
                if not k[1] or any(why(a) or Pd.sigma_reason(a) for a in k[1]) or k in cands: continue
                m = I.eval_pos(X_all, atoms_all, k[1]); y = Y[tg]
                sup = int(m.sum()); prec = float((m & y).sum() / max(1, sup))
                if sup >= I.MIN_SUPPORT and prec >= I.PREC_OOF: cands[k] = {"target": tg, "atoms": list(k[1]), "prec": prec, "m": m}
    kept = []
    for tg in I.TARGETS:
        cs = sorted([c for c in cands.values() if c["target"] == tg], key=lambda c: (-c["prec"], -int(c["m"].sum()), len(c["atoms"]), str(c["atoms"])))
        ks = []
        for c in cs:
            s = set(np.flatnonzero(c["m"]))
            if any(len(s & set(np.flatnonzero(x["m"]))) / max(1, len(s | set(np.flatnonzero(x["m"])))) >= I.JACCARD for x in ks): continue
            ks.append(c)
        kept += ks
    return kept

def main(root="."):
    meta, events, origins = I.load_train(root)
    seeds = I.load_seeds(root); folds = cv_folds(meta, root=root)
    P = json.load(open(os.path.join(root, "reports", "step7", "rules_provenance.json"), encoding="utf-8"))
    final_keys = {(r["target"], tuple(sorted(((a[0], tuple(a[1]) if a[0] == "imgtok" else a[1]) for a in r["atoms"]), key=lambda a: (a[0], str(a[1]))))) for r in P["rules"]}
    preds = {}; info = []
    for fi, (a_, va) in enumerate(folds):
        rules = fold_rules([meta[i] for i in a_], [events[i] for i in a_], [origins[i] for i in a_], seeds)
        for i in va:
            hit = [r for r in rules if Pd.match([(a, True) for a in r["atoms"]], events[i])]
            preds[meta[i]["window_id"]] = {"p": max([r["prec"] for r in hit], default=0.0),
                                           "p_ttp": {t: max([r["prec"] for r in hit if r["target"] == t], default=0.0) for t in TTPS}}
        keys = {(r["target"], tuple(sorted(r["atoms"], key=lambda a: (a[0], str(a[1]))))) for r in rules}
        info.append({"fold": fi, "n_rules": len(rules), "n_val": len(va), "n_final_rules_present": len(keys & final_keys),
                     "rules": [{"target": r["target"], "predicates": [I.fmt_atom(a) for a in r["atoms"]], "precision_in_fold": round(r["prec"], 4)} for r in rules]})
        print(f"  fold {fi}: {len(rules)} luat (trung luat cuoi: {len(keys & final_keys)}/11), {len(va)} cua so val", flush=True)
    write_preds(root, "rules_oof", "train", meta, preds)
    y = np.array([w["window_malicious"] for w in meta], bool); p = np.array([preds[w["window_id"]]["p"] for w in meta]) >= 0.5
    tp, fp, fn = int((p & y).sum()), int((p & ~y).sum()), int((~p & y).sum())
    per = {}
    for t in TTPS:
        yt = np.array([t in w["window_ttps"] for w in meta]); pt = np.array([preds[w["window_id"]]["p_ttp"][t] for w in meta]) >= 0.5
        a, b, c = int((pt & yt).sum()), int((pt & ~yt).sum()), int((~pt & yt).sum())
        per[t] = round(2 * a / (2 * a + b + c), 4) if a else 0.0
    summ = {"file": "reports/preds/rules_oof_train.jsonl", "binary_at_0.5": {"tp": tp, "fp": fp, "fn": fn, "precision": round(tp / max(1, tp + fp), 4),
            "recall": round(tp / max(1, tp + fn), 4), "f1": round(2 * tp / max(1, 2 * tp + fp + fn), 4)}, "ttp_f1_at_0.5": per,
            "macro_f1_ttp": round(float(np.mean(list(per.values()))), 4), "folds": info,
            "note": "rules_train.jsonl = IN-SAMPLE; Buoc 8 CHI dung rules_oof_train.jsonl de hoc fusion. G3 trong fold xap xi bang precision tren 4/5 Train."}
    with open(os.path.join(root, "reports", "step7", "rules_oof.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(summ, f, indent=1)
    print("OOF nhi phan:", summ["binary_at_0.5"], "| F1 TTP:", per, "| macro", summ["macro_f1_ttp"])

if __name__ == "__main__":
    main(".")
